###############################################
#
# Author: Aniruddha Gokhale
# Vanderbilt University
#
# Purpose: Skeleton/Starter code for the Broker application
#
# Created: Spring 2023
#
###############################################


# This is left as an exercise for the student.  The Broker is involved only when
# the dissemination strategy is via the broker.
#
# A broker is an intermediary; thus it plays both the publisher and subscriber roles
# but in the form of a proxy. For instance, it serves as the single subscriber to
# all publishers. On the other hand, it serves as the single publisher to all the subscribers. 


# import the needed packages
import os     # for OS functions
import sys    # for syspath and system exception
import time   # for sleep
import argparse  # for argument parsing
import configparser  # for configuration parsing
import logging  # for logging. Use it in place of print statements.
import random  # needed in the topic selection using random numbers

# Now import our CS6381 Middleware
from CS6381_MW.BrokerMW import BrokerMW

# import any other packages you need.

##################################
#       BrokerAppln class
##################################

class BrokerAppln ():

    ########################################
    # constructor
    ########################################
    def __init__(self, logger):
        self.name = None  # our name (some unique name)
        self.lookup = None  # one of the diff ways we do lookup
        self.dissemination = None  # direct or via broker
        self.mw_obj = None  # handle to the underlying Middleware object
        self.logger = logger  # internal logger for print statements

    ########################################
    # configure/initialize
    ########################################
    def configure(self, args):
        ''' Initialize the object '''

        try:
            # Here we initialize any internal variables
            self.logger.debug("BrokerAppln::configure")

            # initialize our variables
            self.name = args.name  # our name

            # Now, get the configuration object
            self.logger.debug(
                "BrokerAppln::configure - parsing config.ini")
            config = configparser.ConfigParser()
            config.read(args.config)
            self.lookup = config["Discovery"]["Strategy"]
            self.dissemination = config["Dissemination"]["Strategy"]

            # Now setup up our underlying middleware object to which we delegate
            # everything
            self.logger.debug(
                "BrokerAppln::configure - initialize the middleware object")
            self.mw_obj = BrokerMW(self.logger)
            # pass remainder of the args to the m/w object
            self.mw_obj.configure(args)

            self.logger.debug(
                "BrokerAppln::configure - configuration complete")
            
        except Exception as e:
            raise e

    ########################################
    # driver program
    ########################################
    def driver(self):
        ''' Driver program '''

        try:
            self.logger.debug("BrokerAppln::driver")

            # dump our contents (debugging purposes)
            self.dump()

            # First ask our middleware to register ourselves with the discovery service
            self.logger.debug(
                "BrokerAppln::driver - register with the discovery service")
            result = self.mw_obj.register(self.name)
            self.logger.debug(
                "BrokerAppln::driver - result of registration".format(result))

            # Now keep checking with the discovery service if we are ready to go
            self.logger.debug(
                "BrokerAppln::driver - check if are ready to go")
            while (not self.mw_obj.is_ready()):
                # sleep between calls so that we don't make excessive calls
                time.sleep(5)
                self.logger.debug(
                    "BrokerAppln::driver - check again if are ready to go")

            # We broke out so we are ready to go
            self.logger.debug(
                "BrokerAppln::driver - Received True from Discovery Service ready check")

            # sys.exit(1)

            # Perform a lookup request to find the publishers to connect to
            pub_addresses = self.mw_obj.lookup_all_pubs()
            while len(pub_addresses) == 0:
                self.logger.debug(
                    "BrokerAppln::driver - No publishers for our topics found. Checking again...")
                time.sleep(5)
                pub_addresses = self.mw_obj.lookup_all_pubs()

            self.logger.debug(f"BrokerAppln::driver - Found the following publishers: {pub_addresses}")

            # Tell MW to connect to publishers
            self.mw_obj.connect_pubs(pub_addresses)

            self.logger.debug(
                "BrokerAppln::driver - Listening for publishes of interest")

            # Now begin listening to publishes
            while True:
                result = self.mw_obj.event_loop()
                self.logger.debug(f"BrokerAppln::driver - Received {result}")
                self.mw_obj.disseminate(result[0], result[1])

        except Exception as e:
            raise e

    ########################################
    # dump the contents of the object
    ########################################
    def dump(self):
        ''' Pretty print '''

        try:
            self.logger.debug("**********************************")
            self.logger.debug("BrokerAppln::dump")
            self.logger.debug("------------------------------")
            self.logger.debug("     Name: {}".format(self.name))
            self.logger.debug("     Lookup: {}".format(self.lookup))
            self.logger.debug(
                "     Dissemination: {}".format(self.dissemination))
            self.logger.debug("**********************************")

        except Exception as e:
            raise e

###################################
#
# Parse command line arguments
#
###################################


def parseCmdLineArgs():
    # instantiate a ArgumentParser object
    parser = argparse.ArgumentParser(description="Broker Application")

    # Now specify all the optional arguments we support
    # At a minimum, you will need a way to specify the IP and port of the lookup
    # service, the role we are playing, what dissemination approach are we
    # using, what is our endpoint (i.e., port where we are going to bind at the
    # ZMQ level)

    parser.add_argument("-n", "--name", default="pub",
                        help="Some name assigned to us. Keep it unique per Broker")

    parser.add_argument("-a", "--addr", default="localhost",
                        help="IP addr of this Broker to advertise (default: localhost)")

    parser.add_argument("-p", "--port", default="5577",
                        help="Port number on which our underlying Broker ZMQ service runs, default=5577")

    parser.add_argument("-d", "--discovery", default="localhost:5555",
                        help="IP Addr:Port combo for the discovery service, default localhost:5555")

    parser.add_argument("-c", "--config", default="config.ini",
                        help="configuration file (default: config.ini)")

    parser.add_argument("-i", "--iters", type=int, default=1000,
                        help="number of publication iterations (default: 1000)")

    parser.add_argument("-l", "--loglevel", type=int, default=logging.DEBUG, choices=[
                        logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL], help="logging level, choices 10,20,30,40,50: default 10=logging.DEBUG")

    return parser.parse_args()


###################################
#
# Main program
#
###################################
def main():
    try:
        # obtain a system wide logger and initialize it to debug level to begin with
        logging.debug(
            "Main - acquire a child logger and then log messages in the child")
        logger = logging.getLogger("BrokerAppln")

        # first parse the arguments
        logger.debug("Main: parse command line arguments")
        args = parseCmdLineArgs()

        # reset the log level to as specified
        logger.debug("Main: resetting log level to {}".format(args.loglevel))
        logger.setLevel(args.loglevel)
        logger.debug("Main: effective log level is {}".format(
            logger.getEffectiveLevel()))

        # Obtain a Broker application
        logger.debug("Main: obtain the object")
        sub_app = BrokerAppln(logger)

        # configure the object
        sub_app.configure(args)

        # now invoke the driver program
        sub_app.driver()

    except Exception as e:
        logger.error("Exception caught in main - {}".format(e))
        return


###################################
#
# Main entry point
#
###################################
if __name__ == "__main__":

    # set underlying default logging capabilities
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    main()
