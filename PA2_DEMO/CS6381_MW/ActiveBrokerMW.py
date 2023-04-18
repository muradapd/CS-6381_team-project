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
import os     # for OS functions
import sys    # for syspath and system exception
import time   # for sleep
import zmq  # ZMQ sockets

from datetime import datetime
from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError

# import serialization logic
from CS6381_MW import discovery_pb2
from CS6381_MW import topic_pb2


class BrokerMW ():

    ########################################
    # constructor
    ########################################
    def __init__(self, logger):
        self.logger = logger  # internal logger for print statements
        self.pub = None  # will be a ZMQ PUB socket for dissemination
        self.sub = None  # will be a ZMQ SUB socket for receiving messages from publishers
        self.req = None  # will be a ZMQ REQ socket to talk to Discovery service
        self.poller = None  # used to wait on incoming replies
        self.addr = None  # our advertised IP address
        self.port = None  # port num where we are going to publish our topics
        self.name = None
        self.zk_addr = None
        self.disc_addr = None
        self.ppath = '/discovery'
        self.leader = False

    def clean_exit(self, name):
        self.zk.stop ()
        self.zk.close ()
        try:
            # first build a exit req message
            exit_req = discovery_pb2.ExitReq()  # allocate
            exit_req.role = "broker"
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

        self.logger.info("BrokerMW: Cleanly exiting. Goodbye.")

    def init_client(self):
        # Set up zookeeper
        try:

            # instantiate a zookeeper client object
            self.zk = KazooClient (self.zk_addr, logger=self.logger)
            self.logger.info(f"BrokerMW: Zookeeper State -> {self.zk.state}")
            
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
            while (not self.leader):
                if self.zk.exists (self.ppath):

                    # in that case we create our child node
                    try:
                        self.zk.create (self.ppath + str ("/") + self.name, value=self.name.encode(), ephemeral=True)
                        self.leader = True
                    except NodeExistsError:
                        self.logger.info("BrokerMW: Another broker is the current leader, waiting our turn.")
                        self.leader = False
                        time.sleep(1)
                    
                else:
                    self.logger.info(f"BrokerMW: Parent znode {self.ppath} is not up yet.")
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
                self.logger.info(f'BrokerMW - DataChangeWatcher received: {split_data}')
                for data in split_data:
                    split = data.split('-')
                    if split[0] == 'disc_addr' and split[1] != self.disc_addr:

                        self.logger.info(f'BrokerMW - Connecting to new discovery at {split[1]}')
                        # Disconnect from old discovery
                        try:
                            self.req.disconnect(self.disc_addr)
                        except:
                            pass

                        self.disc_addr = split[1]
                        connect_str = "tcp://" + self.disc_addr
                        self.req.connect(connect_str)
            
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
            self.poller = zmq.Poller()

            self.req = context.socket(zmq.REQ)
            self.pub = context.socket(zmq.PUB)
            self.sub = context.socket(zmq.SUB)

            # Setup ZooKeeper before we connect to discovery
            self.init_client()
            self.run_client()

            # Subscribe to all topics
            self.sub.subscribe("")

            # Register our poller to make requests
            self.poller.register(self.req, zmq.POLLIN)
            connect_str = "tcp://" + self.disc_addr
            self.req.connect(connect_str)

            bind_string = "tcp://*:" + self.port
            self.pub.bind(bind_string)

        except Exception as e:
            raise e

    ########################################
    # connect to publishers that we are interested in with filters
    ########################################
    def connect_pubs(self, pub_addresses):
        ''' connect to publishers we are interested in '''

        # Connect to the publishers we want to hear from
        for pub in pub_addresses:
            self.sub.connect(f'tcp://{pub}')

        # register the SUB socket for incoming messages
        self.logger.debug(
            "BrokerMW::connect_pubs - register the SUB socket for incoming messages")
        self.poller.register(self.sub, zmq.POLLIN)

    ########################################
    # register with the discovery service
    ########################################
    def register(self, name):
        ''' register the appln with the discovery service '''
        try:
            register_req = discovery_pb2.RegisterReq()  # allocate
            register_req.role = "broker"  # this will change to an enum later on

            register_req.address = self.addr
            register_req.port = self.port

            unique_id = name
            register_req.id = unique_id  # fill up the ID

            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.msg_type = discovery_pb2.REGISTER
            disc_req.register_req.CopyFrom(register_req)

            buf2send = disc_req.SerializeToString()

            # we use the "send" method of ZMQ that sends the bytes
            self.req.send(buf2send)

            return self.event_loop()

        except Exception as e:
            raise e

    ########################################
    # lookup publishers that match our list of topics so we can connect
    ########################################
    def lookup_all_pubs(self):
        ''' lookup a list of all publishers so we can connect to get their info '''

        try:
            lookup_msg = discovery_pb2.LookupAllPubsReq()  # allocate
            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.msg_type = discovery_pb2.LOOKUP_ALL_PUBS
            disc_req.all_pubs.CopyFrom(lookup_msg)

            buf2send = disc_req.SerializeToString()
            self.req.send(buf2send)

            return self.event_loop()

        except Exception as e:
            raise e

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
            self.logger.debug("BrokerMW::handle_reply")

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
            elif (disc_resp.msg_type == discovery_pb2.LOOKUP_ALL_PUBS):

                real_pubs = []
                pubs = list(disc_resp.all_pubs.pub_addresses.split(','))
                for pub in pubs:
                    if pub:
                        real_pubs.append(pub)
                return real_pubs
            elif (disc_resp.msg_type == discovery_pb2.LOOKUP_PUB_BY_TOPIC):
                real_pubs = []
                pubs = list(disc_resp.resp.pub_addresses.split(','))
                for pub in pubs:
                    if pub:
                        real_pubs.append(pub)
                return real_pubs
            else:  # anything else is unrecognizable by this object
                # raise an exception here
                raise Exception("Unrecognized response message")

        except Exception as e:
            raise e

    #################################################################
    # disseminate the data on our pub socket
    #################################################################
    def disseminate(self, topic, content):
        try:
            self.logger.info(f"BrokerMW::disseminate - {topic} {content.content}")

            topic_msg = topic_pb2.topicMessage()
            topic_msg.topic = topic
            topic_msg.content = content.content
            topic_msg.timestamp = content.timestamp

            buf2send = topic_msg.SerializeToString()
            self.pub.send_multipart([topic, buf2send])

        except Exception as e:
            raise e

    #################################################################
    # handle an incoming message from a pub
    #################################################################
    def handle_message (self):
        try:
            self.logger.info("BrokerMW: Received a message from a publisher")

            # let us first receive all the bytes
            mp_message = self.sub.recv_multipart ()

            topic = mp_message[0]
            bytesRcvd = mp_message[1]

            # now use protobuf to deserialize the bytes
            message = topic_pb2.topicMessage()
            message.ParseFromString (bytesRcvd)

            latency = datetime.now() - datetime.strptime(message.timestamp, "%m/%d/%Y, %H:%M:%S.%f")

            return [topic, message]

        except Exception as e:
            raise e