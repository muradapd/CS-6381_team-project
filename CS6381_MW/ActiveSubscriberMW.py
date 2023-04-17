# Middleware functionality for Subscribers
# John Gordley

# import the needed packages
import zmq  # ZMQ sockets
import sys
import time

from datetime import datetime
from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError

from zk_tools import unpack_znode_val, pack_znode_val

# import serialization logic
from CS6381_MW import discovery_pb2
from CS6381_MW import topic_pb2

##################################
#       Subscriber Middleware class
##################################
class SubscriberMW ():

    ########################################
    # constructor
    ########################################
    def __init__(self, logger):
        self.logger = logger  # internal logger for print statements
        self.sub = None  # will be a ZMQ SUB socket for subscribing to info
        self.req = None  # will be a ZMQ REQ socket to talk to Discovery service
        self.poller = None  # used to wait on incoming replies
        self.addr = None  # our advertised IP address
        self.port = None  # port num where we are going to look for topics?
        self.name = None
        self.zk_addr = None
        self.disc_addr = None
        self.ppath = '/discovery'

        self.connected_addrs = []

    def clean_exit(self, name):
        self.zk.stop ()
        self.zk.close ()
        try:
            # first build a exit req message
            exit_req = discovery_pb2.ExitReq()  # allocate
            exit_req.role = "subscriber"
            exit_req.address = f'{self.addr}:{self.port}'
            exit_req.id = name

            # Build the outer layer Discovery Message
            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.msg_type = discovery_pb2.EXIT
            disc_req.exit.CopyFrom(exit_req)

            buf2send = disc_req.SerializeToString()
            self.req.send(buf2send)

        except Exception as e:
            raise e

        self.logger.info("SubscriberMW: Cleanly exiting. Goodbye.")

    def init_client(self):
        # Set up zookeeper
        try:

            # instantiate a zookeeper client object
            self.zk = KazooClient (self.zk_addr)
            self.logger.info(f"SubscriberMW: Zookeeper State -> {self.zk.state}")
            
        except:
            self.logger.info(f'Unexpected error in zk initialization: {sys.exc_info()[0]}')
            raise

    # main logic of the client
    def run_client (self):
        """main logic of client"""

        try:
            # First, open connection to zookeeper
            self.zk.start ()

            # next our job is to create an ephemeral znode under the parent
            # znode to indicate that we are up. Since it is possible that the
            # parent may not have yet created a znode, we keep testing for it
            while (True):
                if self.zk.exists (self.ppath):

                    self.logger.info(f"SubscriberMW: Parent znode {self.ppath} is set.")

                    # in that case we create our child node
                    self.zk.create (self.ppath + str ("/") + self.name, value=self.name.encode(), ephemeral=True)
                    # make sure to exit the loop
                    break
                else:
                    self.logger.info(f"SubscriberMW: Parent znode {self.ppath} is not up yet.")
                    time.sleep (1)

            # first we set a watcher for our parent's znode data.
            #---------------------------------------------------------
            # define a data watch function on the parent znode
            # note that this is a nested function defn
            @self.zk.DataWatch (self.ppath)
            def data_change_watcher (data, stat):
                """Data Change Watcher"""

                # Need to check if Discovery Address changed, then we need to reconnect
                split_data = data.decode().split('|')
                self.logger.info(f'SubscriberMW - DataChangeWatcher received: {split_data}')
                for data in split_data:
                    split = data.split('-')
                    if split[0] == 'disc_addr':
                        if self.disc_addr != split[1]:
                            self.logger.info(f"SubscriberMW - Connecting to new lead discovery at {split[1]}")
                            # Disconnect from old discovery
                            if self.disc_addr:
                                self.req.disconnect("tcp://" + self.disc_addr)
                                
                            self.disc_addr = split[1]
                            connect_str = "tcp://" + self.disc_addr
                            self.req.connect(connect_str)

                            
                    elif split[0] == 'broker_addr':
                        # Broker might have changed
                        if split[1] and split[1] not in self.connected_addrs and len(self.connected_addrs) > 0:
                            self.logger.info(f"SubscriberMW - Broker changed, need to reconnect")
                            time.sleep(1.5)
                            self.connect_pubs([split[1]])
                            
                
        except:
            self.logger.info("Unexpected error in PublisherMW during Zookeeper run client", sys.exc_info()[0])
            raise


    ########################################
    # configure/initialize
    ########################################
    def configure(self, args):
        ''' Initialize the object '''

        try:
            # First retrieve our advertised IP addr and the publication port num
            self.port = args.port
            self.addr = args.addr
            self.name = args.name

            self.zk_addr = args.discovery

            context = zmq.Context()  # returns a singleton object

            # get the ZMQ poller object
            self.poller = zmq.Poller()

            # Now acquire the REQ and SUB sockets
            self.req = context.socket(zmq.REQ)
            self.sub = context.socket(zmq.SUB)

            # Setup ZooKeeper before we connect to discovery
            self.init_client()
            self.run_client()

            # register the REQ socket for incoming events
            self.poller.register(self.req, zmq.POLLIN)
            connect_str = "tcp://" + self.disc_addr
            self.req.connect(connect_str)
            
            self.logger.info(f"SubscriberMW - {self.name} -> {self.addr}:{self.port} Configured Successfully")

        except Exception as e:
            raise e

    ########################################
    # connect to publishers that we are interested in with filters
    ########################################
    def connect_pubs(self, pub_addresses, topicList=None):
        ''' connect to publishers we are interested in '''
        pub_addresses = list(set(pub_addresses))

        self.logger.info(f"SubscriberMW - connecting to {pub_addresses}")

        # Set up socket filters for only the topics we are interested in
        if topicList:
            for topic in topicList:
                self.sub.setsockopt_string(zmq.SUBSCRIBE, topic)

        # Connect to the publishers we want to hear from
        for pub in pub_addresses:
            if pub and pub not in self.connected_addrs:
                self.sub.connect(f'tcp://{pub}')
                self.connected_addrs.append(pub)

        self.poller.register(self.sub, zmq.POLLIN)

    ########################################
    # register with the discovery service
    ########################################
    def register(self, name, topiclist):
        ''' register the appln with the discovery service '''

        try:
            register_req = discovery_pb2.RegisterReq()  # allocate
            register_req.role = "subscriber"
            comma_sep_topics = ','.join(topiclist)
            register_req.topiclist = comma_sep_topics   # fill up the topic list
            register_req.address = self.addr
            register_req.port = self.port
            register_req.id = name

            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.msg_type = discovery_pb2.REGISTER
            disc_req.register_req.CopyFrom(register_req)

            buf2send = disc_req.SerializeToString()

            self.req.send(buf2send)

            return self.event_loop()

        except Exception as e:
            raise e

    ########################################
    # lookup publishers that match our list of topics so we can connect
    ########################################
    def lookup(self, topicList):
        ''' lookup a list of publishers with the topics we are interested in '''

        try:
            # first build a Lookup message
            lookup_msg = discovery_pb2.LookupPubByTopicReq()  # allocate
            lookup_msg.topiclist = ",".join(topicList)

            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.msg_type = discovery_pb2.LOOKUP_PUB_BY_TOPIC
            disc_req.topic.CopyFrom(lookup_msg)

            buf2send = disc_req.SerializeToString()
            self.req.send(buf2send)

            self.logger.info(f"SubscriberMW - Looking up topics: {topicList}")
            self.logger.info(f"SubscriberMW - Sent lookup request to Discovery")

            return self.event_loop()

        except Exception as e:
            raise e

    #################################################################
    # run the event loop where we expect to receive a reply to a sent request
    #################################################################
    def event_loop(self):

        try:
            while True:
                # poll for events. We give it an infinite timeout.
                # The return value is a socket to event mask mapping
                events = dict(self.poller.poll())

                # the only socket that should be enabled, if at all, is our REQ socket.
                if self.req in events:  # this is the only socket on which we should be receiving replies
                    # handle the incoming reply and return the result
                    return self.handle_reply()

                if self.sub in events:
                    # handle incoming pub topic dissemination
                    return self.handle_message()

        except Exception as e:
            raise e

    #################################################################
    # handle an incoming reply
    #################################################################
    def handle_reply(self):

        try:
            # let us first receive all the bytes
            bytesRcvd = self.req.recv()

            # now use protobuf to deserialize the bytes
            disc_resp = discovery_pb2.DiscoveryResp()
            disc_resp.ParseFromString(bytesRcvd)

            # When your proto file is modified, some of this here
            # will get modified.
            if (disc_resp.msg_type == discovery_pb2.REGISTER):
                # this is a response to register message
                return disc_resp.register_resp.result
            elif (disc_resp.msg_type == discovery_pb2.ISREADY):
                # this is a response to is ready request
                return disc_resp.is_ready.reply
            elif (disc_resp.msg_type == discovery_pb2.LOOKUP_PUB_BY_TOPIC):
                return list(disc_resp.resp.pub_addresses.split(','))
            else:  # anything else is unrecognizable by this object
                # raise an exception here
                raise Exception("Unrecognized response message")

        except Exception as e:
            raise e

    #################################################################
    # handle an incoming message from a pub
    #################################################################

    def handle_message(self):

        try:
            # self.logger.info(f"SubscriberMW - Received a message")

            # let us first receive all the bytes
            mp_message = self.sub.recv_multipart()

            topic = mp_message[0]
            bytesRcvd = mp_message[1]

            # now use protobuf to deserialize the bytes
            message = topic_pb2.topicMessage()
            message.ParseFromString(bytesRcvd)
            latency = datetime.now() - datetime.strptime(message.timestamp, "%m/%d/%Y, %H:%M:%S.%f")

            return message

        except Exception as e:
            raise e