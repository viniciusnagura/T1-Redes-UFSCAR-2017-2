#!/usr/bin/env python
import socket
import sys
import binascii
import subprocess
import thread

# -------------------------------------------
#      F U N C O E S   A U X I L I A R E S   |
# -------------------------------------------

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
		Options = ''
	return (Versao, IHL, TypeOfService, TotalLength, Identification, Flags,\
			FragmentOffset, TimeToLive, Protocol, HeaderChecksum, SourceAddress,\
			DestinationAddress, Options)

def executa_comando(tupla_pacote):

	# Identifica o comando da tupla
	if (tupla_pacote[8] == 1):
		comando = 'ps'
	elif (tupla_pacote[8] == 2):
		comando = 'df'
	elif (tupla_pacote[8] == 3):
		comando = 'finger'
	elif (tupla_pacote[8] == 4):
		comando = 'uptime'

	# Identifica o parametro (options) da tupla e o valida
	# (nao pode ser '|', ';' e '>')
	parametro = tupla_pacote[12]
	if(parametro == '|' or parametro == ';' or parametro == '>'):
		output = 'Comando \'' + comando + '\' com parametro \'' + parametro + '\' ilegal!'
		return output

	# Executa o comando e retorna o output
	while True:
		try:
			output = subprocess.check_output([comando, parametro], stderr=subprocess.STDOUT, shell=True)
			break
		except ValueError:
			output = 'Comando invalido!'
	return output

# Thread que executa os comandos passados para o Daemon
def thread_comando(conn):
	while 1:
	    data = conn.recv(BUFFER_SIZE)
	    if not data: break
	    print "Output:"
	    print executa_comando(desmonta_pacote_comando(data))
	    conn.send(data)
	conn.close()

# -------------------------------------------
#                  M A I N                   |
# -------------------------------------------

# Passagem da porta do Daemon como argumento
if len(sys.argv) < 2:
	print("Necessario passar a porta do Daemon")
	sys.exit(1)

TCP_IP = '127.0.0.1'
TCP_PORT = int(sys.argv[1])

BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

while 1:
	conn, addr = s.accept()
	print 'Connection address:', addr

	# Threads para multiplos comandos
	thread.start_new_thread(thread_comando, (conn,))