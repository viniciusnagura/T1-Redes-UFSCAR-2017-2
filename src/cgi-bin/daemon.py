#!/usr/bin/env python
import socket
import sys

# Passagem da porta do Daemon como argumento
if len(sys.argv) < 2:
	print("Necessario passar a porta do Daemon")
	sys.exit(1)

TCP_IP = '127.0.0.1'
TCP_PORT = int(sys.argv[1])

while 1:
	BUFFER_SIZE = 2048

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((TCP_IP, TCP_PORT))
	s.listen(1)

	conn, addr = s.accept()
	print 'Connection address:', addr
	while 1:
	    data = conn.recv(BUFFER_SIZE)
	    if not data: break
	    print "received data:", data
	    conn.send(data)
	conn.close()