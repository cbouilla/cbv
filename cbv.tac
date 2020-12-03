from twisted.conch.telnet import TelnetTransport, TelnetProtocol, Telnet, IP
from twisted.internet import protocol, reactor
from twisted.application.internet import TCPServer
from twisted.application.service import Application
from twisted.internet.error import ProcessExitedAlready
from twisted.application import strports

class UmixPipeProtocol(protocol.ProcessProtocol):
    def __init__(self, net_proto):
        self.net = net_proto

    def connection_made(self):
        self.net.transport.write(b'VM started. UMIX booting...\n')
        self.net.transport.write(b"-------------------------------\n")

    def outReceived(self, data):
        self.net.transport.write(data)

    def processEnded(self, reason):
        self.net.transport.write(b"-------------------------------\n")
        self.net.transport.write(b"VM stopped. Closing connection.\n")
        self.net.transport.loseConnection()


class UmixNetProtocol(TelnetProtocol):
    def connectionMade(self):
        self.transport.write(b'Starting up VM. Please wait...\n')
        process_proto = UmixPipeProtocol(self)
        self.process = reactor.spawnProcess(process_proto, './short_freelist', args=['./short_freelist', 'codex.um'])
    
    def dataReceived(self, data):
        self.process.write(data)

    def unhandledCommand(self, cmd, pouet):
        # called when the client does CTRL+C
        if cmd == IP:
            self.transport.loseConnection()

    def connectionLost(self, reason):
        try:
            self.process.signalProcess('KILL')
        except ProcessExitedAlready:
            pass


factory = protocol.ServerFactory()
factory.protocol = lambda: TelnetTransport(UmixNetProtocol)
service = strports.service('systemd:domain=INET:index=0', factory)  # switch to tcp:port=23 if not using systemd

application = Application("CBV application")
service.setServiceParent(application)
