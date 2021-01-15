"""
Extention to the lolbot class to add:
* User class - for consistency across nick changes
* Command class - for structured handling of commands
* Shell - for complete debugging control
* Timer class - for calling functions after a certain interval
* say - Throttled messaging function
* say_list - Sending to a list of targets
* set_topic - Sets the current topic

Important notes:
* You must set self.channel
* A log function must be defined
* To use shell or mod, you have to register the commands:
        Command( '^!mod (?P<pwd>\S+)$', Bot.cmd_mod_login ),
        Command( '^!shell$', Bot.cmd_shell ),
* The User class has issues with copyover
* shell_env must be defined to return the globals (or other env) for shell

Author: Joe Taylor
Date: 1st June 2010 5:35AM
"""

import lolbot, re, time, traceback, datetime, sys
from time import sleep

# A little hack to get python to take the prexisting users if it loads this twice (continued below)
try:
    users_list = sys.modules['winbot'].User.users
except Exception:
    users_list = []

class User( object ):
    """
        This class, combined with some lolbot handlers, keeps track
        of changing usernames. When an instance of User is created,
        it will return a globally unique instance that will be
        updated automatically.
    """
    users = users_list # list of users being tracked
    def __new__( cls, nick ):
        u = cls.get( nick )
        if u: # return prexisting instance if it exists
            return u
        else: # else make a new one
            u = object.__new__( cls )
            u.__init__( nick )
            cls.users.append(u) # add to the list of existing instances
            return u
    def __init__( self, nick ):
        self.nick = str(nick)
    def __cmp__( self, nick ):
        return cmp( self.nick.lower(), str(nick).lower() )
    def __str__( self ):
        return self.nick
    def __add__( self, other ):
        return self.nick + str(other)
    def __radd__( self, other ):
        return str(other) + self.nick
    def __repr__( self ):
        return str(self)
    def change( self, nick ):
        self.nick = nick;
    @classmethod
    def copyover( cls, users ):
        """During copyover, the list of existing User instances is overwritten.
        Calling this function for all known instances after copyover will put them back"""
        cls.users = users
    @classmethod
    def get( cls, nick ):
        "returns existing instance for $nick, or None if it doesn't exist"
        if nick in cls.users: # return prexisting instance if it exists
            return [u for u in cls.users if u==nick][0]
        return None
    def isolate( self ):
        """Used for exporting a link to the user for pickle links. ask staircase."""

        class UserProtector(object):
            def __reduce__(self):
                return (User,(str(self.user),));
            def __init__(self,user):
                self.user=user;
        return UserProtector( self )

# solve class version issues
for u in users_list:
    u.__class__ = User

class Command( object ):
    """
        This class simplifies and structures command matching
        On creation, a regular expression must be provided to
        specify the command syntax and parameter names, along
        with the python function to be called. If called, the
        parameters are sent as keyword variables.
    """
    name_re = re.compile( "!(\w+)" )
    def __init__( self, regex, cmd, name=None ):
        if regex[-1] == "$": # add crude support for comments
            regex = regex[:-1] + "\s*(\#.*)?$"
        self.regex = re.compile( regex )
        self.cmd = cmd
        self.match = None
        self.name = name
        if not name:
            m = self.name_re.search( regex )
            if m:
                self.name = m.group(1)
    def __call__( self, s, user ):
        try:
            return self.cmd( s, user, **self.match.groupdict() )
        except Exception, e:
            raise
            return None
    def __cmp__( self, cmd ):
        self.match = self.regex.match( cmd )
        if self.match:
            return 0
        return -1

class Timer( object ):
    def __init__( self, delay, fn ):
        self.fn = fn
        self.time = time.time()+float(delay)
    def __gt__( self, other ):
        return self.time > other
    def __lt__( self, other ):
        return self.time < other
    def __cmp__( self, other ):
        return cmp( self.time, other)
    def __call__( self ):
        self.fn()
    def clear( self ):
        "Cancel the timer"
        self.fn = lambda: None
        self.time = time.time()

class Bot( lolbot.Bot ):
    """
        Extended lolbot class to install event handlers for the
        helper classes defined above.
    """

    SHELL = False # set to True to enable shell
    MOD_PWD = None # needed to login as moderatior

    # command listings
    cmds_global = []
    cmds_public = []
    cmds_private = []

    def __init__( self, *args, **kwargs ):
        lolbot.Bot.__init__( self, *args, **kwargs )
        self.timers = []
        self.named_timers = {}
        self.shell = None
        self.mod = None
        self.throttle_data = []
        self.topic = ""

    def loop( self ):
        while len(self.timers) and time.time() > self.timers[0]:
            self.timers.pop(0)()

    def add_timer( self, delay, fn ):
        "Call a function after a delay in seconds. Returns Timer instance."
        timer = Timer( delay, fn )
        self.timers.append( timer )
        self.timers.sort()
        return timer

    def set_timer( self, delay, fn, tag="main" ):
        "Overwrites a named timer (main by default)"
        self.clear_timer( tag )
        self.named_timers[tag] = self.add_timer( delay, fn )

    def check_timer( self, tag="main" ):
        "Check if a named timer is still ticking"
        if tag in self.named_timers:
            return time.time() < self.named_timers[tag]
        return False

    def clear_timer( self, tag="main" ):
        try:
            self.named_timers[tag].clear()
        except Exception:
            pass # if the timer can't be cleared, it doesn't need to be

    def NICK( self, tail, user, **spare ):
        # user will be the old nick, tail is the new nick
        # If the new nick already exists, let them be
        if user in User.users and tail not in User.users:
            User.get(user).change(tail)

    def PRIVMSG( self, params, tail, user, **spare ):
        if self.shell != None and user == self.mod:
            if params[0][0] != "#":
                return self.Shell( tail )
        if tail[0] != "!": return
        def runcmd( cmds ):
            try:
                cmds[ cmds.index( tail ) ](self, User(user) )
            except ValueError:
                pass #not a command
        runcmd( self.cmds_global )
        if params[0][0] != "#":
            runcmd( self.cmds_private )
        elif params[0] == self.channel:
            runcmd( self.cmds_public )

    def TOPIC( self, tail, **spare ):
        self.topic = tail

    def set_topic( self, topic ):
        if self.topic != topic:
            self.s.send( "TOPIC %s :%s\r\n" % (self.channel,topic) )

    def log( self, msg ):
        "Dummy log, should one not be defined"
        print "Log: %s" %msg
    def shell_env( self ):
        return globals()
    def Shell( self, code ):
        if not self.SHELL:
            self.shell = None
            return
        if code in ["?","??"]:
            self.log( "*** SHELL-QUERY: %s\nby %s\n%s\n" % (datetime.datetime.now(),self.mod,self.shell) )
            try:
                r = eval( self.shell, self.shell_env(), {'self':self} )
                for line in str(r).splitlines():
                    self.say( "> %s" % line, self.mod )
            except Exception, e:
                self.say( "Error: %s" % e, self.mod )
                self.log( "*** PEBKAC: %s\n%s\n" % (datetime.datetime.now(),traceback.format_exc()) )
        if code in ["!","!!"]:
            self.log( "*** SHELL-EXEC: %s\nby %s\n%s\n" % (datetime.datetime.now(),self.mod,self.shell) )
            try:
                exec self.shell in self.shell_env(), {'self':self}
                self.say( "Done", self.mod )
            except Exception, e:
                self.say( "Error: %s" % e, self.mod )
                self.log( "*** PEBKAC: %s\n%s\n" % (datetime.datetime.now(),traceback.format_exc()) )
        if code in ["!!","??",".."]:
            self.shell = ""
            self.say( "Ready for new input", self.mod )
        elif code in ["!","?","."]:
            self.shell = None
        else:
            self.shell += code + "\n"

    def throttle( self, msg ):
        size = len(msg)
        self.throttle_data.append( (size, time.time()+2*len(self.throttle_data) ) )
        while True:
            while self.throttle_data and self.throttle_data[0][1] < time.time():
                self.throttle_data = self.throttle_data[1:]
            if sum( [d[0] for d in self.throttle_data] ) < 150:
                return
            sleep( 0.1 )

    def say( self, message, target=None ):
        if not target:
            target = self.channel
        self.throttle( message )
        self.s.send( "NOTICE %s :%s\r\n" % (target, message) )

    def say_list( self, message, l ):
        for target in l:
            self.say( message, target )

    def cmd_mod_login( self, user, pwd ):
        if pwd == self.MOD_PWD:
            if self.mod:
                self.say( "Mod has switched to %s" % user, self.mod )
            self.mod = user
            self.say( "You are now the mod", user )

    def cmd_shell( self, user ):
        if user == self.mod:
            if not self.SHELL:
                self.say( "Shell is disabled.", user )
                return
            self.shell = ""
            self.say( "Shell mode started. Enter ! or ? on a new line to terminate, !! or ?? to terminate then repeat. Period to abort.", user )
