###############################################
# Author: Aniruddha Gokhale
# Updated by: Patrick Muradaz
# Vanderbilt University
# Purpose: Broker middleware for PAs
# Semester: Spring 2023
###############################################
#
# The broker serves as a proxy and hence has both publisher and subscriber roles. 
# So in addition to the REQ socket to talk to the Discovery service, it will have 
# both PUB and SUB sockets as it must work on behalf of the real publishers and 
# subscribers. So this will have the logic of both publisher and subscriber middleware.
#
# Import statements
import sys, os, zmq, json
sys.path.append(os.getcwd())
from Apps.Common.common import handle_exception, \
  send_message, disseminate, register, is_ready
from Apps.Common import discovery_pb2

"""Broker Middleware class"""
class BrokerMW():

  """constructor"""
  def __init__(self, logger):
    self.logger = logger  # internal logger for print statements
    self.pub = None       # will be a ZMQ PUB socket for dissemination
    self.sub = None       # will be a ZMQ SUB socket for listening to pubs
    self.req = None       # will be a ZMQ REQ socket to talk to Discov service
    self.poller = None    # used to wait on incoming replies
    self.addr = None      # our advertised IP address
    self.port = None      # port num where we are going to publish our topics

  """configure/initialize"""
  def configure(self, args):
    try:
      self.logger.debug("BrokerMW::configure")
      # First retrieve our advertised IP addr and the publication port num
      self.port = args.port
      self.addr = args.addr
      # Now setup ZMQ
      context = zmq.Context()  # returns a singleton object
      self.poller = zmq.Poller()
      # Now setup the sockets
      self.req = context.socket(zmq.REQ)
      self.pub = context.socket(zmq.PUB)
      self.sub = context.socket(zmq.SUB)
      self.poller.register(self.req, zmq.POLLIN)
      connect_str = "tcp://" + args.discovery
      self.logger.debug(f"BrokerMW::configure - connected to: {connect_str}")
      self.req.connect(connect_str)
      bind_string = f"tcp://{self.addr}:{self.port}"
      self.logger.debug(f"BrokerMW::configure - bound to: {bind_string}")
      self.pub.bind(bind_string)
      # Finally, subscribe to any/all topics
      self.sub.subscribe("")
    except Exception as e: handle_exception(e)

  """register with the discovery service using the common function"""
  def register(self, name):
    try:
      self.logger.debug("BrokerMW::register")
      # build the request message
      register_req = discovery_pb2.RegisterReq()
      register(self.logger, register_req.BROKER, 
               name, self.addr, self.port, self.req)
      # now go to our event loop to receive a response to this request
      return self.event_loop()
    except Exception as e: handle_exception(e)

  """check if the discovery service gives the green light to proceed"""
  def is_ready(self):
    try:
      self.logger.debug("BrokerMW::is_ready")
      is_ready(self.logger, self.req)
      # now go to our event loop to receive a response to this request
      return self.event_loop()
    except Exception as e: handle_exception(e)

  """locate all of the registered publishers"""
  def locate_pubs(self):
    try:
      self.logger.debug("BrokerMW::locate_pubs")
      # build the request message
      disc_req = discovery_pb2.DiscoveryReq()
      getpubs_msg = discovery_pb2.LookupAllPubsReq()
      disc_req.msg_type = discovery_pb2.LOOKUP_ALL_PUBS
      disc_req.pubs_req.CopyFrom(getpubs_msg)
      # send the message
      send_message(self.req, disc_req)
      # now go to our event loop to receive a response to this request
      publishers = self.event_loop()
      return publishers
    except Exception as e: handle_exception(e)

  """subscribe to all of the registered publishers"""
  def sub_to_pubs(self, pubs):
    try:
      self.logger.debug("BrokerMW::sub_to_pubs")
      # Subscribe to each publisher
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
        # receive and disseminate messages from the publishers
        message_bytes = self.sub.recv_multipart()
        message = str(message_bytes[0], 'UTF-8')
        self.logger.info(f"Passing on message from publisher: {message}")
        disseminate(self.logger, self.pub, message)
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
      if disc_resp.msg_type == discovery_pb2.REGISTER:
        if disc_resp.register_resp.result == discovery_pb2.RegisterResp().Result.FAILURE:
          raise Exception(disc_resp.register_resp.fail_reason) # return register error
        else: return disc_resp.register_resp.result # return response to register
      elif disc_resp.msg_type == discovery_pb2.ISREADY:
        return disc_resp.is_ready.reply # return response to is_ready request
      elif disc_resp.msg_type == discovery_pb2.LOOKUP_ALL_PUBS:
        return disc_resp.pubs_resp.publishers # return response to lookup_all_pubs request
      else: raise Exception("Unrecognized response message.")
    except Exception as e: handle_exception(e)
