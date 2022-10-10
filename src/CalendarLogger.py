import logging

# Create a custom logger
logger = logging.getLogger(__name__)

def buildLogger(options):
    # Create handlers
    streamLevel = logging.INFO

    if (options.verbose):
        streamLevel = logging.INFO

    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(options.log_file)
    logger.setLevel(logging.DEBUG)
    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(levelname)s - %(message)s')
    f_format = logging.Formatter('%(levelname)s (%(asctime)s) %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

def addLoggerArgsToParser(parser):
    parser.add_argument('-v', '--verbose', help = 'Verbose output.', action = 'store_true', default = False)
    parser.add_argument('--log-file', default = './data/scrapy.log')
