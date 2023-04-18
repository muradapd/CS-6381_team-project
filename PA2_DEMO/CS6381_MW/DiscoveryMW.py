# import the needed packages
import zmq
import time

# import serialization logic
from CS6381_MW import discovery_pb2
from DHT_logic.DHT_vis_util import write_vis_command

class DiscoveryMW ():
    def __init__(self, logger, discovery, dht_peers=None, hash=None):
        self.logger = logger  # internal logger for print statements
        self.rep = None  # will be a ZMQ REP socket to talk to subscribers and publishers
        self.req = {}  # Will be used if we are using the DHT approach
        self.poller = None  # used to wait on incoming replies
        self.port = None  # port num where we are going to look for topics?
        self.discovery = discovery
        self.hash = hash
        self.dht_peers = dht_peers

    def configure(self, args):
        ''' Initialize the object '''
        try:
            # First retrieve our advertised IP addr and the publication port num
            self.port = args.port

            # Next get the ZMQ context
            context = zmq.Context()  # returns a singleton object
            self.poller = zmq.Poller()
            self.rep = context.socket(zmq.ROUTER)

            # register the REP socket for incoming events
            self.poller.register(self.rep, zmq.POLLIN)

            connect_str = f'tcp://*:{self.port}'
            self.rep.bind(connect_str)

            if self.discovery == 'DHT':
                # Set up list of request connections to all other DHT instances
                for id, addr in self.dht_peers.items():
                    print(id, addr)
                    # socket = context.socket(zmq.REQ) # Changing to dealer router
                    socket = context.socket(zmq.DEALER)
                    socket.setsockopt_string(zmq.IDENTITY, str(self.hash))
                    connect_str = "tcp://" + addr
                    socket.connect(connect_str)

                    self.poller.register(socket, zmq.POLLIN)
                    self.req[id] = socket

        except Exception as e:
            raise e


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

                for id, socket in self.req.items():
                    if socket in events:
                        self.logger.info(f'DiscoveryMW - Received an event from {id}')
                        return self.handle_reply(socket)

        except Exception as e:
            raise e

    def register(self, next_name, name, addr, port, role, topiclist, successor, chain):
        ''' register the appln with the discovery service '''

        try:
            self.logger.info(f"DiscoveryMW - Sending register request to next DHT node {next_name} for topic {topiclist}")

            write_vis_command('PA2_DEMO/commands.txt', 'request', name, next_name, 'register')

            # first build a register req message
            register_req = discovery_pb2.RegisterReq()  # allocate
            register_req.role = role  # this will change to an enum later on
            register_req.topiclist = topiclist  # should just be one topic
            register_req.address = addr
            register_req.port = port
            register_req.id = name

            if chain:
                register_req.chain = ','.join(chain)

            if successor:
                # self.logger.info('DiscoveryMW - Successor is true! Next node has the value so we are sending register req there')
                register_req.successor = "True"

            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.msg_type = discovery_pb2.REGISTER
            disc_req.register_req.CopyFrom(register_req)

            buf2send = disc_req.SerializeToString()

            # we use the "send" method of ZMQ that sends the bytes
            self.req.get(next_name, 0).send_multipart([buf2send])

            self.logger.info(f"DiscoveryMW - Sent register request to next DHT node: {next_name}")

        except Exception as e:
            raise e

    def send_is_ready_check(self, next_name, num_pubs, num_subs, broker, initiator, chain, name):

        try:
            # first build a IsReady message
            isready_msg = discovery_pb2.IsReadyReq()  # allocate

            isready_msg.num_pubs = str(num_pubs)
            isready_msg.num_subs = str(num_subs)
            isready_msg.broker = str(broker)
            isready_msg.initiator = initiator

            isready_msg.chain = ','.join(chain)
            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.msg_type = discovery_pb2.ISREADY

            # It was observed that we cannot directly assign the nested field here.
            # A way around is to use the CopyFrom method as shown
            disc_req.is_ready.CopyFrom(isready_msg)

            # now let us stringify the buffer and print it. This is actually a sequence of bytes and not
            # a real string
            buf2send = disc_req.SerializeToString()

            write_vis_command('PA2_DEMO/commands.txt', 'request', name, next_name, 'is_ready')

            self.req.get(next_name, 0).send_multipart([buf2send])

            self.logger.info(f"DiscoveryMW - Sent is_ready request to next DHT node: {next_name}")

        except Exception as e:
            raise e

    #################################################################
    # handle an incoming reply
    #################################################################

    def handle_reply(self, socket=None):

        try:
            message = None
            identity = None

            # let us first receive all the bytes
            bytesRcvd = None
            if socket:
                bytesRcvd = socket.recv_multipart()
                message = bytesRcvd[-1]
                identity = bytesRcvd[0]

                # now use protobuf to deserialize the bytes
                disc_resp = discovery_pb2.DiscoveryResp()
                disc_resp.ParseFromString(message)

                if (disc_resp.msg_type == discovery_pb2.REGISTER):

                    # Another DHT node sent us a register reply
                    resp_obj = {
                        'register_result': disc_resp.register_resp.result,
                        'request_type': 'register_resp',
                        'chain': disc_resp.register_resp.chain.split(',')
                    }
                    return resp_obj
                
                elif (disc_resp.msg_type == discovery_pb2.ISREADY):

                    # Another DHT node sent an is_ready reply
                    self.logger.info(f"DiscoveryMW - Received a socket reply of type is_ready: {disc_resp}")
                    resp_obj = {
                        'request_type': 'is_ready_resp',
                        'is_ready_result': disc_resp.is_ready.reply,
                        'chain': disc_resp.is_ready.chain.split(',')
                    }
                    return resp_obj
                
                elif (disc_resp.msg_type == discovery_pb2.LOOKUP_PUB_BY_TOPIC):
                    self.logger.info(f'DiscoveryMW::handle_reply - received a lookup response: {disc_resp}')

                    return {
                        'request_type': 'lookup_resp',
                        'pub_addresses': list(disc_resp.resp.pub_addresses.split(',')),
                        'chain': disc_resp.resp.chain.split(',')
                    }

                elif (disc_resp.msg_type == discovery_pb2.LOOKUP_ALL_PUBS):
                    self.logger.info(f'DiscoveryMW::handle_reply - received a lookup response: {disc_resp}')

                    return {
                        'identity': identity,
                        'request_type': 'lookup_resp',
                        'pub_addresses': list(disc_resp.all_pubs.pub_addresses.split(',')),
                        'chain': disc_resp.all_pubs.chain.split(',')
                    }
                else:  # anything else is unrecognizable by this object
                    # raise an exception here
                    raise Exception("Unrecognized response message")

            else:
                bytesRcvd = self.rep.recv_multipart()
                message = bytesRcvd[-1]
                identity = bytesRcvd[0]

                self.logger.info(f'RECVD NEW REQUEST FROM PUB/SUB: {bytesRcvd}')

            # now use protobuf to deserialize the bytes
            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.ParseFromString(message)

            if (disc_req.msg_type == discovery_pb2.REGISTER):
                # this is a request to register

                # create new object for our application to ingest
                register_req = {
                    'request_type': 'register',
                    'role': disc_req.register_req.role,
                    'topic_list': list(disc_req.register_req.topiclist.split(',')),
                    'id': disc_req.register_req.id,
                    'address': disc_req.register_req.address,
                    'port': disc_req.register_req.port,
                    'successor': disc_req.register_req.successor,
                    'identity': identity,
                    'chain': disc_req.register_req.chain.split(',')
                }
                return register_req

            elif (disc_req.msg_type == discovery_pb2.ISREADY):

                is_ready_req = {
                    'request_type': 'is_ready',
                    'num_pubs': int(disc_req.is_ready.num_pubs or 0),
                    'num_subs': int(disc_req.is_ready.num_subs or 0),
                    'broker': int(disc_req.is_ready.broker or 0),
                    'initiator': disc_req.is_ready.initiator,
                    'identity': identity,
                    'chain': disc_req.is_ready.chain.split(',')
                }
                self.logger.info(f'DiscoveryMW - received an is_ready request: {is_ready_req}')

                # this is a ready request
                return is_ready_req

            elif (disc_req.msg_type == discovery_pb2.LOOKUP_PUB_BY_TOPIC):
                self.logger.info(f'DiscoveryMW - received a lookup request: {disc_req.topic}')

                successor = False
                if disc_req.topic.successor == 'True':
                    successor = True

                return {
                    'request_type': 'lookup',
                    'successor': successor,
                    'topicList': list(disc_req.topic.topiclist.split(',')),
                    'identity': identity,
                    'chain': disc_req.topic.chain.split(',')
                }

            elif (disc_req.msg_type == discovery_pb2.LOOKUP_ALL_PUBS):

                self.logger.info(f'DiscoveryMW - received a lookup request for all pubs from initiator {disc_req.all_pubs.initiator}')

                return {
                    'request_type': 'lookup_all_pubs',
                    'pubs': list(disc_req.all_pubs.pub_addresses.split(',')),
                    'initiator': disc_req.all_pubs.initiator,
                    'identity': identity,
                    'chain': disc_req.all_pubs.chain.split(',')
                }

            elif (disc_req.msg_type == discovery_pb2.EXIT):
                # this is a notification of exit

                # create new object for our application to ingest
                exit_req = {
                    'request_type': 'exit',
                    'role': disc_req.exit.role,
                    'id': disc_req.exit.id,
                    'address': disc_req.exit.address,
                }
                return exit_req

            else:  # anything else is unrecognizable by this object
                # raise an exception here
                raise Exception("Unrecognized response message")

        except Exception as e:
            raise e

    #################################################################
    # respond to a registration request
    #################################################################
    def verify_registration(self, identity, success, chain=None):

        try:
            target = identity
            if chain:
                target = chain.pop()
                target = bytes.fromhex(target)

            self.logger.info(f'DiscoveryMW: Verifying registration sending back to {target}')
            self.logger.info(f'New chain after that was removed: {chain}')

           # If successfully verified, let them know otherwise let them down easy

            # first build a RegisterResp for the inner layer
            register_rep = discovery_pb2.RegisterResp()  # allocate
            
            if chain:
                register_rep.chain = ','.join(chain)

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
    # respond to an is_ready check
    #################################################################
    def is_ready(self, identity, success, chain=None):

        try:

            target = identity

            self.logger.info("DiscoveryMW - is_ready response beginning")

           # If the system has all connected pubs and subs let them know

            # first build a RegisterResp for the inner layer
            is_ready_rep = discovery_pb2.IsReadyResp()  # allocate

            self.logger.info(f"DiscoveryMW - result of ready check: {success}")

            is_ready_rep.reply = success
            if chain:
                self.logger.info(f'Current Chain: {chain}')
                target = chain.pop()
                target = bytes.fromhex(target)
                self.logger.info(f'Popped next target: {target}, new chain {chain}')
                is_ready_rep.chain = ','.join(chain)

            # Build the outer layer Discovery Message
            disc_rep = discovery_pb2.DiscoveryResp()
            disc_rep.msg_type = discovery_pb2.ISREADY
            disc_rep.is_ready.CopyFrom(is_ready_rep)
            buf2send = disc_rep.SerializeToString()

            # we use the "send" method of ZMQ that sends the bytes
            self.rep.send_multipart([target, b'', buf2send])

        except Exception as e:
            raise e

    ########################################
    # lookup publishers that match our list of topics so we can connect
    ########################################
    def lookup_request(self, next_name, topic, successor, chain, name):
        ''' lookup a list of publishers with the topics we are interested in '''

        try:

            self.logger.info(
                f"DiscoveryMW: Sending lookup request, successor: {successor}")


            # first build a Lookup message
            lookup_msg = discovery_pb2.LookupPubByTopicReq()  # allocate
            lookup_msg.topiclist = topic
            lookup_msg.successor = str(successor)
            lookup_msg.chain = ','.join(chain)

            self.logger.info(
                f"DiscoveryMW: Sending lookup request, successor: {lookup_msg.successor}")

            # Build the outer layer Discovery Message
            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.msg_type = discovery_pb2.LOOKUP_PUB_BY_TOPIC
            disc_req.topic.CopyFrom(lookup_msg)
            buf2send = disc_req.SerializeToString()

            # now send this to our discovery service
            # we use the "send" method of ZMQ that sends the bytes
            write_vis_command('PA2_DEMO/commands.txt', 'request', name, next_name, 'lookup')
            self.req.get(next_name, 0).send_multipart([buf2send])
            

            self.logger.info(
                f"DiscoveryMW - Sent lookup request for topic '{topic}' to next DHT node: {next_name}")
            self.logger.info(
                f"DiscoveryMW - Waiting for lookup reply from {next_name}")

        except Exception as e:
            raise e

    def lookup_all_pubs(self, next_name, pub_list, initiator, chain):
        ''' go around the ring getting all publishers '''

        try:
            lookup_msg = discovery_pb2.LookupAllPubsReq()  # allocate
            lookup_msg.pub_addresses = ",".join(pub_list)
            lookup_msg.initiator = initiator

            if chain:
                lookup_msg.chain = ','.join(chain)

            disc_req = discovery_pb2.DiscoveryReq()
            disc_req.msg_type = discovery_pb2.LOOKUP_ALL_PUBS
            disc_req.all_pubs.CopyFrom(lookup_msg)

            # now let us stringify the buffer and print it. This is actually a sequence of bytes and not
            # a real string
            buf2send = disc_req.SerializeToString()

            # now send this to our discovery service
            self.req.get(next_name, 0).send_multipart([buf2send])

            self.logger.info(
                f"DiscoveryMW - Sent lookup request for all pubs to next DHT node: {next_name}")
            self.logger.info(
                f"DiscoveryMW - Waiting for lookup reply from {next_name}")

        except Exception as e:
            raise e

    #################################################################
    # respond to a lookup request
    #################################################################

    def lookup_response(self, identity, pubs_to_send, chain=None, all=False):

        try:
            
            target = identity
            lookup_rep = None
            if not all:
                lookup_rep = discovery_pb2.LookupPubByTopicResp()  # allocate
            else:
                lookup_rep = discovery_pb2.LookupAllPubsResp()  # allocate

            lookup_rep.pub_addresses = ",".join(pubs_to_send)

            if chain:
                target = chain.pop()
                target = bytes.fromhex(target)
                lookup_rep.chain = ','.join(chain)

            # Build the outer layer Discovery Message
            disc_rep = discovery_pb2.DiscoveryResp()

            if not all:
                disc_rep.msg_type = discovery_pb2.LOOKUP_PUB_BY_TOPIC
                disc_rep.resp.CopyFrom(lookup_rep)
            else:
                disc_rep.msg_type = discovery_pb2.LOOKUP_ALL_PUBS
                disc_rep.all_pubs.CopyFrom(lookup_rep)

            buf2send = disc_rep.SerializeToString()

            # now send this to the requestor
            # we use the "send" method of ZMQ that sends the bytes
            self.rep.send_multipart([target, b'',buf2send])

        except Exception as e:
            raise e
