import lolbot, socket, pickle, base64, select
from time import sleep

def decode( m ):
    return pickle.loads( base64.b64decode( m ) )

class POCBot( lolbot.Bot ):
    def init( self ):
        self.s.send( "JOIN #failmoon\r\n" )
        self.sock = socket.socket( socket.AF_UNIX )
        self.sock.connect( "fullmoon.sock" )
        self.sock.send( "POCBot4563465\r\n" )
        print "waiting for response"
        rsp = decode( self.sock.recv(100) )
        if not rsp[0]:
            print rsp[1]
            exit()
        print "My name is %s" % rsp[1]
        sleep(0.1)
        self.s.send( "PRIVMSG mayonaise :!bot POCBot4563465\r\n" )
        print "running"
    
    def loop( self ):
        r,w,x = select.select( [self.sock], [], [], 1 )
        if r:
            m = decode( self.sock.recv(1024) )
            print m
            if m[0] == "botsay":
                self.s.send( "PRIVMSG #failmoon :%s says '%s'\r\n" % (m[1], m[2]) )

b = POCBot( "Fred", "localhost" )
while True:
    b()
    sleep(0.5)
