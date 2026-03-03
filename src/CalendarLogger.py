"""
This is a custom logger that logs both to stream and to a logfile.
Probably overkill, but can be pasted into future scripts.
"""

import logging
import os
import subprocess

class NotifyHandler(logging.Handler):
    def __init__(self, log_file=None):
        super().__init__()
        self.log_file = os.path.abspath(log_file) if log_file else None

    def emit(self, record):
        try:
            msg = self.format(record)
            if self.log_file:
                subprocess.Popen([
                    'bash', '-c',
                    'action=$(notify-send "Calendar Crawler" "$1" --action="view=View Log"); '
                    '[ "$action" = "view" ] && '
                    'zenity --text-info --filename="$2" --title="Calendar Crawler - Error Log" --width=800 --height=600 2>/dev/null',
                    '--', msg, self.log_file
                ])
            else:
                subprocess.Popen(['notify-send', 'Calendar Crawler', msg])
        except Exception:
            pass

# Create a custom logger
logger = logging.getLogger(__name__)

def buildLogger(options):
    # Create handlers
    streamLevel = logging.WARNING

    if (options.verbose):
        streamLevel = logging.INFO
    if (options.debug):
        streamLevel = logging.DEBUG

    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(options.log_file)
    last_handler = logging.FileHandler('./data/current.log', mode = 'w')

    logger.setLevel(logging.DEBUG)
    c_handler.setLevel(streamLevel)
    last_handler.setLevel(logging.ERROR)
    f_handler.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(levelname)s - %(message)s')
    last_format = logging.Formatter('%(levelname)s - %(message)s')
    f_format = logging.Formatter('%(levelname)s (%(asctime)s) %(message)s')
    c_handler.setFormatter(c_format)
    last_handler.setFormatter(last_format)
    f_handler.setFormatter(f_format)

    # Desktop notification handler for errors
    n_handler = NotifyHandler(log_file='./data/current.log')
    n_handler.setLevel(logging.ERROR)
    n_handler.setFormatter(c_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(last_handler)
    logger.addHandler(f_handler)
    logger.addHandler(n_handler)

def addLoggerArgsToParser(parser, defaults):
    parser.add_argument('-v', '--verbose', help = 'Verbose output.', action = 'store_true', default = defaults.get('verbose', False))
    parser.add_argument('--debug', help = 'Debug output.', action = 'store_true', default = defaults.get('debug', False))
    parser.add_argument('--log-file', default = defaults.get('logLocation', './data/scrapy.log'))
