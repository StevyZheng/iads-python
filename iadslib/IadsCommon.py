# coding = utf-8

import logging
import os
import re
from os.path import join as pjoin

XT_DEFAULT_BASEFS = "xfs"

IADS_LOG_DIR = "/var/log/iads"
IADS_LOG_FILE = "%s/iads.log" % IADS_LOG_DIR
IADS_LOG_FORMAT = '%(asctime)s [%(name)s][%(process)d] %(levelname)s: %(message)s'
IADS_LOG_LEVEL = logging.WARNING
IADS_DEBUG_LEVEL = logging.INFO
IADS_SHELL_TIMEOUT_DEF = 30
IADS_KEEPALIVE_INTERVAL = 5

XTETCD_ROOT = '/etc/xtetcd'
CRASH_DIR = "/var/crash"

IADS_HDD = 'HDD'
IADS_SSD = 'SSD'

YES_STRINGS = ["yes", "YES", "ON", "on", "true", "True", "TRUE"]
NO_STRINGS = ["no", "NO", "OFF", "off", "false", "False", "FALSE"]


def read_file(_file):
	_str = None
	with open(_file) as fp:
		_str = fp.read()
		return _str[:-1]


def write_file(_file, _str):
	with open(_file, 'w') as fp:
		fp.truncate()
		fp.write(_str)

_supported_dists = (
	'centos7', 'centos6', 'redhat'
)
