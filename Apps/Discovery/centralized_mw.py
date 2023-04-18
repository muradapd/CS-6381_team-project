###############################################
# Author: Patrick Muradaz
# Vanderbilt University
# Purpose: Centralized discovery middleware for PAs
# Semester: Spring 2023
###############################################
#
# Import statements
import zmq, json, sys, os
sys.path.append(os.getcwd())
from Apps.Common.common import \
  handle_exception, format_pubs, send_message
from Apps.Common import discovery_pb2

"""Discovery Middleware class"""
class CentralizedMW():

    """constructor"""
    def __init__(self, logger, dissemination):
        self.dissemination = dissemination  # direct or via broker
        self.logger = logger      # internal logger for print statements
        self.rep = None           # will be a ZMQ REP socket for discovery
        self.poller = None        # used to wait on incoming replies
        self.addr = None          # our advertised IP address
        self.port = None          # port num where we listen for pubs/subs
        self.numpubs = None       # number of publishers to expect in the system
        self.numsubs = None       # number of subscribers to expect in the system
        self.pubs = None          # the array of publishers that are registering
        self.subs = None          # the array of subscribers that are registering
        self.broker = None        # the broker to use if we are using that approach
        self.ready_sent = 0       # number of ready replys sent (will match pubs/subs)

    """configure/initialize"""
    def configure(self, args):
        try:
            self.logger.debug("CentralizedMW::configure")
            # Here we initialize any internal variables
            self.port = args.port
            self.addr = args.addr
            # now set up ZMQ
            context = zmq.Context()  # Next get the ZMQ context (singleton object)
            self.poller = zmq.Poller()  # get the ZMQ poller object
            # set up the REP socket
            self.rep = context.socket(zmq.REP)
            self.poller.register(self.rep, zmq.POLLIN)
            bind_string = f"tcp://{self.addr}:{self.port}"
            self.logger.debug(f"CentralizedMW::configure - bound to: {bind_string}")
            self.rep.bind(bind_string)  # bind to the REP socket
        except Exception as e: handle_exception(e)

    """register with the discovery service"""
    def listen(self, pubs, subs, numpubs, numsubs):
        try:
            self.logger.debug("CentralizedMW::listen")
            self.pubs = pubs; self.subs = subs
            self.numpubs = numpubs; self.numsubs = numsubs
            
            while True:
                # poll for events. We give it an infinite timeout.
                # The return value is a socket to event mask mapping
                events = dict(self.poller.poll())
                if self.rep in events: self.handle_message()
        except Exception as e: handle_exception(e)

    """handle an incoming message"""
    def handle_message(self):
        try:
            self.logger.debug("CentralizedMW::handle_message")
            # let us first receive all the bytes
            bytesRcvd = self.rep.recv()
            # now use protobuf to deserialize the bytes
            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.ParseFromString(bytesRcvd)
            # Depending on the message type, the contents of the msg will differ
            if (disc_req.msg_type == discovery_pb2.ISREADY): self.handle_is_ready()
            elif (disc_req.msg_type == discovery_pb2.REGISTER): self.handle_register(disc_req.register_req)
            elif (disc_req.msg_type == discovery_pb2.LOOKUP_ALL_PUBS): self.handle_pub_lookup(disc_req, return_all_pubs=True)
            elif (disc_req.msg_type == discovery_pb2.LOOKUP_PUB_BY_TOPIC): self.handle_pub_lookup(disc_req, return_all_pubs=False)
            else: raise Exception("Unrecognized response message")
        except Exception as e: handle_exception(e)

    """gives a green signal to proceed"""
    def handle_is_ready(self):
        try:
            self.logger.debug("CentralizedMW::handle_is_ready")
            # buiild the response message
            disc_resp = discovery_pb2.DiscoveryResp()
            isreadyresp_msg = discovery_pb2.IsReadyResp()
            if len(self.pubs) == self.numpubs and len(self.subs) == self.numsubs:
                if self.dissemination == "Direct" or (self.dissemination == "Broker" and self.broker):
                    isreadyresp_msg.reply = True
                    self.logger.info("All ready message sent.")
                    self.ready_sent += 1
                else: isreadyresp_msg.reply = False
            else: isreadyresp_msg.reply = False
            disc_resp.msg_type = discovery_pb2.ISREADY
            disc_resp.is_ready.CopyFrom(isreadyresp_msg)
            # send the message
            send_message(self.rep, disc_resp)
        except Exception as e: handle_exception(e)

    """handle a registration with the discovery service"""
    def handle_register(self, register_req):
        try:
            self.logger.debug("CentralizedMW::handle_register")
            id = register_req.id; req_id = f"{id.name} - {id.ip}:{id.port}"
            self.logger.info(f"New registration request from: {req_id}")

            if (register_req.role == discovery_pb2.RegisterReq().Role.PUBLISHER):
                self.logger.debug("CentralizedMW::handle_message - handle pub register")
                self.pubs.append(register_req)
            elif (register_req.role == discovery_pb2.RegisterReq().Role.SUBSCRIBER):
                self.logger.debug("CentralizedMW::handle_message - handle sub register")
                self.subs.append(register_req)
            elif (register_req.role == discovery_pb2.RegisterReq().Role.BROKER):
                self.logger.debug("CentralizedMW::handle_message - handle broker register")
                self.broker = register_req
            else: raise Exception("Unrecognized result message")

            # build the response message
            disc_resp = discovery_pb2.DiscoveryResp()
            register_resp = discovery_pb2.RegisterResp()
            register_resp.result = register_resp.Result.SUCCESS
            disc_resp.msg_type = discovery_pb2.REGISTER
            disc_resp.register_resp.CopyFrom(register_resp)
            # send the message
            send_message(self.rep, disc_resp)
            self.logger.info(f"Registration request handled successfully.")
        except Exception as e: handle_exception(e)

    """responds with all of the requested pubs"""
    def handle_pub_lookup(self, disc_req, return_all_pubs):
        try:
            self.logger.debug("CentralizedMW::handle_pub_lookup")
            # build the response message
            disc_resp = discovery_pb2.DiscoveryResp()
            if return_all_pubs: 
                pubs_msg = discovery_pb2.LookupAllPubsResp()
                pubs_msg.publishers.extend(format_pubs(self.pubs))
                disc_resp.msg_type = discovery_pb2.LOOKUP_ALL_PUBS
                disc_resp.pubs_resp.CopyFrom(pubs_msg)
            else:
                matching_pubs_msg = discovery_pb2.LookupPubByTopicResp()  
                if self.dissemination == "Broker": matching_pubs_msg.publishers.extend(format_pubs([self.broker]))
                else: matching_pubs_msg.publishers.extend(self.get_matching_pubs(disc_req.topics))
                disc_resp.msg_type = discovery_pb2.LOOKUP_PUB_BY_TOPIC
                disc_resp.resp.CopyFrom(matching_pubs_msg)
            # send the message
            send_message(self.rep, disc_resp)
        except Exception as e: handle_exception(e)

    """gets all of the pubs that match the topiclist"""
    def get_matching_pubs(self, topics):
        try:
          self.logger.debug("CentralizedMW::get_matching_pubs")
          # First, set up the topiclist and matching_pubs variables
          topiclist = list(topics.topiclist); matching_pubs = []
          # Check each pub to see if it matches the topiclist
          for pub in self.pubs:
              for topic in topiclist:
                  if topic in pub.topiclist:
                      # If the publisher matches the topiclist, add it to matches
                      publisher = {"name": pub.id.name, "ip": pub.id.ip, "port": pub.id.port}
                      matching_pubs.append(json.dumps(publisher)); break
          return matching_pubs
        except Exception as e: handle_exception(e)
