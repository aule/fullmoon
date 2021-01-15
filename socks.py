"""
Handle connections to a UNIX socket for sending data to bots

Author: Joe Taylor
Date: 1st June 2010
"""

import socket, pickle, base64, threading, time, os

class DummySockPuppet(object):
    def send( self, msg, target=None ):
        pass
    def register( self, lookup, target ):
        return False
    path = "!!!!! Dummy Sock Puppet"

class SockPuppet(object):
    def __init__( self, socketpath ):
        self.l = socket.socket( socket.AF_UNIX )
        try: 
            os.unlink( socketpath )
        except OSError:
            pass
        self.l.bind( socketpath )
        self.l.listen( 2 )
        self.l.settimeout( 0.01 )
        self.thread = threading.Thread( target=self.accept_loop )
        self.thread.daemon = True
        self.thread.start()
        self.connections = {}
        self.registers = {}
        if socketpath[0] == os.sep:
            self.path = socketpath
        else:
            self.path = os.path.join( os.getcwd(), socketpath )

    def encode( self, msg ):
        return "%s\n" % base64.b64encode( pickle.dumps( msg ) )

    def accept_loop( self ):
        while True:
            try:
                conn, addr = self.l.accept()
                self.connect( conn )
            except socket.timeout:
                time.sleep( 1 )

    def connect( self, c ):
        "Obtain a name for the connection and list it"
        c.settimeout( 5 )
        try:
            name = c.recv( 50 ).strip()
        except socket.timeout:
            try:
                c.send( self.encode( (False,"Error: timeout") ) )
                c.close()
            except Exception:
                pass
            return
        except Exception:
            try:
                c.send( self.encode( (False,"Error: exception") ) )
                c.close()
            except Exception:
                pass
            return
        if name in self.connections.keys():
            try:
                self.connections[name].send("")
                try:
                    c.send( self.encode( (False,name) ) )
                    c.close() # live connection already goes by this name
                except Exception:
                    pass # have to make sure the return is sent
                return
            except socket.error:
                pass # existing socket died. overwrite it.
        self.connections[name] = c
        self.send((True,name),name);

    def send( self, msg, target=None ):
        print "SEND to %s: %s" % (target, msg )
        data = self.encode( msg )
        if not target:
            for n,c in self.connections.items():
                try:
                    c.send( data )
                except Exception:
                    del self.connections[n];
        elif type(target) in [list,tuple]:
            for t in target:
                self.send( msg, t )
        else:
            try:
                self.registers[target].send( data )
            except KeyError:
                try:
                    self.connections[target].send( data )
                except KeyError:
                    pass
                except Exception:
                    del self.connections[target]
            except Exception:
                del self.registers[target]

    def register( self, lookup, target ):
        try:
            self.registers[lookup] = self.connections[target]
        except KeyError:
            return False
        return True
