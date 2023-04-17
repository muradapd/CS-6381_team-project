###############################################
#
# Author: John Gordley
# Professor: Aniruddha Gokhale
# Vanderbilt University
#
# Active publisher MW for zookeeper interaction
#
# Created: Spring 2023
#
###############################################

# import the needed packages
import zmq  # ZMQ sockets
import sys

from kazoo.client import KazooClient

from zk_tools import unpack_znode_val, pack_znode_val

from datetime import datetime
import time

# import serialization logic
from CS6381_MW import discovery_pb2
from CS6381_MW import topic_pb2

class PublisherMW ():

    ########################################
    # constructor
    ########################################
    def __init__(self, logger, num_topics, lookup):
        self.logger = logger  # internal logger for print statements
        self.pub = None  # will be a ZMQ PUB socket for dissemination
        self.req = None  # will be a ZMQ REQ socket to talk to Discovery service
        self.poller = None  # used to wait on incoming replies
        self.addr = None  # our advertised IP address
        self.port = None  # port num where we are going to publish our topics
        self.zk_addr = None
        self.name = None

        self.disc_addr = None

        self.num_topics = num_topics
        self.lookup = lookup
        self.ppath = '/discovery'

    def clean_exit(self, name):
        self.zk.stop ()
        self.zk.close ()
        try:
            # first build a exit req message
            exit_req = discovery_pb2.ExitReq()  # allocate
            exit_req.role = "publisher"
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

        self.logger.info("PublisherMW: Cleanly exiting. Goodbye.")

    def init_client(self):
        # Set up zookeeper
        try:

            # instantiate a zookeeper client object
            self.zk = KazooClient (self.zk_addr)
            self.logger.info(f"PublisherMW: Zookeeper State -> {self.zk.state}")
            
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

                    self.logger.info(f"PublisherMW: Parent znode {self.ppath} is set.")

                    # in that case we create our child node
                    self.zk.create (self.ppath + str ("/") + self.name, value=self.name.encode(), ephemeral=True)
                    # make sure to exit the loop
                    break
                else:
                    self.logger.info(f"PublisherMW: Parent znode {self.ppath} is not up yet.")
                    time.sleep (1)

            # first we set a watcher for our parent's znode data.
            #---------------------------------------------------------
            # define a data watch function on the parent znode
            # note that this is a nested function defn
            @self.zk.DataWatch (self.ppath)
            def data_change_watcher (data, stat):
                """Data Change Watcher"""
                # self.logger.info(f"PublisherMW - DataChangeWatcher received {data}, {stat}")

                split_data = data.decode().split('|')
                self.logger.info(f'PublisherMW - DataChangeWatcher received: {split_data}')
                for data in split_data:
                    split = data.split('-')
                    if split[0] == 'disc_addr':

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

            # Next get the ZMQ context
            context = zmq.Context()

            # get the ZMQ poller object
            self.poller = zmq.Poller()
            self.zk_addr = args.discovery

            # Now acquire the REQ and PUB sockets
            self.req = context.socket(zmq.REQ)
            self.pub = context.socket(zmq.PUB)

            # Setup ZooKeeper before we connect to discovery
            self.init_client()
            self.run_client()

            # register the REQ socket for incoming events
            self.poller.register(self.req, zmq.POLLIN)
            connect_str = "tcp://" + self.disc_addr
            self.req.connect(connect_str)

            # Bind to the port we'll be publishing to
            bind_string = "tcp://*:" + self.port
            self.pub.bind(bind_string)

            self.logger.info(f"PublisherMW - {self.name} -> {self.addr}:{self.port} Configured Successfully")

        except Exception as e:
            raise e

    ########################################
    # register with the discovery service
    ########################################
    def register(self, name, topiclist):
        ''' register the appln with the discovery service '''

        try:
            self.logger.info("PublisherMW: Sending registration request to Discovery")

            register_req = discovery_pb2.RegisterReq()
            register_req.role = "publisher"
            register_req.topiclist = ','.join(topiclist)
            register_req.address = self.addr
            register_req.port = self.port
            register_req.id = name + ":" + self.addr + ":" + self.port

            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.msg_type = discovery_pb2.REGISTER
            disc_req.register_req.CopyFrom(register_req)

            buf2send = disc_req.SerializeToString()
            self.req.send(buf2send)
            return self.event_loop()

        except Exception as e:
            raise e

    #################################################################
    # run the event loop where we expect to receive a reply to a sent request
    #################################################################
    def event_loop(self):

        try:
            self.logger.debug("PublisherMW::event_loop - run the event loop")
            self.logger.info(f"PublisherMW - Waiting for events...")

            while True:
                # poll for events. We give it an infinite timeout.
                # The return value is a socket to event mask mapping
                events = dict(self.poller.poll())

                # the only socket that should be enabled, if at all, is our REQ socket.
                if self.req in events:  # this is the only socket on which we should be receiving replies
                    # handle the incoming reply and return the result
                    return self.handle_reply()

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

            if (disc_resp.msg_type == discovery_pb2.REGISTER):

                # Result of registration request
                return disc_resp.register_resp.result
            
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
            self.logger.info(f"PublisherMW - Disseminating - {topic} {content}")

            # Build the outer layer Discovery Message
            topic_msg = topic_pb2.topicMessage()
            topic_msg.topic = topic
            topic_msg.content = content
            topic_msg.timestamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S.%f")

            buf2send = topic_msg.SerializeToString()

            # we use the "send" method of ZMQ that sends the bytes
            self.pub.send_multipart([topic.encode(encoding='utf-8'), buf2send])


        except Exception as e:
            raise e