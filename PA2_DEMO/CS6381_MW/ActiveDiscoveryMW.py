###############################################
#
# Author: John Gordley
# Professor: Aniruddha Gokhale
# Vanderbilt University
#
# Simple discovery middleware for ZK integration
#
# Created: Spring 2023
#
###############################################

# import the needed packages
import zmq
import sys
import time

from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError
from zk_tools import unpack_znode_val, pack_znode_val

# import serialization logic
from CS6381_MW import discovery_pb2

##################################
#       Discovery Middleware class
##################################


class DiscoveryMW ():

    ########################################
    # constructor
    ########################################
    def __init__(self, logger):
        self.logger = logger  # internal logger for print statements
        self.rep = None  # will be a ZMQ REP socket to talk to subscribers and publishers
        self.req = {}  # Will be used if we are using the DHT approach
        self.poller = None  # used to wait on incoming replies
        self.port = None  # port num where we are going to look for topics?
        self.address = None
        self.zkIPAddr = None
        self.zkPort = None
        self.zk = None  # session handle to the server
        self.leader = False
        self.path = '/discovery'
        self.publishers = None
        self.broker_addr = None

    def update_pubs(self, pubs_dict):
        self.publishers = pubs_dict

    def update_broker(self, broker_addr):
        value, stat = self.zk.get (self.path)
        
        value_dict = unpack_znode_val(value)

        discs = value_dict.get('disc_list')
        updated_values = pack_znode_val(value_dict.get('disc_addr'), broker_addr, discs)
        self.zk.set(self.path, updated_values.encode())
        self.broker_addr = broker_addr


    def clean_exit(self):

        # Get leader list, select next one, put that one's info as the ip addr, etc.
        # Get leader list
        value, stat = self.zk.get (self.path)
        
        value_dict = unpack_znode_val(value)

        discs = value_dict.get('disc_list')
        real_discs = []
        for disc in discs:
            if disc:
                real_discs.append(disc)
        discs = real_discs

        self.logger.info(f"DiscoveryMW: Remaining discs: {discs}")
        if len(discs) < 1:
            self.logger.info("DiscoveryMW: No backup discovery services present!")
        else:
            next_leader = discs.pop()

            self.logger.info(f"DiscoveryMW: Transferring leadership to {next_leader}")

            # Connect to the next leader
            connect_str = "tcp://" + next_leader
            self.req.connect(connect_str)

            # Send a leader elect request
            leader_req = discovery_pb2.LeaderReq()

            # Format for pub_info_str
            # 10.0.0.1:5000-weather,temperature,pressure|10.0.0.2:5555-weather,pressure,climate
            pub_info_str = ''

            for name, pub in self.publishers.items():
                pub_info_str += name + '-' + pub.get('address') + ':' + pub.get('port') + '-'
            
                pub_topics = pub.get('topicList')
                for topic in pub_topics:
                    pub_info_str += topic + ','

                pub_info_str += '|'

            leader_req.pub_info = pub_info_str
            leader_req.broker = self.broker_addr or ''

            self.logger.info(f"DiscoveryMW: Sending pubs info as {pub_info_str}")

            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.msg_type = discovery_pb2.LEADER
            disc_req.leader_elect.CopyFrom(leader_req)

            # Send the new leader all the data
            buf2send = disc_req.SerializeToString()
            self.req.send(buf2send)

            self.logger.info(f"DiscoveryMW: Setting remaining discs as {discs}")
        
            updated_values = pack_znode_val(next_leader, value_dict.get('broker_addr'), discs)
            self.zk.set(self.path, updated_values.encode())

        self.zk.stop ()
        self.zk.close ()

        self.logger.info("DiscoveryMW: Cleanly exiting. Goodbye.")

    def init_driver(self):
        # Set up zookeeper
        try:

            # instantiate a zookeeper client object
            # right now only one host; it could be the ensemble
            hosts = self.zkIPAddr + str (":") + str (self.zkPort)
            self.zk = KazooClient (hosts)
            self.logger.info(f"DiscoveryMW: Zookeeper State -> {self.zk.state}")
            
        except:
            self.logger.info(f'Unexpected error in zk initialization: {sys.exc_info()[0]}')
            raise

    def run_driver(self):

        # first connect to the zookeeper server
        self.logger.info(f"DiscoveryMW: Connecting to Zookeeper")
        self.zk.start ()
        self.logger.info(f"DiscoveryMW: Zookeeper State -> {self.zk.state}")

        # next, create a znode for the barrier sync with initial value 0
        try:

            addr_to_send = f'{self.address}:{self.port}'
            packed_init_vals = pack_znode_val(addr_to_send, '', [])

            # If this works, we are the leader
            self.zk.create (self.path, value=packed_init_vals.encode())

            # TODO: Set our address and port as the leader credentials
            self.leader = True
            self.logger.info(f"DiscoveryMW: We are the leader! Set our address in Zookeeper as {self.address}:{self.port}")

        except NodeExistsError:
            # We are not the leader, simply register to listen
            self.logger.info("DiscoveryMW: We are not the leader, but we will wait for our turn...")

            value, stats = self.zk.get(self.path)
            unpacked = unpack_znode_val(value)

            discs = unpacked.get('disc_list')
            discs.append(f'{self.address}:{self.port}')

            packed_to_send = pack_znode_val(unpacked.get('disc_addr'), unpacked.get('broker_addr'), discs)
            self.zk.set(self.path, packed_to_send.encode())

            self.leader = False
            pass

    ########################################
    # configure/initialize
    ########################################
    def configure(self, args):
        ''' Initialize the object '''

        try:

            # First retrieve our advertised IP addr and the publication port num
            self.port = args.port
            self.address = args.address

            # Next get the ZMQ context
            context = zmq.Context()  # returns a singleton object
            self.poller = zmq.Poller()
            self.rep = context.socket(zmq.ROUTER)

            # Set this up so we can connect to other discoveries later and tell them they are the leader
            self.req = context.socket(zmq.REQ)

            # register the REP socket for incoming events
            self.poller.register(self.rep, zmq.POLLIN)
            connect_str = f'tcp://*:{self.port}'
            self.rep.bind(connect_str)

            self.zkIPAddr = args.zkIPAddr  # ZK server IP address
            self.zkPort = args.zkPort # ZK server port num

            # Set up zookeeper
            self.init_driver()

            # Run zookeeper driver to register listeners, etc.
            self.run_driver()

        except Exception as e:
            raise e

    #################################################################
    # run the event loop where we expect to receive a reply to a sent request
    #################################################################
    def event_loop(self):

        try:
            self.logger.info("DiscoveryMW - Running the MW event loop")

            while True:
                # poll for events. We give it an infinite timeout.
                # The return value is a socket to event mask mapping

                events = dict(self.poller.poll())

                # the only socket that should be enabled, if at all, is our REQ socket.
                if self.rep in events:  # this is the only socket on which we should be receiving replies
                    # handle the incoming reply and return the result
                    self.logger.info(f'DiscoveryMW - Received an event from our REP socket')
                    return self.handle_reply()

        except Exception as e:
            raise e

    def handle_reply(self):

        try:
            bytesRcvd = self.rep.recv_multipart()
            message = bytesRcvd[-1]
            identity = bytesRcvd[0]

            self.logger.info(f'DiscoveryMW: Received new bytes from {identity} -> {bytesRcvd}')

            # now use protobuf to deserialize the bytes
            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.ParseFromString(message)

            if (disc_req.msg_type == discovery_pb2.REGISTER):
                # this is a request to register
                self.logger.info(f'DiscoveryMW: Register RQ from {disc_req.register_req.id} at addr {disc_req.register_req.address}')

                # create new object for our application to ingest
                register_req = {
                    'request_type': 'register',
                    'role': disc_req.register_req.role,
                    'topic_list': list(disc_req.register_req.topiclist.split(',')),
                    'id': disc_req.register_req.id,
                    'address': disc_req.register_req.address,
                    'port': disc_req.register_req.port,
                    'identity': identity
                }
                return register_req

            elif (disc_req.msg_type == discovery_pb2.LOOKUP_PUB_BY_TOPIC):

                self.logger.info(f'DiscoveryMW: Lookup RQ from {disc_req.register_req.id} for {disc_req.topic.topiclist.split(",")}')

                return {
                    'request_type': 'lookup',
                    'topicList': list(disc_req.topic.topiclist.split(',')),
                    'identity': identity,
                }

            elif (disc_req.msg_type == discovery_pb2.LOOKUP_ALL_PUBS):

                self.logger.info(f'DiscoveryMW: Lookup All Pubs RQ from {disc_req.register_req.id}')

                return {
                    'request_type': 'lookup_all_pubs',
                    'identity': identity
                }

            elif (disc_req.msg_type == discovery_pb2.EXIT):
                # this is a notification of exit
                self.logger.info(f'DiscoveryMW: Exit Notification from {disc_req.register_req.id}')

                # create new object for our application to ingest
                exit_req = {
                    'request_type': 'exit',
                    'role': disc_req.exit.role,
                    'id': disc_req.exit.id,
                    'address': disc_req.exit.address,
                }
                return exit_req
            
            elif (disc_req.msg_type == discovery_pb2.LEADER):

                self.logger.info(f'DiscoveryMW: We have been elected as the leader!')
                self.leader = True

                pub_dict = {}

                # Format for pub_info_str
                # 10.0.0.1:5000-weather,temperature,pressure|10.0.0.2:5555-weather,pressure,climate

                pubs_split = list(disc_req.leader_elect.pub_info.split('|'))
                print(pubs_split)
                for pub in pubs_split:
                    if pub:
                        name_addr_topics = list(pub.split('-'))
                        print(name_addr_topics)
                        name = name_addr_topics[0]

                        addr_port = list(name_addr_topics[1].split(':'))

                        topics = list(name_addr_topics[2].split(','))

                        pub_dict[name] = {
                            'address': addr_port[0],
                            'port': addr_port[1],
                            'topicList': topics
                        }

                leader_req = {
                    'request_type': 'leader',
                    'pub_info': pub_dict,
                    'broker': disc_req.leader_elect.broker
                }
                return leader_req

            else:  # anything else is unrecognizable by this object
                # raise an exception here
                raise Exception("Unrecognized response message")

        except Exception as e:
            raise e

    #################################################################
    # respond to a registration request
    #################################################################
    def verify_registration(self, identity, success):

        try:

            target = identity
            self.logger.info(f'DiscoveryMW: Verifying registration sending back to {target}')

           # If successfully verified, let them know otherwise let them down easy

            # first build a RegisterResp for the inner layer
            register_rep = discovery_pb2.RegisterResp()  # allocate

            if success:
                register_rep.result = '1'
            else:
                register_rep.result = '0'

            # Build the outer layer Discovery Message
            disc_rep = discovery_pb2.DiscoveryResp()
            disc_rep.msg_type = discovery_pb2.REGISTER
            disc_rep.register_resp.CopyFrom(register_rep)

            buf2send = disc_rep.SerializeToString()
            self.rep.send_multipart([target, b'', buf2send])

        except Exception as e:
            raise e

    #################################################################
    # respond to a lookup request
    #################################################################

    def lookup_response(self, identity, pubs_to_send, all=False):

        try:
            self.logger.debug("DiscoveryMW::lookup request")
            
            target = identity

            lookup_rep = None
            if not all:
                lookup_rep = discovery_pb2.LookupPubByTopicResp()  # allocate
            else:
                lookup_rep = discovery_pb2.LookupAllPubsResp()  # allocate

            lookup_rep.pub_addresses = ",".join(pubs_to_send)

            # Build the outer layer Discovery Message
            disc_rep = discovery_pb2.DiscoveryResp()

            if not all:
                disc_rep.msg_type = discovery_pb2.LOOKUP_PUB_BY_TOPIC
                disc_rep.resp.CopyFrom(lookup_rep)
            else:
                disc_rep.msg_type = discovery_pb2.LOOKUP_ALL_PUBS
                disc_rep.all_pubs.CopyFrom(lookup_rep)

            buf2send = disc_rep.SerializeToString()
            self.rep.send_multipart([target, b'',buf2send])

        except Exception as e:
            raise e
