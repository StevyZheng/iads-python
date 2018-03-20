# coding=utf-8

import os
import logging
from os.path import join as pjoin


IADS_LOG_DIR = "/var/log/iads"
IADS_LOG_FILE = "%s/iads.log" % IADS_LOG_DIR
IADS_LOG_FORMAT = '%(asctime)s [%(name)s][%(process)d] %(levelname)s: %(message)s'
IADS_LOG_LEVEL = logging.WARNING
IADS_DEBUG_LEVEL = logging.INFO
IADS_SHELL_TIMEOUT_DEF = 30

