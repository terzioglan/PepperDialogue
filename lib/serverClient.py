# python 2 and 3
import json, socket, time

class Server(object):
    def __init__(self, host, port, size):
        self.host = host
        self.port = port
        self.size = size
        self.sct = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sct.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.sct.bind((host, port))
        self.sct.listen(1)
        self.conn, self.addr = self.sct.accept()
    
    def send(self, message):
        data = json.dumps(message)
        self.conn.sendall(data.encode('utf-8'))
    
    def receive(self,size):
        data = self.conn.recv(size).decode('utf-8')
        return json.loads(data)
    
    def exit(self,):
        self.conn.close()
        self.sct.shutdown(socket.SHUT_RDWR)
        self.sct.close()


class Client(object):
    def __init__(self, host, port, size):
        self.host = host
        self.port = port
        self.size = size
        self.sct = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        while not self.connected:
            try:
                self.sct.connect((host, port))
            except Exception as e:
                print(e)
                time.sleep(1.0)
            else:
                self.connected = True
    
    def receive(self,):
        data =  self.sct.recv(self.size).decode('utf-8')
        return json.loads(data)
    
    def send(self, message):
        data = json.dumps(message)
        self.sct.sendall(data.encode('utf-8'))

    def exit(self,):
        self.sct.shutdown(socket.SHUT_RDWR)
        self.sct.close()
