import socket
import time

TCP_IP = '10.211.55.9'
TCP_PORT = 2001
BUFFER_SIZE = 1024
MESSAGE="Hello, World!\r\n"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
count = 0
while 1:
    count = count + 1
    s.send(str(count) + MESSAGE)
    print "sent"
    time.sleep(.1)
    data = s.recv(1024)
    print "dude", data
