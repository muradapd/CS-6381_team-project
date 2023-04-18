###############################################
#
# Author: Aniruddha Gokhale
# Vanderbilt University
#
# Purpose: Skeleton/Starter code for the broker middleware code
#
# Created: Spring 2023
#
###############################################

# Designing the logic is left as an exercise for the student. Please see the
# PublisherMW.py file as to how the middleware side of things are constructed
# and accordingly design things for the broker side of things.
#
# As mentioned earlier, a broker serves as a proxy and hence has both
# publisher and subscriber roles. So in addition to the REQ socket to talk to the
# Discovery service, it will have both PUB and SUB sockets as it must work on
# behalf of the real publishers and subscribers. So this will have the logic of
# both publisher and subscriber middleware.

# import the needed packages
import os     # for OS functions
import sys    # for syspath and system exception
import time   # for sleep
import argparse  # for argument parsing
import configparser  # for configuration parsing
import logging  # for logging. Use it in place of print statements.
import zmq  # ZMQ sockets

from datetime import datetime

# import serialization logic
from CS6381_MW import discovery_pb2
from CS6381_MW import topic_pb2

# import any other packages you need.

##################################
#       Broker Middleware class
##################################


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

	########################################
	# configure/initialize
	########################################
	def configure(self, args):
		''' Initialize the object '''

		try:
			# Here we initialize any internal variables
			self.logger.debug("BrokerMW::configure")

			# First retrieve our advertised IP addr and the publication port num
			self.port = args.port
			self.addr = args.addr

			# Next get the ZMQ context
			self.logger.debug("BrokerMW::configure - obtain ZMQ context")
			context = zmq.Context()  # returns a singleton object

			# get the ZMQ poller object
			self.logger.debug("BrokerMW::configure - obtain the poller")
			self.poller = zmq.Poller()

			# Now acquire the REQ and PUB sockets
			self.logger.debug(
				"BrokerMW::configure - obtain REQ and PUB sockets")
			self.req = context.socket(zmq.REQ)
			self.pub = context.socket(zmq.PUB)
			self.sub = context.socket(zmq.SUB)

			# Subscribe to all topics
			self.sub.subscribe("")

			# register the REQ socket for incoming events
			self.logger.debug(
				"BrokerMW::configure - register the REQ socket for incoming replies")
			self.poller.register(self.req, zmq.POLLIN)

			# Now connect ourselves to the discovery service. Recall that the IP/port were
			# supplied in our argument parsing.
			self.logger.debug(
				"BrokerMW::configure - connect to Discovery service")
			# For these assignments we use TCP. The connect string is made up of
			# tcp:// followed by IP addr:port number.
			connect_str = "tcp://" + args.discovery
			self.req.connect(connect_str)

			# Since we are the broker, the best practice as suggested in ZMQ is for us to
			# "bind" to the PUB socket
			self.logger.debug(
				"BrokerMW::configure - bind to the pub socket")
			# note that we publish on any interface hence the * followed by port number.
			# We always use TCP as the transport mechanism (at least for these assignments)
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
			self.logger.debug("BrokerMW::register")

			# as part of registration with the discovery service, we send
			# what role we are playing, the list of topics we are publishing,
			# and our whereabouts, e.g., name, IP and port

			# Recall that the current defns of the messages in discovery.proto file
			# are treating everything as string. But you are required to change those.
			# So in this code, I am showing the serialization based on existing defns.
			# This will change once you make changes in the proto file.

			# The following code shows serialization using the protobuf generated code.

			# first build a register req message
			self.logger.debug(
				"BrokerMW::register - populate the nested register req")
			register_req = discovery_pb2.RegisterReq()  # allocate
			register_req.role = "broker"  # this will change to an enum later on

			# TODO: Get actual ip address info (not from cmd line)
			# Send ip address and port information to discovery service
			register_req.address = self.addr
			register_req.port = self.port

			unique_id = name + ":" + self.addr + ":" + self.port
			register_req.id = unique_id  # fill up the ID
			self.logger.debug(
				"BrokerMW::register - done populating nested RegisterReq")

			# Build the outer layer Discovery Message
			self.logger.debug(
				"BrokerMW::register - build the outer DiscoveryReq message")
			disc_req = discovery_pb2.DiscoveryReq()
			disc_req.msg_type = discovery_pb2.REGISTER
			# It was observed that we cannot directly assign the nested field here.
			# A way around is to use the CopyFrom method as shown
			disc_req.register_req.CopyFrom(register_req)
			self.logger.debug(
				"BrokerMW::register - done building the outer message")

			# now let us stringify the buffer and print it. This is actually a sequence of bytes and not
			# a real string
			buf2send = disc_req.SerializeToString()
			self.logger.debug(
				"Stringified serialized buf = {}".format(buf2send))

			# now send this to our discovery service
			self.logger.debug(
				"BrokerMW::register - send stringified buffer to Discovery service")
			# we use the "send" method of ZMQ that sends the bytes
			self.req.send(buf2send)

			# now go to our event loop to receive a response to this request
			self.logger.debug("BrokerMW::register - now wait for reply")
			return self.event_loop()

		except Exception as e:
			raise e

	########################################
	# check if the discovery service gives us a green signal to proceed
	########################################
	def is_ready(self):
		''' register the appln with the discovery service '''

		try:
			self.logger.debug("BrokerMW::is_ready")

			# we do a similar kind of serialization as we did in the register
			# message but much simpler, and then send the request to
			# the discovery service

			# The following code shows serialization using the protobuf generated code.

			# first build a IsReady message
			self.logger.debug(
				"BrokerMW::is_ready - populate the nested IsReady msg")
			isready_msg = discovery_pb2.IsReadyReq()  # allocate
			# actually, there is nothing inside that msg declaration.
			self.logger.debug(
				"BrokerMW::is_ready - done populating nested IsReady msg")

			# Build the outer layer Discovery Message
			self.logger.debug(
				"BrokerMW::is_ready - build the outer DiscoveryReq message")
			disc_req = discovery_pb2.DiscoveryReq()
			disc_req.msg_type = discovery_pb2.ISREADY
			# It was observed that we cannot directly assign the nested field here.
			# A way around is to use the CopyFrom method as shown
			disc_req.is_ready.CopyFrom(isready_msg)
			self.logger.debug(
				"BrokerMW::is_ready - done building the outer message")

			# now let us stringify the buffer and print it. This is actually a sequence of bytes and not
			# a real string
			buf2send = disc_req.SerializeToString()
			self.logger.debug(
				"Stringified serialized buf = {}".format(buf2send))

			# now send this to our discovery service
			self.logger.debug(
				"BrokerMW::is_ready - send stringified buffer to Discovery service")
			# we use the "send" method of ZMQ that sends the bytes
			self.req.send(buf2send)

			# now go to our event loop to receive a response to this request
			self.logger.debug("BrokerMW::is_ready - now wait for reply")
			return self.event_loop()

		except Exception as e:
			raise e

	########################################
	# lookup publishers that match our list of topics so we can connect
	########################################
	def lookup_all_pubs(self):
		''' lookup a list of all publishers so we can connect to get their info '''

		try:
			self.logger.debug("BrokerMW::lookup all pubs")

			# we do a similar kind of serialization as we did in the register
			# message but much simpler, and then send the request to
			# the discovery service

			# first build a Lookup message
			self.logger.debug(
				"BrokerMW::lookup - populate the nested LookupAllPubsReq msg")
			lookup_msg = discovery_pb2.LookupAllPubsReq()  # allocate

			self.logger.debug(
				"BrokerMW::lookup - done populating nested LookupAllPubsReq msg")

			# Build the outer layer Discovery Message
			self.logger.debug(
				"BrokerMW::lookup - build the outer discovery message")
			disc_req = discovery_pb2.DiscoveryReq()
			disc_req.msg_type = discovery_pb2.LOOKUP_ALL_PUBS
			# It was observed that we cannot directly assign the nested field here.
			# A way around is to use the CopyFrom method as shown
			disc_req.all_pubs.CopyFrom(lookup_msg)
			self.logger.debug(
				"BrokerMW::lookup - done building the outer message")

			# now let us stringify the buffer and print it. This is actually a sequence of bytes and not
			# a real string
			buf2send = disc_req.SerializeToString()
			self.logger.debug(
				"Stringified serialized buf = {}".format(buf2send))

			# now send this to our discovery service
			self.logger.debug(
				"BrokerMW::lookup - send stringified buffer to Discovery service")
			# we use the "send" method of ZMQ that sends the bytes
			self.req.send(buf2send)

			# now go to our event loop to receive a response to this request
			self.logger.debug(
				"BrokerMW::lookup - now wait for list of publishers")
			return self.event_loop()

		except Exception as e:
			raise e

	#################################################################
	# run the event loop where we expect to receive a reply to a sent request
	#################################################################
	def event_loop(self):

		try:
			self.logger.debug("BrokerMW::event_loop - run the event loop")

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

			# depending on the message type, the remaining
			# contents of the msg will differ

			# TO-DO
			# When your proto file is modified, some of this here
			# will get modified.
			if (disc_resp.msg_type == discovery_pb2.REGISTER):
				# this is a response to register message
				return disc_resp.register_resp.result
			elif (disc_resp.msg_type == discovery_pb2.ISREADY):
				# this is a response to is ready request
				return disc_resp.is_ready.reply
			elif (disc_resp.msg_type == discovery_pb2.LOOKUP_ALL_PUBS):
				return list(disc_resp.all_pubs.pub_addresses.split(','))
			elif (disc_resp.msg_type == discovery_pb2.LOOKUP_PUB_BY_TOPIC):
				return list(disc_resp.resp.pub_addresses.split(','))
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
			self.logger.debug(f"BrokerMW::disseminate - {topic} {content.content}")

			# self.pub.send_string(data)
			# Build the outer layer Discovery Message
			self.logger.debug(
				"BrokerMW::disseminate - build the topic message")
			topic_msg = topic_pb2.topicMessage()
			topic_msg.topic = topic
			topic_msg.content = content.content
			topic_msg.timestamp = content.timestamp

			# now let us stringify the buffer and print it. This is actually a sequence of bytes and not
			# a real string
			buf2send = topic_msg.SerializeToString()
			self.logger.debug(
				"Stringified serialized buf = {}".format(buf2send))
			self.logger.debug(
				"BrokerMW::disseminate - publish our serialized message")

			# we use the "send" method of ZMQ that sends the bytes
			self.pub.send_multipart([topic, buf2send])

		except Exception as e:
			raise e

	#################################################################
	# handle an incoming message from a pub
	#################################################################
	def handle_message (self):
		try:
			self.logger.debug ("BrokerMW::handle_message")

			# let us first receive all the bytes
			mp_message = self.sub.recv_multipart ()

			topic = mp_message[0]
			bytesRcvd = mp_message[1]

			# now use protobuf to deserialize the bytes
			message = topic_pb2.topicMessage()
			message.ParseFromString (bytesRcvd)

			print(f'Received a message from publisher: {message.timestamp} {message.topic}')

			latency = datetime.now() - datetime.strptime(message.timestamp, "%m/%d/%Y, %H:%M:%S.%f")
			print(f'LATENCY WAS: {latency}')
			print(f'CONTENT WAS: {message.content}')

			return [topic, message]

		except Exception as e:
			raise e