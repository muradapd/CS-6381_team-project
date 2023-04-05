###############################################
# Author: Aniruddha Gokhale
# Updated by: Patrick Muradaz
# Vanderbilt University
# Purpose: Python file for common functions
# Semester: Spring 2023
###############################################
# 
# This file contains any declarations that are common to all middleware entities
#
# import statements
import json, hashlib
from Apps.Common import discovery_pb2

"""handle the given exception"""
def handle_exception(e):
    exc_traceback = e.__traceback__
    raise e.with_traceback(exc_traceback)

"""dump the contents of the object"""
def dump(logger, app, ip, port, name=None, iters=None,
         topiclist=None, numpubs=None, numsubs=None):
  try:
    logger.debug("**********************************")
    logger.debug(f"     {app}::dump")
    logger.debug("------------------------------")
    if name: logger.debug(f"     Name: {name}")
    logger.debug(f"     IP: {ip}")
    logger.debug(f"     Port: {port}")
    if topiclist: 
      logger.debug(f"     TopicList: {topiclist}")
      logger.info(f"App: {name} - {ip}:{port}; Topiclist: {topiclist}")
    if iters: logger.debug(f"     Iterations: {iters}")
    if numpubs: logger.debug(f"     Pubs Expected: {numpubs}")
    if numsubs: logger.debug(f"     Subs Expected: {numsubs}")
    logger.debug("**********************************")
  except Exception as e: handle_exception(e)

"""format and return the given array of publishers"""
def format_pubs(pubs):
    try:
      formatted_pubs = []; pub_names = []
      for pub in pubs:
          try: publisher = {"name": pub.id.name, "ip": pub.id.ip, "port": pub.id.port}
          except: publisher = {"name": pub.name, "ip": pub.ip, "port": pub.port}
          if publisher["name"] not in pub_names:
              formatted_pubs.append(json.dumps(publisher))
              pub_names.append(publisher["name"])
      return formatted_pubs
    except Exception as e: handle_exception(e)

"""send the given message on the given socket"""
def send_message(socket, message):
    try:
      buf2send = message.SerializeToString()
      socket.send(buf2send)
    except Exception as e: handle_exception(e)

"""register with the discovery service"""
def register(logger, role, name, addr, port, req, topiclist=None):
  try:
    logger.debug("Common::register")
    # build the request message
    disc_req = discovery_pb2.DiscoveryReq()
    register_req = discovery_pb2.RegisterReq() 
    register_req.role = role
    if topiclist: register_req.topiclist.extend(topiclist)
    register_req.id.name = name
    register_req.id.ip = addr
    register_req.id.port = port
    disc_req.msg_type = discovery_pb2.REGISTER
    disc_req.register_req.CopyFrom(register_req)
    # send the message
    send_message(req, disc_req)
  except Exception as e: handle_exception(e)

"""check if the discovery service gives the green light to proceed"""
def is_ready(logger, req):
  try:
    logger.debug("Common::is_ready")
    # build the request message
    disc_req = discovery_pb2.DiscoveryReq()
    isready_msg = discovery_pb2.IsReadyReq()
    disc_req.msg_type = discovery_pb2.ISREADY
    disc_req.is_ready.CopyFrom(isready_msg)
    # send the message
    send_message(req, disc_req)
  except Exception as e: handle_exception(e)

"""disseminate the data on our pub socket"""
def disseminate(logger, pub, data):
    logger.debug(f"Common::disseminate - {data}")
    try: pub.send_string(data)
    except Exception as e: handle_exception(e)

"""get the hash for a value"""
def hash_func(bits_hash, value):
    try:
        # first get the digest from hashlib and then take the desired number of bytes from the
        # lower end of the 256 bits hash. Big or little endian does not matter.
        # this is how we get the digest or hash value
        hash_digest = hashlib.sha256(bytes(value, "utf-8")).digest()
        # figure out how many bytes to retrieve
        # otherwise we get float which we cannot use below
        num_bytes = int(bits_hash/8)
        # take lower N number of bytes
        hash_val = int.from_bytes(hash_digest[:num_bytes], "big")
        return hash_val
    except Exception as e: handle_exception(e)
