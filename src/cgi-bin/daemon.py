#!/usr/bin/env python
import socket
import sys
import binascii

def desmonta_pacote_comando(pacote):
	Versao = pacote[0:4]
	IHL = pacote[4:8]
	TypeOfService = pacote[8:16]
	TotalLength = pacote[16:32]
	Identification = pacote[32:48]
	Flags = pacote[48:51]
	FragmentOffset = pacote[51:64]
	TimeToLive = pacote[64:72]
	Protocol = int(pacote[72:80], 2)
	HeaderChecksum = pacote[80:96]
	SourceAddress = pacote[96:128]
	DestinationAddress = pacote[128:160]
	if (int(IHL, 2) > 5):
		Options = binascii.unhexlify('%x' % int(pacote[160:int(TotalLength, 2)], 2)).replace('\x00', '')
	else:
		Options = None
	return (Versao, IHL, TypeOfService, TotalLength, Identification, Flags,\
			FragmentOffset, TimeToLive, Protocol, HeaderChecksum, SourceAddress,\
			DestinationAddress, Options)

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
	    print "received data:", desmonta_pacote_comando(data)
	    conn.send(data)
	conn.close()