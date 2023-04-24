###############################################
# Author: Patrick Muradaz
# Vanderbilt University
# Purpose: Distributed discovery middleware for PAs
# Semester: Spring 2023
###############################################
#
# Import statements
import zmq, sys, os
sys.path.append(os.getcwd())
from Apps.Common.common import handle_exception, \
    format_pubs, send_message, hash_func
from Apps.Common import discovery_pb2
from Visualization.DHT_vis_util import write_vis_command

"""Discovery Middleware class"""
class DistributedMW():

    """constructor"""
    def __init__(self, logger, dissemination):
        self.dissemination = dissemination # direct or via broker
        self.logger = logger       # internal logger for print statements
        self.rep = None            # will be a ZMQ REP socket for discovery
        self.req = None            # will be a ZMQ REQ socket for DHT discovery
        self.poller = None         # used to wait on incoming replies
        self.known_node = None     # the IP and port of the known DHT node
        self.bits_hash = None      # the number of bits that we use when hashing
        self.node_id = None        # the ID of this node in the DHT ring
        self.predecessor = None    # the info for our predecessor node
        self.successor = None      # the info for our successor node
        self.addr = None           # our advertised IP address
        self.port = None           # port num where we listen for pubs/subs
        self.numpubs = None        # number of publishers to expect in the system
        self.numsubs = None        # number of subscribers to expect in the system
        self.hash_table = None     # the hash table that is used in DHT mode
        self.broker = None         # the broker to use if we are using that approach
        self.reg_count = 0         # number of pubs/subs registered (eventually consistent across DHT)
        self.ready_sent = 0        # number of ready replys sent (will match pubs/subs)

    """configure/initialize"""
    def configure(self, args):
        try:
            self.logger.debug("DistributedMW::configure")
            # Here we initialize any internal variables
            self.known_node = args.knownnode
            self.port = args.port
            self.addr = args.addr
            # now set up ZMQ
            context = zmq.Context()  # Next get the ZMQ context (singleton object)
            self.poller = zmq.Poller() # get the ZMQ poller object
            # set up the REP socket
            self.rep = context.socket(zmq.REP) # Now acquire the REP socket
            self.poller.register(self.rep, zmq.POLLIN) # register the REP socket incoming events
            bind_string = f"tcp://{self.addr}:{self.port}"
            self.logger.debug(f"DistributedMW::configure - bound to: {bind_string}")
            self.rep.bind(bind_string) # bind to the REP socket
            # set up the REQ socket
            self.req = context.socket(zmq.REQ) # Now acquire the REQ socket
            self.poller.register(self.req, zmq.POLLIN) # register REQ socket for incoming events
            connect_str = "tcp://" + self.known_node # connect to the given known DHT node
            self.logger.debug(f"DistributedMW::configure - connected to: {connect_str}")
            self.req.connect(connect_str)      
        except Exception as e: handle_exception(e)

# ======================================== CORE FUNCTIONS ======================================== #
    """listen for pub/sub registers with our service"""
    def register_dht(self, bits_hash):
        try:
            self.logger.debug("DistributedMW::register_dht")
            # get our node id
            self.bits_hash = bits_hash
            to_hash = f"{self.addr}:{self.port}"
            node_id = hash_func(self.bits_hash, to_hash)
            next_id = hash_func(self.bits_hash, self.known_node)
            result = {"node_id": node_id}
            # determine if we are the fist node in the ring
            address = f"{self.addr}:{self.port}"
            if self.known_node == address: return result
            # First build a register req message
            register_req = discovery_pb2.RegisterReq()
            register_req.role = register_req.DHT_NODE
            register_req.id.node_id = node_id
            register_req.id.ip = self.addr
            register_req.id.port = self.port
            # Build the outer layer Discovery Message
            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.msg_type = discovery_pb2.REGISTER
            disc_req.register_req.CopyFrom(register_req)
            write_vis_command('Visualization/commands.txt', 'request', node_id, next_id, 'register_dht')
            send_message(self.req, disc_req)
            # now go to our event loop to receive a response to this request
            res = self.event_loop()
            result["predecessor"] = res.predecessor
            result["successor"] = res.successor
            self.format_neighbors(res.predecessor, res.successor)
            self.logger.debug(f"DistributedMW::register_dht - res from known node: {result}")
            return result
        except Exception as e: handle_exception(e)

    """listen for new registration and lookup requests"""
    def listen(self, hash_table, numpubs, numsubs, node_id):
        try:
            self.logger.debug(f"DistributedMW::listen")
            self.node_id = node_id; self.hash_table = hash_table
            self.numpubs = numpubs; self.numsubs = numsubs
            
            while True:
                self.logger.debug("DistributedMW::listen - LISTENING")
                # poll for events. We give it an infinite timeout.
                # The return value is a socket to event mask mapping
                events = dict(self.poller.poll())
                if self.rep in events: self.handle_message()
        except Exception as e: handle_exception(e)

# ======================================== CORE HELPERS ======================================== #
    """handle an incoming message"""
    def handle_message(self):
        try:
            self.logger.debug("DistributedMW::handle_message")
            # let us first receive all the bytes
            bytesRcvd = self.rep.recv()
            # now use protobuf to deserialize the bytes
            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.ParseFromString(bytesRcvd)
            self.logger.debug(f"DistributedMW::listen - disc req: {disc_req}")
            # Depending on the message type, the contents of the msg will differ
            if disc_req.msg_type == discovery_pb2.ISREADY: self.handle_is_ready()
            elif disc_req.msg_type == discovery_pb2.REGISTER: self.handle_register(disc_req.register_req)
            elif disc_req.msg_type == discovery_pb2.LOOKUP_PUB_BY_TOPIC:
                self.handle_pub_lookup(disc_req, return_all_pubs=False)
            elif disc_req.msg_type == discovery_pb2.LOOKUP_ALL_PUBS: 
                self.handle_pub_lookup(disc_req, return_all_pubs=True)
            elif disc_req.msg_type == discovery_pb2.LOCATE_NEW_NODE:
                new_node = disc_req.locate_req.new_node
                location_info = self.determine_node_location(new_node)
                self.handle_locate_request(location_info=location_info)
            elif disc_req.msg_type == discovery_pb2.LOCATE_HASH_TABLE:
                topic_hash = disc_req.locate_req.topic_info.topic_hash
                app_id = disc_req.locate_req.topic_info.app_id
                app_type = disc_req.locate_req.topic_info.app_type
                success = self.determine_topic_location(topic_hash, app_id, app_type)
                self.handle_locate_request(success=success)
            elif disc_req.msg_type == discovery_pb2.LOCATE_PUB_BY_TOPIC_HASH:
                topic_hash = disc_req.locate_req.topic_info.topic_hash
                start_node_id = disc_req.locate_req.start_node_id
                matching_pubs = self.get_pubs_matching_topic(topic_hash, start_node_id)
                self.handle_locate_request(matching_pubs=matching_pubs)
            elif disc_req.msg_type == discovery_pb2.LOCATE_ALL_PUBS:
                start_node_id = disc_req.locate_req.start_node_id
                all_pubs = self.get_all_pubs(start_node_id)
                self.handle_locate_request(all_pubs=all_pubs)
            elif disc_req.msg_type == discovery_pb2.UPDATE_NODE:
                new_node = disc_req.update_req.new_node
                start_node_id = disc_req.update_req.start_node_id
                which_neighbor = disc_req.update_req.which_neighbor
                if new_node.node_id: self.update_neighbor(which_neighbor, new_node)
                elif new_node.name: self.register_broker(new_node, start_node_id)
                elif start_node_id: self.update_reg_count(start_node_id)
                else: raise Exception("Unrecognized response message")
                if self.node_id != start_node_id: self.respond_to_register(None)
            else: raise Exception("Unrecognized response message")
        except Exception as e: handle_exception(e)

    """gives a green signal to proceed"""
    def handle_is_ready(self):
        try:
            self.logger.debug("DistributedMW::handle_is_ready")
            # build the response message
            disc_resp = discovery_pb2.DiscoveryResp()
            isreadyresp_msg = discovery_pb2.IsReadyResp()
            self.logger.debug(f"DistributedMW::handle_is_ready - rc: {self.reg_count}; np: {self.numpubs}; ns: {self.numsubs}")
            if self.reg_count == self.numpubs + self.numsubs:
                if self.dissemination == "Direct" or (self.dissemination == "Broker" and self.broker):
                    isreadyresp_msg.reply = True
                    self.logger.debug("DistributedMW::handle_is_ready - Ready message sent.")
                    self.ready_sent += 1
                    if self.ready_sent >= self.numpubs + self.numsubs: 
                        self.logger.info("All ready messages sent!")
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
            self.logger.debug("DistributedMW::handle_register")
            id = register_req.id; req_id = f"{id.name} - {id.ip}:{id.port}"
            self.logger.info(f"New registration request from: {req_id}")
            dht_info = None

            if register_req.role == discovery_pb2.RegisterReq().Role.PUBLISHER:
                write_vis_command('Visualization/commands.txt', 'configure', id.name, id.port, "publisher")
                write_vis_command('Visualization/commands.txt', 'request', id.port, self.node_id, 'register_pub')
                self.register_topic_hashes(register_req, app_type="PUB")
            elif register_req.role == discovery_pb2.RegisterReq().Role.SUBSCRIBER:
                write_vis_command('Visualization/commands.txt', 'configure', id.name, id.port, "subscriber")
                write_vis_command('Visualization/commands.txt', 'request', id.port, self.node_id, 'register_sub')
                self.register_topic_hashes(register_req, app_type="SUB")
            elif register_req.role == discovery_pb2.RegisterReq().Role.BROKER:
                self.register_broker(register_req.id, self.node_id)
            elif register_req.role == discovery_pb2.RegisterReq().Role.DHT_NODE:
                dht_info = self.handle_dht_register(register_req.id)
            else: raise Exception("Unrecognized result message")
            self.respond_to_register(dht_info)
            self.logger.info(f"Registration request handled successfully.")
        except Exception as e: handle_exception(e)

    """responds with all of the requested pubs"""
    def handle_pub_lookup(self, disc_req, return_all_pubs):
        try:
            self.logger.debug(f"DistributedMW::handle_pub_lookup")
            # build the response message
            disc_resp = discovery_pb2.DiscoveryResp()
            if return_all_pubs: 
                pubs_msg = discovery_pb2.LookupAllPubsResp()
                pubs_msg.publishers.extend(self.get_all_pubs(self.node_id))
                disc_resp.msg_type = discovery_pb2.LOOKUP_ALL_PUBS
                disc_resp.pubs_resp.CopyFrom(pubs_msg)
            else:
                matching_pubs_msg = discovery_pb2.LookupPubByTopicResp()
                if self.dissemination == "Broker": matching_pubs_msg.publishers.extend(format_pubs([self.broker]))
                else: matching_pubs_msg.publishers.extend(format_pubs(self.get_pubs_matching_topics(disc_req.topics)))
                disc_resp.msg_type = discovery_pb2.LOOKUP_PUB_BY_TOPIC
                disc_resp.resp.CopyFrom(matching_pubs_msg)
            # send the message
            send_message(self.rep, disc_resp)
        except Exception as e: handle_exception(e)

    """handle a registration with the discovery service"""
    def handle_locate_request(self, location_info=None, success=None, matching_pubs=None, all_pubs=None):
        try:
            self.logger.debug("DistributedMW::handle_locate_request")
            # build the response message
            disc_resp = discovery_pb2.DiscoveryResp()
            locate_resp = discovery_pb2.LocateResp()
            if location_info:
                locate_resp.location_info.predecessor = location_info["predecessor"]
                locate_resp.location_info.successor = location_info["successor"]
                disc_resp.msg_type = discovery_pb2.LOCATE_NEW_NODE
            if success == False or success == True: 
                locate_resp.success = success
                disc_resp.msg_type = discovery_pb2.LOCATE_HASH_TABLE
            if matching_pubs: 
                self.logger.debug(f"DistributedMW::handle_locate_request - matching pubs: {matching_pubs}")
                locate_resp.publishers.extend(matching_pubs)
                disc_resp.msg_type = discovery_pb2.LOCATE_PUB_BY_TOPIC_HASH
            if all_pubs:
                self.logger.debug(f"DistributedMW::handle_locate_request - all pubs: {all_pubs}")
                locate_resp.publishers.extend(all_pubs)
                self.logger.debug(f"DistributedMW::handle_locate_request - locate resp: {locate_resp}")
                disc_resp.msg_type = discovery_pb2.LOCATE_ALL_PUBS
            disc_resp.locate_resp.CopyFrom(locate_resp)
            # send the message
            send_message(self.rep, disc_resp)
        except Exception as e: handle_exception(e)

    """We need to update our neigbor (predecessor or successor) 
    based on the information from the requesting node (our neighbor)"""
    def update_neighbor(self, which_neighbor, new_node):
        try:
            self.logger.debug("DistributedMW::update_neighbor")
            # update our neighbor based on incoming info
            if which_neighbor == "predecessor":
                self.predecessor = new_node
                self.logger.info(f"New predecessor node: {self.format_node_info(self.predecessor)}")
            elif which_neighbor == "successor":
                self.successor = new_node
                self.logger.info(f"New successor node: {self.format_node_info(self.successor)}")
            else: self.logger.error("Unknown neighbor type.")
        except Exception as e: handle_exception(e)

    """register the broker with our node and tell our neighbor to do the same"""
    def register_broker(self, broker, start_node_id):
        try:
            self.logger.debug("DistributedMW::register_broker")
            # update our broker with the incoming broker
            self.broker = broker
            # tell our neighbor to update their broker
            if self.successor.node_id != start_node_id:
                self.talk_to_neighbor(neighbor=self.successor, broker=broker, start_node_id=start_node_id)
        except Exception as e: handle_exception(e)

    """update our reg count and tell our neighbor to do the same"""
    def update_reg_count(self, start_node_id):
        try:
            self.logger.debug("DistributedMW::update_reg_count")
            # increase our reg_count by one
            self.reg_count += 1
            # tell our neighbor to update their reg_count
            print(self.successor)
            if self.successor.node_id != start_node_id:
                self.talk_to_neighbor(neighbor=self.successor, start_node_id=start_node_id)
        except Exception as e: handle_exception(e)

# ======================================== OTHER HELPERS ======================================== #
    """convert the node info into the proper format"""
    def format_node_info(self, node_info):
        self.logger.debug("DistributedMW::format_node_info")        
        try: return f"{node_info.node_id}:{node_info.ip}:{node_info.port}"
        except Exception as e: handle_exception(e)

    """convert the neighbors into the proper format"""
    def format_neighbors(self, predecessor, successor):
        # TODO change the neighbor return so that this is no longer necessary
        try:
            self.logger.debug(f"DistributedMW::format_neighbors")
            split_predecessor = predecessor.split(":")
            split_successor = successor.split(":")
            self.predecessor = discovery_pb2.ID()
            self.successor = discovery_pb2.ID()
            self.predecessor.node_id = int(split_predecessor[0])
            self.predecessor.ip = split_predecessor[1]
            self.predecessor.port = split_predecessor[2]
            self.successor.node_id = int(split_successor[0])
            self.successor.ip = split_successor[1]
            self.successor.port = split_successor[2]
        except Exception as e: handle_exception(e)

    """registers registering apps based on the hash values of their topics"""
    def register_topic_hashes(self, register_req, app_type):
        try:
            self.logger.debug("DistributedMW::register_topic_hashes")
            # iterate through each topic in the register_req topiclist
            for topic in register_req.topiclist:
                topic_hash = hash_func(self.bits_hash, topic)
                self.determine_topic_location(topic_hash, register_req.id, app_type)
            # send commands to successor for them to update their reg_count var
            self.reg_count += 1
            self.talk_to_neighbor(neighbor=self.successor, start_node_id=self.node_id)
        except Exception as e: handle_exception(e)

    """handle a DHT node registration with the discovery service"""
    def handle_dht_register(self, new_node):
        try:
            self.logger.debug("DistributedMW::handle_dht_register")
            # Handle the case where we are the only node we know of
            if self.predecessor == None:
                # They are now our predecessor and successor
                self.predecessor = new_node; self.successor = new_node
                self.logger.info(f"New predecessor node: {self.format_node_info(new_node)}")
                self.logger.info(f"New successor node: {self.format_node_info(new_node)}")
                # We are both their predecessor and successor
                predecessor = f"{self.node_id}:{self.addr}:{self.port}"
                successor = f"{self.node_id}:{self.addr}:{self.port}"
            else:
                # Find out where to fit this node into the ring
                location_info = self.determine_node_location(new_node)
                predecessor = location_info["predecessor"]
                successor = location_info["successor"]
            # Return the predecessor and successor info to the new node
            return {"predecessor": predecessor, "successor": successor}
        except Exception as e: handle_exception(e)

    """responds to a registration request"""
    def respond_to_register(self, dht_info):
        try:
            self.logger.debug("DistributedMW::respond_to_register")
            # build the response message
            disc_resp = discovery_pb2.DiscoveryResp()
            register_resp = discovery_pb2.RegisterResp()
            register_resp.result = register_resp.Result.SUCCESS
            if dht_info:
              self.logger.debug(f"DistributedMW::respond_to_register - dht_info: {dht_info}")
              register_resp.neighbor_nodes.predecessor = dht_info["predecessor"]
              register_resp.neighbor_nodes.successor = dht_info["successor"]
            disc_resp.msg_type = discovery_pb2.REGISTER
            disc_resp.register_resp.CopyFrom(register_resp)
            # send the message
            send_message(self.rep, disc_resp)
        except Exception as e: handle_exception(e)

    """run the event loop where we expect to receive a reply to a sent request"""
    def event_loop(self, neighbor_req=None):
        try:
            self.logger.debug("DistributedMW::event_loop")
            while True:
                self.logger.debug("DistributedMW::event_loop - LISTENING")
                # poll for events. We give it an infinite timeout.
                # The return value is a socket to event mask mapping
                events = dict(self.poller.poll())
                self.logger.debug(f"DistributedMW::event_loop - events: {events}")
                if self.req in events: return self.handle_reply()
                if neighbor_req and neighbor_req in events: 
                    return self.handle_reply(neighbor_req)
        except Exception as e: handle_exception(e)

    """handle an incoming reply to a sent request"""
    def handle_reply(self, neighbor_req=None):
        try:
            self.logger.debug("DistributedMW::handle_reply")
            # let us first receive all the bytes
            if neighbor_req: bytesRcvd = neighbor_req.recv()
            else: bytesRcvd = self.req.recv()
            # now use protobuf to deserialize the bytes
            disc_resp = discovery_pb2.DiscoveryResp()
            disc_resp.ParseFromString(bytesRcvd)
            self.logger.debug(f"DistributedMW::handle_reply - disc_resp: {disc_resp}")
            # Depending on the message type, the contents of the msg will differ
            if disc_resp.msg_type == discovery_pb2.REGISTER:
                if disc_resp.register_resp.result == discovery_pb2.RegisterResp().Result.FAILURE:
                    raise Exception(disc_resp.register_resp.fail_reason) # return register error
                else: return disc_resp.register_resp.neighbor_nodes # return neighbor nodes to DHT node
            elif disc_resp.msg_type == discovery_pb2.LOCATE_NEW_NODE:
                return disc_resp.locate_resp.location_info
            elif disc_resp.msg_type == discovery_pb2.LOCATE_HASH_TABLE:
                return disc_resp.locate_resp.success
            elif disc_resp.msg_type == discovery_pb2.LOCATE_PUB_BY_TOPIC_HASH or \
                disc_resp.msg_type == discovery_pb2.LOCATE_ALL_PUBS:
                return disc_resp.locate_resp.publishers
            else: raise Exception("Unrecognized response message")
        except Exception as e: handle_exception(e)

    """Determine where the new node belongs. Update nodes in the ring in the process."""
    def determine_node_location(self, new_node):
        try:
            self.logger.debug(f"DistributedMW::determine_node_location")
            # If the new_node ID is between our predecessor and us...
            if ((self.predecessor.node_id < new_node.node_id < self.node_id) or
                ((self.predecessor.node_id > self.node_id) and
               (new_node.node_id < self.node_id or new_node.node_id > self.predecessor.node_id))):
                # We tell our old predecessor to set this as their new successor
                self.talk_to_neighbor(neighbor=self.predecessor, new_node=new_node, which_neighbor="successor")
                # Our old predecessor becomes the new nodes predecessor
                predecessor = f"{self.predecessor.node_id}:{self.predecessor.ip}:{self.predecessor.port}"
                # The new node becomes our new predecessor
                self.predecessor = new_node
                self.logger.info(f"New predecessor node: {self.format_node_info(self.predecessor)}")
                # We become the new nodes successor
                successor = f"{self.node_id}:{self.addr}:{self.port}"
            # If the new_node ID is between us and our successor
            elif ((self.node_id < new_node.node_id < self.successor.node_id) or
                  ((self.successor.node_id < self.node_id) and
                   (new_node.node_id > self.node_id or new_node.node_id < self.successor.node_id))):
                # We tell our successor to set this as their new predecessor
                self.talk_to_neighbor(neighbor=self.successor, new_node=new_node, which_neighbor="predecessor")
                # We become the new nodes predecessor
                predecessor = f"{self.node_id}:{self.addr}:{self.port}"
                # The new node becomes our new successor
                self.successor = new_node
                self.logger.info(f"New successor node: {self.format_node_info(self.successor)}")
                # Our old successor becomes the new nodes successor
                successor = f"{self.successor.node_id}:{self.successor.ip}:{self.successor.port}"
            # If the new_node ID is below our predecessor...
            elif new_node.node_id < self.predecessor.node_id:
                # recursively iterate through the ring and return the result once it is found
                location_info = self.talk_to_neighbor(neighbor=self.predecessor, new_node=new_node)
                print(location_info)
                predecessor = location_info.predecessor
                successor = location_info.successor
            # If the new_node is greater than our successor
            else:
                # recursively iterate through the ring and return the result once it is found
                location_info = self.talk_to_neighbor(neighbor=self.successor, new_node=new_node)
                predecessor = location_info.predecessor
                successor = location_info.successor
            return {"predecessor": predecessor, "successor": successor}
        except Exception as e: handle_exception(e)

    """Determine the proper node to store this hashed topic pub/sub in. 
    Then use helper function to push the registering app to the hash_table on that node."""
    def determine_topic_location(self, topic_hash, app_id, app_type):
        try:
            self.logger.debug(f"DistributedMW::determine_topic_location")
            topic_info = discovery_pb2.LocateReq().topic_info
            # If the topic_hash is between our predecessor and us then we store it in our table
            if ((self.predecessor and self.predecessor.node_id < topic_hash < self.node_id) or
                ((self.predecessor.node_id > self.node_id) and
               (topic_hash < self.node_id or topic_hash > self.predecessor.node_id))):
                self.add_to_hash_table(topic_hash, app_id, app_type)
                self.logger.debug(f"DistributedMW::determine_topic_location - stored {app_type}:{app_id.name} in hash table")
                return True
            else:
                topic_info.topic_hash = topic_hash; topic_info.app_type = app_type
                topic_info.app_id.name = app_id.name; topic_info.app_id.ip = app_id.ip
                topic_info.app_id.port = app_id.port
                # If the topic_hash is below our predecessor then pass down
                if topic_hash < self.predecessor.node_id:
                    # recursively iterate through the ring and return the result once it is found
                    result = self.talk_to_neighbor(neighbor=self.predecessor, topic_info=topic_info)
                # If the topic_hash is greater than our successor then pass up
                else:
                    # recursively iterate through the ring and return the result once it is found
                    result = self.talk_to_neighbor(neighbor=self.successor, topic_info=topic_info)
                self.logger.debug(f"DistributedMW::determine_topic_location - success: {result}")
                return result
        except Exception as e: handle_exception(e)

    """adds a registering app to the hash_table on this node"""
    def add_to_hash_table(self, topic_hash, app_id, app_type):
        try:
            self.logger.debug(f"DistributedMW::add_to_hash_table")
            if topic_hash not in self.hash_table:
                self.hash_table[topic_hash] = {}
            if app_type in self.hash_table[topic_hash]:
                self.hash_table[topic_hash][app_type].append(app_id)
            else:
                self.hash_table[topic_hash][app_type] = [app_id]
        except Exception as e: handle_exception(e)

    """get all of the pubs in the ring that publish on any of the given topics"""
    def get_pubs_matching_topics(self, topics):
        try: 
            self.logger.debug("DistributedMW::get_pubs_matching_topics")
            # First, set up the topiclist and matching_pubs variables
            topiclist = list(topics.topiclist); matching_pubs = []
            # Check each sub topic to see if we have a pub for it
            for topic in topiclist:
                topic_hash = hash_func(self.bits_hash, topic)
                matching_pubs.extend(self.get_pubs_matching_topic(topic_hash, self.node_id))
            return matching_pubs
        except Exception as e: handle_exception(e)
    
    """get the pubs that publish on the given topic"""
    def get_pubs_matching_topic(self, topic_hash, start_node_id):
        try: 
            self.logger.debug("DistributedMW::get_pubs_matching_topic")
            if topic_hash in self.hash_table and 'PUB' in self.hash_table[topic_hash]:
                return self.hash_table[topic_hash]['PUB']
            elif start_node_id == self.successor.node_id:
                return []
            elif topic_hash < self.node_id:
                # add to the list of pubs by asking our predecessor
                return self.talk_to_neighbor(neighbor=self.predecessor, topic_hash=topic_hash, start_node_id=start_node_id)
            else:
                # add to the list of pubs by asking our successor
                return self.talk_to_neighbor(neighbor=self.successor, topic_hash=topic_hash, start_node_id=start_node_id)
        except Exception as e: handle_exception(e)

    """get all of the pubs in the DHT ring"""
    def get_all_pubs(self, start_node_id):
        try:
            self.logger.debug("DistributedMW::get_all_pubs")
            # ask successor for all their pubs recursively until reaching starting node
            if self.successor.node_id == start_node_id: return self.get_own_pubs()
            else:
                all_pubs = self.talk_to_neighbor(neighbor=self.successor, start_node_id=start_node_id, all_pubs=True)
                all_pubs.extend(self.get_own_pubs())
                self.logger.debug(f"DistributedMW::get_all_pubs - all pubs: {all_pubs}")
                if self.node_id != start_node_id: return all_pubs
                else: return format_pubs(all_pubs)
        except Exception as e: handle_exception(e)

    """get all of the pubs in our own hash table"""
    def get_own_pubs(self):
        try: 
            self.logger.debug("DistributedMW::get_own_pubs")
            own_pubs = []
            for topic_hash in self.hash_table:
                if 'PUB' in self.hash_table[topic_hash]:
                    own_pubs.extend(self.hash_table[topic_hash]['PUB'])
            self.logger.debug(f"DistributedMW::get_own_pubs - own_pubs: {own_pubs}")
            return own_pubs
        except Exception as e: handle_exception(e)

    """send a message to the given neighbor and wait for a response"""
    def talk_to_neighbor(self, neighbor, new_node=None, which_neighbor=None, broker=None,
                         topic_info=None, topic_hash=None, start_node_id=None, all_pubs=False):
        try:
            self.logger.debug("DistributedMW::talk_to_neighbor")
            # set up the neighbor_req
            context = zmq.Context()  # returns a singleton object
            neighbor_req = context.socket(zmq.REQ)
            connect_str = f"tcp://{neighbor.ip}:{neighbor.port}"
            self.poller.register(neighbor_req, zmq.POLLIN)
            neighbor_req.connect(connect_str)
            # build the request message
            next_id = hash_func(self.bits_hash, f'{neighbor.ip}:{neighbor.port}')
            disc_req = discovery_pb2.DiscoveryReq()
            if which_neighbor or start_node_id and not topic_hash and not all_pubs:
                return self.send_update_request(disc_req, neighbor_req, new_node, which_neighbor, broker, start_node_id, next_id)
            else:
                return self.send_locate_request(disc_req, neighbor_req, new_node, topic_info, topic_hash, start_node_id, all_pubs, next_id)
        except Exception as e: handle_exception(e)

    """send an update message to the given neighbor and wait for a response"""
    def send_update_request(self, disc_req, neighbor_req, new_node, which_neighbor, broker, start_node_id, next_id):
        try:
            self.logger.debug("DistributedMW::send_update_request")
            update_req = discovery_pb2.UpdateReq()
            if which_neighbor: update_req.which_neighbor = which_neighbor
            if start_node_id: 
                write_vis_command('Visualization/commands.txt', 'request', self.node_id, next_id, 'update is_ready') 
                update_req.start_node_id = start_node_id
            if broker: 
                update_req.new_node.name = broker.name
                update_req.new_node.ip = broker.ip
                update_req.new_node.port = broker.port
            elif new_node:
                write_vis_command('Visualization/commands.txt', 'request', self.node_id, next_id, 'update neighbor') 
                update_req.new_node.node_id = new_node.node_id
                update_req.new_node.ip = new_node.ip
                update_req.new_node.port = new_node.port
            disc_req.msg_type = discovery_pb2.UPDATE_NODE
            disc_req.update_req.CopyFrom(update_req)
            # send the message
            send_message(neighbor_req, disc_req)
            # get response to clear the socket but we don't care about it right now
            self.event_loop(neighbor_req)
            return True
        except Exception as e: handle_exception(e)

    """send a locate message to the given neighbor and wait for a response"""
    def send_locate_request(self, disc_req, neighbor_req, new_node, topic_info, topic_hash, start_node_id, all_pubs, next_id):
        try:
            self.logger.debug("DistributedMW::send_locate_request")
            locate_req = discovery_pb2.LocateReq()
            if start_node_id: locate_req.start_node_id = start_node_id
            if new_node:
                locate_req.new_node.node_id = new_node.node_id
                locate_req.new_node.ip = new_node.ip
                locate_req.new_node.port = new_node.port
            if topic_info:
                locate_req.topic_info.topic_hash = topic_info.topic_hash
                locate_req.topic_info.app_type = topic_info.app_type
                locate_req.topic_info.app_id.name = topic_info.app_id.name
                locate_req.topic_info.app_id.ip = topic_info.app_id.ip
                locate_req.topic_info.app_id.port = topic_info.app_id.port
                disc_req.msg_type = discovery_pb2.LOCATE_HASH_TABLE
            elif topic_hash:
                write_vis_command('Visualization/commands.txt', 'request', self.node_id, next_id, 'locate publisher') 
                locate_req.topic_info.topic_hash = topic_hash
                disc_req.msg_type = discovery_pb2.LOCATE_PUB_BY_TOPIC_HASH
            elif all_pubs: disc_req.msg_type = discovery_pb2.LOCATE_ALL_PUBS
            else: 
                write_vis_command('Visualization/commands.txt', 'request', self.node_id, next_id, 'locate new node') 
                disc_req.msg_type = discovery_pb2.LOCATE_NEW_NODE
            disc_req.locate_req.CopyFrom(locate_req)
            # send the message
            send_message(neighbor_req, disc_req)
            # get response
            return self.event_loop(neighbor_req)
        except Exception as e: handle_exception(e)
