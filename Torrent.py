#!/usr/bin/env python
# -*- coding: utf-8 -*- 

# **********
# Filename:         Torrent.py
# Description:      A small torrent file library
# Author:           Marc Vieira Cardinal
# Creation Date:    July 22, 2014
# Revision Date:    July 23, 2014
# Resources:
#   http://torrentfreak.com/how-to-make-the-best-torrents-081121/
#   http://monotorrent.fr.yuku.com/topic/367/RecommendedPieceSize-and-Optimum-Piece-Length#.U88HnXWx15Q
# **********


# External imports
import time
import types
import socket
from hashlib import md5, sha1


# Application imports
from bencode import bencode


class Torrent():
    def __init__(self, logger):
        self.logger      = logger.getChild(__name__)

    def TestPieceSize(self):
        for i in range(1, 10):
            totalSize = i * 1000 # Kb range
            pSize, pCount = self.OptimalPieceSize(totalSize)
            self.logger.info("%s,%s,%s" % (totalSize, pSize, pCount))

        for i in range(1, 10):
            totalSize = i * 1000000 # Mb range
            pSize, pCount = self.OptimalPieceSize(totalSize)
            self.logger.info("%s,%s,%s" % (totalSize, pSize, pCount))

        for i in range(1, 10):
            totalSize = i * 1000000000 # Gb range
            pSize, pCount = self.OptimalPieceSize(totalSize)
            self.logger.info("%s,%s,%s" % (totalSize, pSize, pCount))

    def OptimalPieceSize(self, totalSize):
        """ Based on:
            public int RecommendedPieceSize()
                {
                long totalSize = GetSize();

                // Check all piece sizes that are multiples of 32kB
                // Basically "i" starts at 32768 and does *2 until it reaches
                // 4 * 1024 * 1024 (or 4194304)
                //   32768 is 2^15
                // 4194304 is 2^22
                // Gives an exp range of [15,22[
                for (int i = 32768; i < 4 * 1024 * 1024; i *= 2)
                    {
                    int pieces = (int)(totalSize / i) + 1;
                    if ((pieces * 20) < (60 * 1024))
                        return i;
                    }

                // If we get here, we're hashing a massive file, so lets limit
                // to a max of 4MB pieces.
                return 4 * 1024 * 1024;
                }

            Expected results:
                OptimalPieceSize(         1 000) =   32768,   1 (   1k size =    1 piece of    32768)
                OptimalPieceSize(       100 000) =   32768,   4 ( 100k size =    4 pieces of   32768)
                OptimalPieceSize(     1 000 000) =   32768,  31 (  1mb size =   31 pieces of   32768)
                OptimalPieceSize(   100 000 000) =   32768,3052 (100mb size = 3052 pieces of   32768)
                OptimalPieceSize(   250 000 000) =  131072,1908 (250mb size = 1908 pieces of  131072)
                OptimalPieceSize( 1 000 000 000) =  524288,1908 (  1gb size = 1908 pieces of  524288)
                OptimalPieceSize(10 000 000 000) = 4194304,2385 ( 10gb size = 2385 pieces of 4194304)
            Real world sizes:
                OptimalPieceSize(         4700 ) =   32768,   1 ( 4.7k size =    1 piece of    32768)
                OptimalPieceSize(         5400 ) =   32768,   1 ( 5.4k size =    1 piece of    32768)
                OptimalPieceSize(        27000 ) =   32768,   1 (  27k size =    1 piece of    32768)
                OptimalPieceSize(        60000 ) =   32768,   2 (  60k size =    2 pieces of   32768)
                OptimalPieceSize(       101000 ) =   32768,   4 ( 101k size =    4 pieces of   32768)
                OptimalPieceSize(       156000 ) =   32768,   5 ( 156k size =    1 pieces of   32768)
                OptimalPieceSize(       308000 ) =   32768,  10 ( 308k size =   10 pieces of   32768)
                OptimalPieceSize(       842000 ) =   32768,  26 ( 842k size =   26 pieces of   32768)
                OptimalPieceSize(    1 100 000 ) =   32768,  34 (1.1mb size =   34 pieces of   32768)
                OptimalPieceSize(    2 900 000 ) =   32768,  89 (2.9mb size =   89 pieces of   32768)
                OptimalPieceSize(    4 600 000 ) =   32768, 141 (4.6mb size =  141 pieces of   32768)
                OptimalPieceSize(    5 000 000 ) =   32768, 153 (5.0mb size =  153 pieces of   32768)
                OptimalPieceSize(    6 100 000 ) =   32768, 187 (6.1mb size =  187 pieces of   32768)
                OptimalPieceSize(    7 500 000 ) =   32768, 229 (7.5mb size =  229 pieces of   32768)
                OptimalPieceSize(   21 000 000 ) =   32768, 641 ( 21mb size =  641 pieces of   32768)
                OptimalPieceSize(   93 000 000 ) =   32768,2839 ( 93mb size = 2839 pieces of   32768)
                OptimalPieceSize(1 100 000 000 ) =  524288,2099 (1.1gb size = 2099 pieces of  524288)
                OptimalPieceSize(1 400 000 000 ) =  524288,2671 (1.4gb size = 2671 pieces of  524288)
                OptimalPieceSize(1 800 000 000 ) = 1048576,1717 (1.8gb size = 1717 pieces of 1048576)
                OptimalPieceSize(3 600 000 000 ) = 2097152,1717 (3.6gb size = 1717 pieces of 2097152)
                OptimalPieceSize(4 400 000 000 ) = 2097152,2099 (4.4gb size = 2099 pieces of 2097152)
                """
        self.logger.info("Calculating piece size for [%s]" % totalSize)
        for size in (2**exp for exp in range(15,22)):
            pieces = int(totalSize / size) + 1

            if (pieces * 20) < (60 * 1024):
                return size, pieces

        return 4194304, int(totalSize / 4194304) + 1 # (2^22)

    def Slice(self, text, length):
        return [text[i:i+length] for i in range(0, len(text), length)]

    def GenInfoDict(self, filename):
        """ Returns the info dictionary for a torrent file """
        """ with a given source filename """
        self.logger.info("Generating torrent info for [%s]" % filename)

        with open(filename) as f:
            contents = f.read()

        pieceLength, pieceCount = self.OptimalPieceSize(len(contents))

        # Pieces processing
        pieces = self.Slice(contents, pieceLength)
        pieces = [ sha1(p).digest() for p in pieces ]

        return {
            "piece length": pieceLength,
            "length":       len(contents),
            "name":         filename,
            "md5sum":       md5(contents).hexdigest(),
            "pieces":       "".join(pieces),
        }

    def GenTorrentFileContent(self, filename, tracker, comment = None):
        """ Generate a bencoded torrent file """
        self.logger.info("Generating torrent content for [%s,%s,%s]" % (filename, tracker, comment))

        torrent = {}

        # Multiple trackers
        if type(tracker) == list:
            torrent["announce"]      = tracker[0]
            torrent["announce-list"] = [[tr] for tr in tracker]
        else:
            torrent["announce"]      = tracker

        torrent["creation date"] = int(time.time())
        torrent["created by"] = "pyBTclient"
        if comment:
            torrent["comment"] = comment

        torrent["info"] = self.GenInfoDict(filename)

        return bencode(torrent)

    def WriteTorrentFile(self, torrentFile, filename, tracker, comment = None):
        """ Write the output of GenTorrentFileContent to a file """
        self.logger.info("Writing torrent file [%s,%s,%s,%s]" % (torrentFile, filename, tracker, comment))

        content = self.GenTorrentFileContent(filename, tracker, comment)

        with open(torrentFile, "w") as f:
            f.write(content)
