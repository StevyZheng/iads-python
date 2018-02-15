# coding = utf-8

import sys
import os
import json
import signal
import logging
import traceback

from .IadsCommon import *


class IadsBaseException (Exception):
        """When we manually raise exception, we should use this rather than
        generic Exceptions. We should catch explicitly raised exceptions (which
        are generally not bugs, but by design), but let bugs dump traces (which
        better helps debugging).
        """
        pass


class IadsBaseContext(object):
    def __init__(self,
                 name=None,
                 logfile=IADS_LOG_FILE,
                 loglevel=IADS_LOG_LEVEL,
                 logconsole=True,
                 lockfile=""):
        if not name:
            name = self.__class__.__name__
        if type(loglevel) != type(IADS_DEBUG_LEVEL):
            loglevel = self.__map_level(logfile)

        self.name = name
        self.loglevel = loglevel
        self.logfile = logfile
        self.logconsole = logconsole
        self.agentHostname = None

        if logfile:
            logdir = os.path.dirname(logfile)
            if not os._exists(logdir):
                os.makedirs(logdir)
            if not os.path.exists(logfile):
                with open(logfile, 'w') as fp:
                    pass
            self.logger = self.__init_logger(name, logfile, loglevel, logconsole)
        else:
            self.logger = None
        signal.signal(signal.SIGHUP, self.__log_rotate_handler)

    def __init_logger(self, name, logfile, loglevel, logconsole):
        logger = logging.Logger(name)
        formatter = logging.Formatter(IADS_LOG_FORMAT)
        logger.setLevel(loglevel)

        # file logger
        handler = logging.FileHandler(logfile)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # stream logger if needed
        if logconsole and sys.stdin.isatty():
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def __map_level(self, lvl):
        levelList = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warn": logging.WARNING,
            "warning": logging.WARNING,
            "err": logging.ERROR,
            "error": logging.ERROR,
        }
        if lvl not in levelList:
            raise Exception("unknown log level: " + lvl)
        return levelList[lvl]

    def __clear_logger(self):
        # without this, we will have fh leak, and finally leads to fd
        # overflow of process..

        # in case we have not inited the instance..
        if not hasattr(self, "logger"):
            return

        if self.logger:
            for handler in self.logger.handlers:
                handler.close()
            del self.logger

    def __log_rotate_handler (self, sig=None, frm=None):
        "Handles log rotate"
        self.__clear_logger()
        self.logger = self.__init_logger(self.name,
                                        self.logfile,
                                        self.loglevel,
                                        self.logconsole)
        self.logger.info("Received SIGHUP, rotating log")