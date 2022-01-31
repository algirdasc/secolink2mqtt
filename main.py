#!/usr/bin/python3

import os
import logging
import secolink
import configparser

APP_PATH = os.path.dirname(os.path.abspath(__file__))
LOG_FORMAT = '%(asctime)-15s\t%(name)s\t\t%(levelname)s\t%(message)s'

# Parse config
config = configparser.ConfigParser()
config.read(os.path.join(APP_PATH, 'config.ini'))

# Configure logging
logging.basicConfig(
    filename=config.get('logging', 'filename'), 
    format=LOG_FORMAT,
    level=getattr(logging, config.get('logging', 'level'), 'INFO')
)
logger = logging.getLogger('main')

# Assign config values
secolink.Server.config = config
connection = (config.get('secolink', 'bind', fallback='0.0.0.0'), config.getint('secolink', 'port', fallback=8130))

# Start server
with secolink.Server(connection, secolink.Handler) as server:
    server.serve_forever()

