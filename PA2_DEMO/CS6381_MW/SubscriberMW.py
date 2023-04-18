# Middleware functionality for Subscribers
# John Gordley

# import the needed packages
import zmq  # ZMQ sockets

from datetime import datetime

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

    ########################################
    # configure/initialize
    ########################################
    def configure(self, args):
        ''' Initialize the object '''

        try:
            # Here we initialize any internal variables
            self.logger.debug("SubscriberMW::configure")

            # First retrieve our advertised IP addr and the publication port num
            self.port = args.port
            self.addr = args.addr

            # Next get the ZMQ context
            self.logger.debug("SubscriberMW::configure - obtain ZMQ context")
            context = zmq.Context()  # returns a singleton object

            # get the ZMQ poller object
            self.logger.debug("SubscriberMW::configure - obtain the poller")
            self.poller = zmq.Poller()

            # Now acquire the REQ and SUB sockets
            self.logger.debug(
                "SubscriberMW::configure - obtain REQ and SUB sockets")
            self.req = context.socket(zmq.REQ)
            self.sub = context.socket(zmq.SUB)

            # register the REQ socket for incoming events
            self.logger.debug(
                "SubscriberMW::configure - register the REQ socket for incoming replies")
            self.poller.register(self.req, zmq.POLLIN)

            # Now connect ourselves to the discovery service. Recall that the IP/port were
            # supplied in our argument parsing.
            self.logger.debug(
                "SubscriberMW::configure - connect to Discovery service")
            # For these assignments we use TCP. The connect string is made up of
            # tcp:// followed by IP addr:port number.
            connect_str = "tcp://" + args.discovery
            self.req.connect(connect_str)

            # Since we are the Subscriber, the best practice as suggested in ZMQ is for us to
            # "connect" to the SUB socket
            self.logger.debug(
                "SubscriberMW::configure - connect to the sub socket")
            
            self.logger.info(f"SubscriberMW - {self.addr}:{self.port} Configured Successfully")

        except Exception as e:
            raise e

    ########################################
    # connect to publishers that we are interested in with filters
    ########################################
    def connect_pubs(self, pub_addresses, topicList):
        ''' connect to publishers we are interested in '''

        self.logger.debug(f"SubscriberMW::connect_pubs - connecting to {pub_addresses}")
        self.logger.info(f"SubscriberMW - connecting to {pub_addresses}")

        # Set up socket filters for only the topics we are interested in
        for topic in topicList:
            self.sub.setsockopt_string(zmq.SUBSCRIBE, topic)

        # Connect to the publishers we want to hear from
        for pub in pub_addresses:
            if pub:
                self.sub.connect(f'tcp://{pub}')

        # register the SUB socket for incoming messages
        self.logger.debug(
            "SubscriberMW::connect_pubs - register the SUB socket for incoming messages")
        self.poller.register(self.sub, zmq.POLLIN)

        self.logger.info(f"SubscriberMW - register the SUB socket for incoming messages")

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

            unique_id = name + ":" + self.addr + ":" + self.port
            register_req.id = unique_id  # fill up the ID

            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.msg_type = discovery_pb2.REGISTER
            disc_req.register_req.CopyFrom(register_req)

            buf2send = disc_req.SerializeToString()

            self.req.send(buf2send)

            return self.event_loop()

        except Exception as e:
            raise e

    ########################################
    # check if the discovery service gives us a green signal to proceed
    ########################################
    def is_ready(self):
        ''' register the appln with the discovery service '''

        try:
            self.logger.debug("SubscriberMW::is_ready")

            isready_msg = discovery_pb2.IsReadyReq()  # allocate
            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.msg_type = discovery_pb2.ISREADY
            disc_req.is_ready.CopyFrom(isready_msg)

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
            self.logger.debug("SubscriberMW::lookup")

            # we do a similar kind of serialization as we did in the register
            # message but much simpler, and then send the request to
            # the discovery service

            # first build a Lookup message
            self.logger.debug(
                "SubscriberMW::lookup - populate the nested LookupPubByTopicReq msg")
            lookup_msg = discovery_pb2.LookupPubByTopicReq()  # allocate
            lookup_msg.topiclist = ",".join(topicList)

            self.logger.debug(
                "SubscriberMW::lookup - done populating nested LookupPubByTopicReq msg")

            # Build the outer layer Discovery Message
            self.logger.debug(
                "SubscriberMW::lookup - build the outer discovery message")
            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.msg_type = discovery_pb2.LOOKUP_PUB_BY_TOPIC
            # It was observed that we cannot directly assign the nested field here.
            # A way around is to use the CopyFrom method as shown
            disc_req.topic.CopyFrom(lookup_msg)
            self.logger.debug(
                "SubscriberMW::lookup - done building the outer message")

            # now let us stringify the buffer and print it. This is actually a sequence of bytes and not
            # a real string
            buf2send = disc_req.SerializeToString()
            self.logger.debug(
                "Stringified serialized buf = {}".format(buf2send))

            # now send this to our discovery service
            self.logger.debug(
                "SubscriberMW::lookup - send stringified buffer to Discovery service")
            # we use the "send" method of ZMQ that sends the bytes
            self.req.send(buf2send)

            self.logger.info(f"SubscriberMW - Looking up topics: {topicList}")
            self.logger.info(f"SubscriberMW - Sent lookup request to Discovery")

            # now go to our event loop to receive a response to this request
            self.logger.debug(
                "SubscriberMW::lookup - now wait for list of publishers")
            return self.event_loop()

        except Exception as e:
            raise e

    #################################################################
    # run the event loop where we expect to receive a reply to a sent request
    #################################################################
    def event_loop(self):

        try:
            self.logger.debug("SubscriberMW::event_loop - run the event loop")
            self.logger.info("SubscriberMW - Waiting for events...")

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
            self.logger.debug("SubscriberMW::handle_reply")

            # let us first receive all the bytes
            bytesRcvd = self.req.recv()

            # now use protobuf to deserialize the bytes
            disc_resp = discovery_pb2.DiscoveryResp()
            disc_resp.ParseFromString(bytesRcvd)

            self.logger.info(f"SubscriberMW - Received reply of type {disc_resp.msg_type}")

            # depending on the message type, the remaining
            # contents of the msg will differ

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
            self.logger.info(f"SubscriberMW - Received a message")

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

    ########################################
    # tell discovery service we have exited
    ########################################
    def exit(self, name):
        ''' exit the discovery service '''

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
