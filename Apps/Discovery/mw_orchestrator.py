###############################################
# Author: Aniruddha Gokhale
# Updated by: Patrick Muradaz
# Vanderbilt University
# Purpose: Discovery middleware for PAs
# Semester: Spring 2023
###############################################
#
# The discovery service is a server. So at the middleware level, we will
# maintain a REP socket binding it to the port on which we expect to
# receive requests.
#
# There will be a forever event loop waiting for requests. Each request will
# be parsed and the application logic asked to handle the request. To that
# end, an upcall will need to be made to the application logic.
#
# Import statements
import configparser, sys, os
sys.path.append(os.getcwd())
from Apps.Common.common import handle_exception
from Apps.Discovery.centralized_mw import CentralizedMW
from Apps.Discovery.distributed_mw import DistributedMW

"""Discovery Middleware class"""
class MWOrchestrator():

    """constructor"""
    def __init__(self, logger):
        self.logger = logger    # internal logger for print statements
        self.discovery = None   # determine if we are centralized or DHT
        self.mw_helper = None   # handle the discovery type specific functions

    """configure/initialize"""
    def configure(self, args):
        try:
            self.logger.debug("MWOrchestrator::configure")
            # get the configuration object
            config = configparser.ConfigParser()
            config.read(args.config)
            self.discovery = config["Discovery"]["Strategy"]
            dissemination = config["Dissemination"]["Strategy"]
            # determine which helper class to use
            if self.discovery == "Distributed":
                self.mw_helper = DistributedMW(self.logger, dissemination)
            elif self.discovery == "Centralized":
                self.mw_helper = CentralizedMW(self.logger, dissemination)
            else: raise Exception("Invalid discovery method.")
            # set up the helper class
            self.mw_helper.configure(args)
            return self.discovery
        except Exception as e: handle_exception(e)

    """register with the DHT ring"""
    def register_dht(self, bits_hash):
        self.logger.debug("MWOrchestrator::register_dht") 
        try: return self.mw_helper.register_dht(bits_hash)
        except Exception as e: handle_exception(e)

    """listen for registrations and lookups"""
    def listen(self, hash_table, pubs, subs, numpubs, numsubs, node_id):
        try:
            self.logger.debug("MWOrchestrator::listen")
            if self.discovery == "Distributed":
                self.mw_helper.listen(hash_table, numpubs, numsubs, node_id)
            elif self.discovery == "Centralized":
                self.mw_helper.listen(pubs, subs, numpubs, numsubs)
            else: raise Exception("Invalid discovery method.")
        except Exception as e: handle_exception(e)
