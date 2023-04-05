###############################################
# Author: Aniruddha Gokhale
# Updated by: Patrick Muradaz
# Vanderbilt University
# Purpose: Discovery application for PAs
# Semester: Spring 2023
###############################################
# The Discovery service is a server and hence only responds to requests. 
# It should be able to handle the register, is_ready, the different 
# variants of the lookup methods. etc.
#
# The key steps for the discovery application are
# (1) parse command line and configure application level parameters. One
#     of the parameters should be the total number of publishers and 
#     subscribers in the system.
# (2) obtain the discovery middleware object and configure it.
# (3) since we are a server, we always handle events in an infinite event loop.
#     See publisher code to see how the event loop is written. Accordingly, 
#     when a message arrives, the middleware object parses the message and 
#     determines what method was invoked and then hands it to the application 
#     logic to handle it
# (4) Some data structure or in-memory database etc will need to be used to 
#     save the registrations.
# (5) When all the publishers and subscribers in the system have registered 
#     with us, then we are in a ready state and will respond with a true to 
#     is_ready method. Until then it will be false.
#
# Import statements
import sys, os, argparse, logging
sys.path.append(os.getcwd())
from Apps.Common.common import handle_exception, dump
from Apps.Discovery.mw_orchestrator import MWOrchestrator

"""DiscoveryAppln class"""
class DiscoveryAppln():

  """constructor"""
  def __init__(self, logger):
    self.logger = logger      # internal logger for print statements
    self.discovery = None     # tells if we are using centralized discovery or DHT
    self.bits_hash = None     # the number of bits that we use when hashing
    self.node_id = None       # the actual ID of this node in the DHT ring
    self.addr = None          # our advertised IP address
    self.port = None          # port num where we listen for pubs/subs
    self.numpubs = None       # number of publishers to expect in the system
    self.numsubs = None       # number of subscribers to expect in the system
    self.pubs = []            # the array of publishers that are registering
    self.subs = []            # the array of subscribers that are registering
    self.hash_table = {}      # the hash table that is used in DHT mode
    self.mw_obj = None        # handle to the underlying Middleware object

  """configure/initialize"""
  def configure(self, args):
    try:
      self.logger.debug("DiscoveryAppln::configure")
      # Here we initialize internal variables
      self.bits_hash = 48 # all DHT nodes need to have the same bit value
      self.numpubs = int(args.numpubs) # number of publishers
      self.numsubs = int(args.numsubs) # number of subscribers
      self.port = args.port
      self.addr = args.addr
      # setup up middleware object
      self.mw_obj = MWOrchestrator(self.logger)
      self.discovery = self.mw_obj.configure(args)
      self.logger.info("Discovery app configured.")
      dump(self.logger, "DiscoveryAppln", self.addr, 
           self.port, numpubs=self.numpubs, numsubs=self.numsubs)
    except Exception as e: handle_exception(e)

  """driver program"""
  def driver(self):
    try:
      self.logger.debug("DiscoveryAppln::driver")

      # First, decide if we are using the distributed config
      if self.discovery == "Distributed":
        # Then, ask our middleware to contact the known DHT node to register
        self.logger.info("Registering with DHT ring...")
        result = self.mw_obj.register_dht(self.bits_hash)
        self.node_id = int(result['node_id'])
        self.logger.info(f"Registered with DHT ring! Our node ID: {self.node_id}")
        try: 
          self.logger.info(f"Our predecessor node: {result['predecessor']}")
          self.logger.info(f"Our successor node: {result['successor']}")
        except: self.logger.info("We are the fist node in the ring!")

      # Ask our middleware to listen for publishers and subscribers
      self.logger.info("Listening for registration requests...")
      self.mw_obj.listen(self.hash_table, self.pubs, self.subs, self.numpubs, self.numsubs, self.node_id)
    except Exception as e: handle_exception(e)
    
"""Parse command line arguments"""
def parseCmdLineArgs():
  # instantiate a ArgumentParser object
  parser = argparse.ArgumentParser(description="Discovery Application")
  # Now specify all the optional arguments we support  
  parser.add_argument(
    "-np", "--numpubs", default="1", 
    help="The number of publishers in the system. Default is 3."
  )
  parser.add_argument(
    "-ns", "--numsubs", default="1", 
    help="The number of subscribers in the system. Default is 3."
  )
  parser.add_argument(
    "-a", "--addr", default="localhost", 
    help="IP addr of this discovery app to advertise (default: localhost)"
  )
  parser.add_argument(
    "-p", "--port", default="5555", 
    help="Port number on which our underlying discovery ZMQ service runs, " + 
      "default=5555"
  )
  parser.add_argument(
    "-kn", "--knownnode", default="localhost:5555", 
    help="IP and port number on which we can find a known DHT node, " + 
      "default=localhost:5555 (only used in the 'Distributed' discovery config)"
  )
  parser.add_argument(
    "-c", "--config", default="Apps/Common/config.ini", 
    help="configuration file (default: Apps/Common/config.ini)"
  )
  parser.add_argument(
    "-l", "--loglevel", type=int, default=logging.INFO, 
    choices=[
      logging.DEBUG,logging.INFO,logging.WARNING,
      logging.ERROR,logging.CRITICAL
    ], 
    help="logging level, choices 10,20,30,40,50: default 20=logging.INFO"
  )
  return parser.parse_args()

"""Main program"""
def main():
  try:
    # obtain a system wide logger and initialize it to debug to begin with
    logging.debug("Main - acquire a child logger to log messages in")
    logger = logging.getLogger("SubAppln")
    # first parse the arguments
    logger.debug("Main: parse command line arguments")
    args = parseCmdLineArgs()
    # reset the log level to as specified
    logger.debug("Main: resetting log level to {}".format(args.loglevel))
    logger.setLevel(args.loglevel)
    logger.debug("Main: effective log level is {}".format(logger.getEffectiveLevel()))
    # Obtain a discovery application
    logger.debug("Main: obtain the object")
    disc_app = DiscoveryAppln(logger) # get the object
    disc_app.configure(args)          # configure the object
    disc_app.driver()                 # invoke the object driver
  except Exception as e: handle_exception(e)

"""Main entry point"""
if __name__ == "__main__":
  # set underlying default logging capabilities
  logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  main()
