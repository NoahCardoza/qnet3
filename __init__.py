import socket
import select

class Connector:
    def __init__(self,sock,addr):
        self.sock = sock
        self.addr = addr

        self.write_queue = ''
        self.read_queue = ''
        self.current_message = ''

    def update_queues(self):
        for item in self.read_queue:
            if item == '\n':
                if self.message(self.current_message.replace('\\\\','\\').replace('\\n','\n')):
                    return True
                self.current_message = ''
            else:
                self.current_message += item
        self.read_queue = ''
        if self.write_queue:
            try: self.write_queue = self.write_queue[self.sock.send(self.write_queue.encode(encoding='utf-8', errors='strict')):]
            except socket.error: return True

    def message(self,msg):
        print('Received message from ['+self.addr[0]+':'+str(self.addr[1])+']')
        print(msg)
        self.respond('ok')

    def respond(self,msg):
        self.write_queue += msg + '\n'

    def update(self):
        ret = True
        try:
            to_read,to_write,in_err = select.select([self.sock],[self.sock],[self.sock])
        except:
            to_read,to_write,in_err = [[],[],[]]
            ret = False


        if to_read and not in_err:
            try: self.read_queue += self.sock.recv(4096).decode(encoding='utf-8', errors='strict')
            except socket.error:
                return False
        if in_err:
            ret = False

        if not in_err:
            if self.update_queues():
                return False
        return ret

class Server:
    def __init__(self,host,port,connector):
        self.host = host
        self.port = port

        self.connections = []
        self.connector = connector

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(0)
        self.sock.bind((host,port))
        self.sock.listen(5)

    def update(self):
        for _ in range(len(self.connections)):
            c = self.connections.pop(0)
            if c.update():
                self.connections.append(c)
            else:
                print('[SERVER] Connection to',c.addr,'terminated.')

        try:
            (sock, addr) = self.sock.accept()
            #self.connections.append(self.connector(sock,addr))
        except socket.error:
            return

        self.connections.append(self.connector(sock,addr))


class Connection:
    def __init__(self,host,port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.connect((host,port))

    def converse(self,msg):
        msg = msg.replace('\\','\\\\').replace('\n','\\n') + '\n'
        while msg:
            msg = msg[self.sock.send(msg.encode(encoding='utf-8', errors='strict')):]
        response = ''
        while True:
            d = self.sock.recv(4096).decode(encoding='utf-8', errors='strict')
            if not d:
                raise ValueError('Connection broken; no longer receiving')
            response += d
            if response.endswith('\n'):
                return response[:-1].replace('\\n','\n').replace('\\\\','\\')


if __name__ == '__main__':
    host = input('Host: ')
    port = int(input('Port: '))
    connection = Connection(host,port)
    print(connection.converse('who'))
    print(connection.converse('motd'))
    while True:
        print(connection.converse(input('> ')))
