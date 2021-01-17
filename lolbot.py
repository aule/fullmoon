import sys
import socket
import string
import re

HOST = ""
PORT = 6667

DEBUG_FLAG = False


class Bot(object):
    class BadBot(Exception):
        pass

    linegrep = re.compile(
        r"(:((?P<user>\S+)!)?(?P<address>\S+)\s+)?(?P<command>\S+)\s*(?P<params>((?<=\s)[^:\s]\S*\s*)*)((?<=\s):(?P<tail>[^\r]*))?"
    )

    def __init__(self, nick=None, host=HOST, port=PORT, **params):
        if not nick:
            return
        self.params = params
        self.nick = nick
        self.buffer = ""
        self.s = socket.socket()
        self.s.connect((host, port))
        self.s.settimeout(0.01)
        self.active = False
        self.initialised = False
        self()
        self.s.send("NICK %s\r\n" % nick)

        def mkuser(nick):
            u = "".join([l for l in nick if l.isalnum()])
            return (u[0].isdigit() and "l" or "") + u

        self.s.send("USER %s %s bla :%s\r\n" % (mkuser(nick), mkuser(nick), nick))
        if DEBUG_FLAG:
            print "-- Sent login info (%s,%s)" % (nick, mkuser(nick))
        while not self.active:
            self()
        if DEBUG_FLAG:
            print "-- initialising"
        self.init(**params)
        self.initialised = True

    def init(self):
        pass

    def loop(self):
        pass

    def __call__(self):
        if self.active:
            self.loop()
        try:
            self.buffer = self.buffer + self.s.recv(1024)
        except socket.timeout:
            return
        temp = string.split(self.buffer, "\n")
        self.buffer = temp.pop()

        for line in temp:
            if DEBUG_FLAG:
                print line
            msg = self.linegrep.match(line.strip())
            if msg:
                data = msg.groupdict()
                if not data["params"]:
                    data["params"] = ""
                data["params"] = data["params"].split(" ")
                if data["tail"]:
                    data["params"].append(data["tail"])
                cmd = data["command"].upper()
                if cmd.isdigit():
                    cmd = "N" + cmd
                if hasattr(self, cmd):
                    getattr(self, cmd)(**data)

    def PING(self, command, params, tail, **spare):
        if not params:
            return
        self.s.send("PONG :%s\r\n" % params[-1])
        if DEBUG_FLAG:
            print "--PONG! (%s)" % params[-1]

    def N001(self, **spare):
        self.active = True

    def ERROR(self, params, **spare):
        raise self.BadBot(params)
