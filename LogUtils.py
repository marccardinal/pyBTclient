#!/usr/bin/env python
# -*- coding: utf-8 -*- 

# **********
# Filename:         LogUtils.py
# Description:      A set of logging utiliries
# Author:           Marc Vieira Cardinal
# Creation Date:    July 08, 2014
# Revision Date:    July 19, 2014
# **********


import sys
import logging
from logging.handlers import TimedRotatingFileHandler


def RotatingFile(tag, logLevel, logFile, foreground):
    """
    logLevel   -- string,  one of NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
    logFile    -- string,  path for a log file
    foreground -- boolean, true == also log to stdout
    """

    logLevel = logging.getLevelName(logLevel.upper())
    logger = logging.getLogger(tag)
    logger.setLevel(logLevel)
    logFormatter = logging.Formatter('%(asctime)s,%(msecs)d %(name)s [%(levelname)s] %(message)s', "%Y-%m-%d %H:%M:%S")

    logFile = TimedRotatingFileHandler(logFile, "midnight")
    logFile.suffix = "%Y-%m-%d_%H:%M:%S"
    logFile.setFormatter(logFormatter)
    logFile.setLevel(logLevel)
    logger.addHandler(logFile)

    if foreground:
        logConsole = logging.StreamHandler(sys.stdout)
        logConsole.setFormatter(logFormatter)
        logConsole.setLevel(logLevel)
        logger.addHandler(logConsole)

    return logger
