#!/usr/bin/env python
# -*- coding: utf-8 -*- 

# **********
# Filename:         pyBTclient.py
# Description:      A torrent client
# Author:           Marc Vieira Cardinal
# Creation Date:    July 16, 2014
# Revision Date:    July 26, 2014
# Dependencies:
#    apt-get install python-libtorrent
# **********


# External imports
import sys
import time
import urllib
import requests
import tempfile
import libtorrent as lt
from argparse import ArgumentParser


# Application imports
import LogUtils
import Torrent


#############
# ActionMKTorrent
###

def ActionMKTorrent(logger, args):
    torrent = Torrent.Torrent(logger)
    torrent.WriteTorrentFile(args["destFile"],
                             args["sourceFile"],
                             args["trackerAnnUri"],
                             comment = "Created by pyBTclient")


#############
# ActionDNLDTorrent
###

def ActionDNLDTorrent(logger, args):

    ses = lt.session()
    ses.listen_on(args["portStart"],
                  args["portEnd"])

    info = lt.torrent_info(args["torrentFile"])
    h = ses.add_torrent({'ti':        info,
                         'save_path': args["destPath"]})

    logger.info("Starting [%s]" % h.name())
    while (not h.is_seed()):
       s = h.status()

       state_str = ['queued', 'checking', 'downloading metadata', \
          'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']
       print '\r%.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' % \
          (s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000, \
          s.num_peers, state_str[s.state]),
       sys.stdout.flush()

       time.sleep(1)

    logger.info("Completed [%s]" % h.name())


#############
# ActionDNLDFromKey
###

def ActionDNLDFromKey(logger, args):

    # Download the torrent identified by fileKey to a temp location
    tempFile = tempfile.NamedTemporaryFile(delete = false)
    logger.info("Retrieving key [%s] to [%s]" % (args["fileKey"], tempFile))
    tempFile.write(urllib.urlopen(args["trackerGetUri"] + "?key=" + args["fileKey"]).read())
    tempFile.close()

    args["torrentFile"] = tempFile.name

    # Pass the processing along to the regular
    # torrent download routine
    ActionDNLDTorrent(logger, args)

    # Cleanup the temp file
    tempFile.unlink(tempFile.name)


#############
# ActionPushTorrent
###

def ActionPushTorrent(logger, args):

    requests.post(args["trackerPushUri"],
                  files = { "torrentFile": (args["fileKey"], open(args["torrentFile"], 'rb')) },
                )


#############
# ActionTests
###

def ActionTests(logger, args):

    if args["testName"] == "tsize":
        torrent = Torrent.Torrent(logger)
        torrent.TestPieceSize()


#############
# Main
###

if __name__ == "__main__":

    # Parse the command line arguments
    # Define the main parser (top-level)
    argParser = ArgumentParser()

    argParser.add_argument("-f", "--foreground",
                           dest    = "foreground",
                           action  = "store_true",
                           default = False,
                           help    = "Run in foreground")
    argParser.add_argument("-l", "--loglevel",
                           dest    = "logLevel",
                           choices = ["notset", "debug", "info",
                                      "warning", "error", "critical"],
                           default = "notset",
                           help    = "Logging level")
    argParser.add_argument("-o", "--logfile",
                           dest    = "logFile",
                           action  = "store",
                           default = "/tmp/pyBTclient.log",
                           help    = "Log file")

    subParsers = argParser.add_subparsers(help = "sub-command help")

    # Define the mktorrent sub-parser
    mktorrentParser = subParsers.add_parser("mktorrent", help = "mktorrent help")
    mktorrentParser.add_argument("sourceFile",
                                 action = "store",
                                 help = "Source file for the torrent")
    mktorrentParser.add_argument("destFile",
                                 action = "store",
                                 help = "Filename of the torrent to be created")
    mktorrentParser.set_defaults(func = ActionMKTorrent)
    mktorrentParser.add_argument("trackerAnnUri",
                                 action = "store",
                                 help = "The address of the announce endpoint")

    # Define the dnldtorrent sub-parser
    dnldtorrentParser = subParsers.add_parser("dnldtorrent", help = "dnldtorrent help")
    dnldtorrentParser.add_argument("torrentFile",
                                   action = "store",
                                   help = "Source torrent file")
    dnldtorrentParser.add_argument("destPath",
                                   action = "store",
                                   help = "Location of the resulting file(s)")
    dnldtorrentParser.add_argument("--port-start",
                                   dest = "portStart",
                                   action = "store",
                                   type = int,
                                   default = 6881,
                                   help = "Location of the resulting file(s)")
    dnldtorrentParser.add_argument("--port-end",
                                   dest = "portEnd",
                                   action = "store",
                                   type = int,
                                   default = 6981,
                                   help = "Location of the resulting file(s)")
    dnldtorrentParser.set_defaults(func = ActionDNLDTorrent)

    # Define the dnldfromkey sub-parser
    dnldfromkeyParser = subParsers.add_parser("dnldfromkey", help = "dnldfromkey help")
    dnldfromkeyParser.add_argument("fileKey",
                                   action = "store",
                                   help = "Key for the torrent definition")
    dnldfromkeyParser.add_argument("destPath",
                                   action = "store",
                                   help = "Location of the resulting file(s)")
    dnldfromkeyParser.add_argument("trackerGetUri",
                                   action = "store",
                                   help = "The address of the get endpoint")
    dnldfromkeyParser.add_argument("--port-start",
                                   dest = "portStart",
                                   action = "store",
                                   type = int,
                                   default = 6881,
                                   help = "Location of the resulting file(s)")
    dnldfromkeyParser.add_argument("--port-end",
                                   dest = "portEnd",
                                   action = "store",
                                   type = int,
                                   default = 6981,
                                   help = "Location of the resulting file(s)")
    dnldfromkeyParser.set_defaults(func = ActionDNLDFromKey)

    # Define the pushtorrent sub-parser
    pushtorrentParser = subParsers.add_parser("pushtorrent", help = "pushtorrent help")
    pushtorrentParser.add_argument("torrentFile",
                                   action = "store",
                                   help = "Source torrent file")
    pushtorrentParser.add_argument("fileKey",
                                   action = "store",
                                   help = "Key for the torrent definition")
    pushtorrentParser.add_argument("trackerPushUri",
                                   action = "store",
                                   help = "The address of the push endpoint")
    pushtorrentParser.set_defaults(func = ActionPushTorrent)

    # Define the autoindexer sub-parser
    autoindexerParser = subParsers.add_parser("autoindexer", help = "autoindexer help")
    autoindexerParser.add_argument("trackerPushUri",
                                   action = "store",
                                   help = "The address of the push endpoint")
    autoindexerParser.add_argument("watchPaths",
                                   action = "store",
                                   nargs = argparse.REMAINDER,
                                   help = "The address of the push endpoint")
    autoindexerParser.set_defaults(func = ActionAutoIndexer)


# TODO: --autoIndex or --autoUpload for a daemon that
# watches a specific folder?


    # Define the tests sub-parser
    testsParser = subParsers.add_parser("tests", help = "tests help")
    testsParser.add_argument("testName",
                             choices = ["tsize"],
                             help = "Name of the test to run")
    testsParser.set_defaults(func = ActionTests)

    # Parse the command line arguments
    argsObj = argParser.parse_args()
    argsDict = vars(argParser.parse_args())

    # Start the logging facilities
    logger = LogUtils.RotatingFile(__name__,
                                   argsDict["logLevel"],
                                   argsDict["logFile"],
                                   argsDict["foreground"])
    logger.info("Started with arguments: " + str(argsDict))

    # Run the action function
    argsObj.func(logger, argsDict)