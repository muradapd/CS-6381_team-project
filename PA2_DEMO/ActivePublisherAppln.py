###############################################
#
# Author: John Gordley
# Professor: Aniruddha Gokhale
# Vanderbilt University
#
# Purpose: Simple publisher script that comes and goes and does not perform is_ready
#
# Created: Spring 2023
#
###############################################

# import the needed packages
import time   # for sleep
import argparse  # for argument parsing
import configparser  # for configuration parsing
import logging  # for logging. Use it in place of print statements.
import random  # needed in the topic selection using random numbers
import sys
import atexit


# Import our topic selector. Feel free to use alternate way to
# get your topics of interest
from topic_selector import TopicSelector

# Now import our CS6381 Middleware
from CS6381_MW.ActivePublisherMW import PublisherMW

# import any other packages you need.

##################################
#       PublisherAppln class
##################################

class PublisherAppln ():

    ########################################
    # constructor
    ########################################
    def __init__(self, logger):
        self.iters = None   # number of iterations of publication
        self.name = None  # our name (some unique name)
        self.topiclist = None  # the different topics that we publish on
        self.lookup = None  # one of the diff ways we do lookup
        self.dissemination = None  # direct or via broker
        self.mw_obj = None  # handle to the underlying Middleware object
        self.logger = logger  # internal logger for print statements
        self.num_topics = None  # number of topics we want to publish

    ########################################
    # configure/initialize
    ########################################
    def configure(self, args):
        ''' Initialize the object '''

        try:
            # Here we initialize any internal variables
            self.logger.debug("PublisherAppln::configure")

            # initialize our variables
            self.name = args.name  # our name
            self.iters = args.iters  # num of iterations
            self.num_topics = args.num_topics

            # Now, get the configuration object
            self.logger.debug("PublisherAppln::configure - parsing config.ini")
            config = configparser.ConfigParser()
            config.read(args.config)
            self.lookup = config["Discovery"]["Strategy"]
            self.dissemination = config["Dissemination"]["Strategy"]

            # Now get our topic list of interest
            self.logger.debug("PublisherAppln::configure - selecting our topic list")
            ts = TopicSelector()
            self.topiclist = ts.interest(self.num_topics)

            # Now setup up our underlying middleware object to which we delegate
            # everything
            self.mw_obj = PublisherMW(self.logger, self.num_topics, self.lookup)
            
            # pass remainder of the args to the m/w object
            self.mw_obj.configure(args)

            atexit.register(self.mw_obj.clean_exit, self.name)

            self.logger.info(f"PublisherAppln - {self.name} configured with topics: {self.topiclist}")

        except Exception as e:
            raise e

    ########################################
    # driver program
    ########################################
    def driver(self):
        ''' Driver program '''

        try:
            self.logger.debug("PublisherAppln::driver")

            # dump our contents (debugging purposes)
            self.dump()

            # First ask our middleware to register ourselves with the discovery service
            self.logger.info(f"PublisherAppln - Attempting to register with Discovery service")
            result = self.mw_obj.register(self.name, self.topiclist)
            self.logger.info(f"PublisherAppln - Result of registration: {result}")
            if result != '1':
                self.logger.info(f"PublisherAppln - Failed to register. Exiting...")
                sys.exit(1)
            
            time.sleep(10)

            # Now disseminate
            ts = TopicSelector()
            for i in range(self.iters):
                # I leave it to you whether you want to disseminate all the topics of interest in
                # each iteration OR some subset of it. Please modify the logic accordingly.
                # Here, we choose to disseminate on all topics that we publish.  Also, we don't care
                # about their values. But in future assignments, this can change.
                for topic in self.topiclist:
                    # dissemination_data = topic + ":" + ts.gen_publication (topic)

                    self.mw_obj.disseminate(topic, ts.gen_publication(topic))

                    # time.sleep(random.randrange(1, 5))
                    time.sleep(2)

            self.logger.info(f"PublisherAppln - Dissemination complete after {self.iters} rounds")

            # Gracefully exit
            self.mw_obj.clean_exit(self.name)

        except Exception as e:
            raise e

    ########################################
    # dump the contents of the object
    ########################################
    def dump(self):
        ''' Pretty print '''

        try:
            self.logger.debug("**********************************")
            self.logger.debug("PublisherAppln::dump")
            self.logger.debug("------------------------------")
            self.logger.debug("     Name: {}".format(self.name))
            self.logger.debug("     Lookup: {}".format(self.lookup))
            self.logger.debug(
                "     Dissemination: {}".format(self.dissemination))
            self.logger.debug("     TopicList: {}".format(self.topiclist))
            self.logger.debug("     Iterations: {}".format(self.iters))
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
    parser = argparse.ArgumentParser(description="Publisher Application")

    # Now specify all the optional arguments we support
    # At a minimum, you will need a way to specify the IP and port of the lookup
    # service, the role we are playing, what dissemination approach are we
    # using, what is our endpoint (i.e., port where we are going to bind at the
    # ZMQ level)

    parser.add_argument("-n", "--name", required=True, default="pub",
                        help="Some name assigned to us. Keep it unique per publisher")

    parser.add_argument("-a", "--addr", required=True, default="localhost",
                        help="IP addr of this publisher to advertise (default: localhost)")

    parser.add_argument("-p", "--port", default="5577",
                        help="Port number on which our underlying publisher ZMQ service runs, default=5577")

    parser.add_argument("-d", "--discovery", required=True, default="localhost:5555",
                        help="IP Addr:Port combo for the discovery service, default localhost:5555")

    parser.add_argument("-t", "--num_topics", type=int, choices=range(1,
                        10), default=1, help="number of topics to select")

    parser.add_argument("-c", "--config", default="config.ini",
                        help="configuration file (default: config.ini)")

    parser.add_argument("-i", "--iters", type=int, default=1000,
                        help="number of publication iterations (default: 1000)")

    parser.add_argument("-l", "--loglevel", type=int, default=logging.INFO, choices=[
                        logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL], help="logging level, choices 10,20,30,40,50: default 10=logging.DEBUG")

    return parser.parse_args()


###################################
#
# Main program
#
###################################
def main():

    # obtain a system wide logger and initialize it to debug level to begin with
    logging.debug(
        "Main - acquire a child logger and then log messages in the child")
    logger = logging.getLogger("PubAppln")

    # first parse the arguments
    logger.debug("Main: parse command line arguments")
    args = parseCmdLineArgs()

    # reset the log level to as specified
    logger.debug("Main: resetting log level to {}".format(args.loglevel))
    logger.setLevel(args.loglevel)
    logger.debug("Main: effective log level is {}".format(
        logger.getEffectiveLevel()))

    # Obtain a publisher application
    logger.debug("Main: obtain the object")
    pub_app = PublisherAppln(logger)

    # configure the object
    pub_app.configure(args)

    # now invoke the driver program
    pub_app.driver()


###################################
#
# Main entry point
#
###################################
if __name__ == "__main__":

    # set underlying default logging capabilities
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    main()
