"""
Main loop for handling exceptions, reboots, copyovers and logging

Author: Joe Taylor
Date: 1/6/10
"""

import datetime
import pickle
import sys
from time import sleep
import traceback
import socks


def copyover():
    for m in sys.modules.values():
        if type(m) == type(sys):
            try:
                reload(m)
            except ImportError:
                pass
    reload(sys.modules["winbot"])
    reload(sys.modules["fullmoon"])


def savestate(d):
    for i in d:
        try:
            d[i] = (True, pickle.dumps(d[i]))
        except Exception:
            print "Skipped %s" % i
            d[i] = (False, d[i])
    return d


def loadstate(d):
    for i in d:
        if d[i][0]:
            d[i] = pickle.loads(d[i][1])
        else:
            d[i] = d[i][1]
    return d


def main(
    nick="Mayor",
    channel="#fullmoon",
    logpath="fullmoon.log",
    host="localhost",
    port=6667,
    tick=0.2,
    socket="fullmoon.sock",
):

    log_file = open(logpath, "a")

    def log(msg):
        log_file.write(msg)
        log_file.flush()

    if socket:
        botInterface = socks.SockPuppet(socket)
    else:
        botInterface = socks.DummySockPuppet()

    import fullmoon

    class ReBoot(Exception):
        pass

    log("*** BOOTING: %s\n" % (datetime.datetime.now()))

    while True:
        try:
            copyover()
            n = fullmoon.Narrator(
                nick,
                channel=channel,
                host=host,
                port=port,
                log=log,
                botInterface=botInterface,
            )
            while True:
                try:
                    n()
                    sleep(tick)
                except n.BadBot:
                    raise
                except n.ReBoot:
                    raise ReBoot
                except n.CopyOver:
                    log("*** COPYOVER: %s\n" % (datetime.datetime.now()))
                    save = savestate(n.__dict__)
                    try:  # try to keep User instances consistent
                        users = sys.modules["winbot"].User.users
                    except Exception:
                        users = []
                    try:
                        copyover()
                        n = fullmoon.Narrator()
                        n.__dict__ = loadstate(save)
                    except Exception:
                        n.say("Could not copyover: new code sucks.")
                        log(
                            "*** 1D10T: %s\n%s\n"
                            % (datetime.datetime.now(), traceback.format_exc())
                        )
                except Exception:
                    n.say("An exception was thrown. Please check '!ping'.")
                    log(
                        "*** ERROR: %s\n%s\n"
                        % (datetime.datetime.now(), traceback.format_exc())
                    )
        except ReBoot:
            n.s.close()
            del n
            sleep(5)
            log("*** REBOOT: %s\n" % (datetime.datetime.now()))
        except Exception:
            log(
                "*** FAIL: %s\n%s\n" % (datetime.datetime.now(), traceback.format_exc())
            )
            try:
                n.s.close()
            except Exception:
                pass
            sleep(20)
