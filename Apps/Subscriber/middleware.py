###############################################
# Author: Aniruddha Gokhale
# Updated by: Patrick Muradaz
# Vanderbilt University
# Purpose: Subscriber middleware for PAs
# Semester: Spring 2023
###############################################
#
# Here is what this middleware should do
# (1) it must maintain the ZMQ sockets, one in the REQ role to talk to the 
#     Discovery service and one in the SUB role to receive topic data 
# (2) It must, on behalf of the application logic, register the subscriber 
#     application with the discovery service. To that end, it must use the 
#     protobuf-generated serialization code to send the appropriate message 
#     with the contents to the discovery service.
# (3) On behalf of the subscriber appln, it must use the ZMQ setsockopt method 
#     to subscribe to all the user-supplied topics of interest. 
# (4) Since it is a receiver, the middleware object will maintain a poller 
#     and even loop waiting for some subscription to show up(or response from 
#     Discovery service).
# (5) On receipt of a subscription, determine which topic it is and let the 
#     application level handle the incoming data. To that end, you may need to 
#     make an upcall to the application-level object.
#
# Import statements
import sys, os, zmq, json
sys.path.append(os.getcwd())
from Apps.Common.common import handle_exception, \
  send_message, register, is_ready
from Apps.Common import discovery_pb2

"""Subscriber Middleware class"""
class SubscriberMW():

  """constructor"""
  def __init__(self, logger):
    self.logger = logger  # internal logger for print statements
    self.req = None       # will be a ZMQ REQ socket for register with discovery
    self.sub = None       # will be a ZMQ REQ socket for subscriptions
    self.poller = None    # used to wait on incoming subscriptions
    self.addr = None      # advertised IP address (might not be necessary)
    self.port = None      # port num (might not be necessary)

  """configure/initialize"""
  def configure(self, args):
    try:
      self.logger.debug("SubscriberMW::configure")
      # retrieve our advertised IP addr and the publication port num
      self.port = args.port
      self.addr = args.addr
      # setup ZMQ
      context = zmq.Context()
      self.poller = zmq.Poller()
      # Now setup the sockets
      self.req = context.socket(zmq.REQ)
      self.sub = context.socket(zmq.SUB)
      self.poller.register(self.req, zmq.POLLIN)
      connect_str = "tcp://" + args.discovery
      self.req.connect(connect_str)
      self.logger.debug(f"DiscoveryMW::configure - connected to: {connect_str}")
    except Exception as e: handle_exception(e)

  """register with the discovery service"""
  def register(self, name, topiclist):
    try:
      self.logger.debug("SubscriberMW::register")
      # First build a register req message
      register_req = discovery_pb2.RegisterReq()
      register(self.logger, register_req.SUBSCRIBER, name, 
               self.addr, self.port, self.req, topiclist=topiclist)
      # now go to our event loop to receive a response to this request
      return self.event_loop()
    except Exception as e: handle_exception(e)

  """check if the discovery service gives the green light to proceed"""
  def is_ready(self):
    try:
      self.logger.debug("PublisherMW::is_ready")
      is_ready(self.logger, self.req)
      # now go to our event loop to receive a response to this request
      return self.event_loop()
    except Exception as e: handle_exception(e)

  """locate all of the publishers that we care about"""
  def locate_pubs(self, topiclist):
    try:
      self.logger.debug("SubscriberMW::locate_pubs")
      # build the request message
      disc_req = discovery_pb2.DiscoveryReq()
      getpubs_msg = discovery_pb2.LookupPubByTopicReq()
      getpubs_msg.topiclist.extend(topiclist)
      disc_req.msg_type = discovery_pb2.LOOKUP_PUB_BY_TOPIC
      disc_req.topics.CopyFrom(getpubs_msg)
      # send the message
      send_message(self.req, disc_req)
      # now go to our event loop to receive a response to this request
      self.logger.debug("SubscriberMW::locate_pubs - now wait for reply")
      publishers = self.event_loop()
      return publishers
    except Exception as e: handle_exception(e)

  """subscribe to the publishers that we care about"""
  def sub_to_pubs(self, pubs, topiclist):
    try:
      self.logger.debug("SubscriberMW::sub_to_pubs")
      # First, set up the ZMQ socket filters for our desired topics
      for topic in topiclist:
        self.logger.debug(f"SubscriberMW::sub_to_pubs - topic: {topic}")
        self.sub.setsockopt(zmq.SUBSCRIBE, topic.encode('utf-8'))
      # Then subscribe to each publisher we care about
      for pub in pubs:
        p = json.loads(pub)
        pub_addr = f"tcp://{p['ip']}:{p['port']}"
        self.sub.connect(pub_addr)
        self.logger.info(f"Subscribed to publisher: {pub_addr}")
      # Then listen from messages from our subscriptions
      self.listen_to_pubs()      
    except Exception as e: handle_exception(e)

  """listen to all of our subscribed publishers"""
  def listen_to_pubs(self):
    try:
      self.logger.debug("BrokerMW::listen_to_pubs")
      while True:
        # receive messages from the publishers
        message_bytes = self.sub.recv_multipart()
        message = str(message_bytes[0], 'UTF-8')
        self.logger.info(f"Message from publisher: {message}")
    except Exception as e: handle_exception(e)

  """run event loop where we expect to receive replies to sent requests"""
  def event_loop(self):
    try:
      self.logger.debug("BrokerMW::event_loop - run the event loop")
      while True:
        # poll for events. We give it an infinite timeout.
        # The return value is a socket to event mask mapping
        events = dict(self.poller.poll())
        if self.req in events: return self.handle_reply()
    except Exception as e: handle_exception(e)
            
  """handle an incoming reply"""
  def handle_reply(self):
    try:
      self.logger.debug("BrokerMW::handle_reply")
      # let us first receive all the bytes
      bytesRcvd = self.req.recv()
      # now use protobuf to deserialize the bytes
      disc_resp = discovery_pb2.DiscoveryResp()
      disc_resp.ParseFromString(bytesRcvd)
      # Depending on the message type, the contents of the msg will differ
      if(disc_resp.msg_type == discovery_pb2.REGISTER):
        if disc_resp.register_resp.result == discovery_pb2.RegisterResp().Result.FAILURE:
          raise Exception(disc_resp.register_resp.fail_reason) # return register error
        else: return disc_resp.register_resp.result # return response to register
      elif(disc_resp.msg_type == discovery_pb2.ISREADY):
        return disc_resp.is_ready.reply # response to is_ready request
      elif(disc_resp.msg_type == discovery_pb2.LOOKUP_PUB_BY_TOPIC):
        return disc_resp.resp.publishers # response to lookup_pub... message
      else: raise Exception("Unrecognized response message.")
    except Exception as e: handle_exception(e)
