###############################################
# Author: Aniruddha Gokhale
# Updated by: Patrick Muradaz
# Vanderbilt University
# Purpose: Publisher middleware for PAs
# Semester: Spring 2023
###############################################
#
# Here is what this middleware should do
# (1) it must maintain the ZMQ sockets, one in the REQ role to talk to the 
#     Discovery service and one in the PUB role to disseminate topics
# (2) It must, on behalf of the application logic, register the publisher 
#     application with the discovery service. To that end, it must use the 
#     protobuf-generated serialization code to send the appropriate message 
#     with the contents to the discovery service.
# (3) On behalf of the publisher appln, it must also query the discovery 
#     service (when instructed) to see if it is fine to start dissemination
# (4) It must do the actual dissemination activity of the topic data when 
#     instructed by the 
#
# Import statements
import sys, os, zmq
sys.path.append(os.getcwd())
from Apps.Common.common import handle_exception, \
  disseminate, register, is_ready
from Apps.Common import discovery_pb2
from Apps.Common.topic_selector import TopicSelector

"""Publisher Middleware class"""
class PublisherMW():

  """constructor"""
  def __init__(self, logger):
    self.logger = logger  # internal logger for print statements
    self.pub = None       # will be a ZMQ PUB socket for dissemination
    self.req = None       # will be a ZMQ REQ socket to talk to Discov service
    self.poller = None    # used to wait on incoming replies
    self.addr = None      # our advertised IP address
    self.port = None      # port num where we are going to publish our topics

  """configure/initialize"""
  def configure(self, args):
    try:
      self.logger.debug("PublisherMW::configure")
      # First retrieve our advertised IP addr and the publication port num
      self.port = args.port
      self.addr = args.addr
      # Next setup ZMQ
      context = zmq.Context()  # returns a singleton object
      self.poller = zmq.Poller()
      # Now setup the sockets
      self.req = context.socket(zmq.REQ)
      self.pub = context.socket(zmq.PUB)
      self.poller.register(self.req, zmq.POLLIN)
      connect_str = "tcp://" + args.discovery
      self.req.connect(connect_str)
      self.logger.debug(f"DiscoveryMW::configure - connected to: {connect_str}")
      bind_string = f"tcp://{self.addr}:{self.port}"
      self.pub.bind(bind_string)
      self.logger.debug(f"PublisherMW::configure - bound to socket: {bind_string}")
    except Exception as e: handle_exception(e)

  """register with the discovery service using the common function"""
  def register(self, name, topiclist):
    try:
      self.logger.debug("PublisherMW::register")
      # First build a register req message
      register_req = discovery_pb2.RegisterReq()
      register(self.logger, register_req.PUBLISHER, name, 
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

  """run the event loop where we expect to receive a reply to a sent request"""
  def event_loop(self):
    try:
      self.logger.debug("PublisherMW::event_loop - run the event loop")
      while True:
        # poll for events. We give it an infinite timeout.
        # The return value is a socket to event mask mapping
        events = dict(self.poller.poll())
        if self.req in events: return self.handle_reply()
    except Exception as e: handle_exception(e)

  """handle an incoming reply"""
  def handle_reply(self):
    try:
      self.logger.debug("PublisherMW::handle_reply")
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
      else: raise Exception("Unrecognized response message")
    except Exception as e: handle_exception(e)
            
  """disseminate the data on our pub socket using the common function"""
  def disseminate(self, iters, topiclist):
      try:
        self.logger.debug("PublisherMW::disseminate")
        ts = TopicSelector()
        for i in range(iters):
          # Here, we choose to disseminate on all topics that we publish.  
          # Also, we don't care about their values. But in future assignments, this can change.
          for topic in topiclist:
            data = topic + ":" + ts.gen_publication(topic)
            disseminate(self.logger, self.pub, data)
        self.logger.info("Dissemination finished. Exiting.")
      except Exception as e: handle_exception(e)
