#!/usr/bin/env python
import cgi
import cgitb
import os
import socket
import math

cgitb.enable()

# -------------------------------------------
#      F U N C O E S   A U X I L I A R E S   |
# -------------------------------------------

def le_parametros_html():
	'''
	Efetua a leitura dos parametros passados pelo HTML, retornando uma lista de comandos
	no seguinte formato: (nro_maquina, nro_comando, argumento_comando)
		nro_comando:
			1 - ps
			2 - df
			3 - finger
			4 - uptime
	'''

	# Leitura dos parametros do HTML 
	parametros_html = cgi.FieldStorage()

	# Tuplas de comandos passados pelo HTML
	tuplas_html = []
	for parametro in parametros_html:
		if(parametro[0:3] == 'maq'):
			if(parametro[4] == '_'):
				tuplas_html.append((parametro[3],parametro[5:len(parametro)], ''))
			else:
				tuplas_html.append((parametro[3],parametro[5:len(parametro)], parametros_html[parametro].value))

	# Validacao das tuplas de comandos (duplicata de comandos e consistencia de checkbox)
	tuplas_validadas = []
	for comando in ('ps', 'df', 'finger', 'uptime'):
		for i in ('1','2','3'):
			tupla_sem_argumento = None
			tupla_com_argumento = None
			for tupla in tuplas_html:
				if(tupla[0] == i and tupla[1] == comando):
					if(tupla[2] == ''):
						tupla_sem_argumento = tupla
					else:
						tupla_com_argumento = tupla
			if tupla_sem_argumento is not None:
				if tupla_com_argumento is not None:
					tuplas_validadas.append(tupla_com_argumento)
				else:
					tuplas_validadas.append(tupla_sem_argumento)

	# Conversao dos comandos ps, df, finger e uptime nos numeros 1, 2, 3 e 4, respectivamente
	tuplas_finais = []
	for tupla in tuplas_validadas:
		if(tupla[1] == 'ps'):
			tuplas_finais.append((int(tupla[0]), 1, tupla[2]))
		elif (tupla[1] == 'df'):
			tuplas_finais.append((int(tupla[0]), 2, tupla[2]))
		elif (tupla[1] == 'finger'):
			tuplas_finais.append((int(tupla[0]), 3, tupla[2]))
		elif (tupla[1] == 'uptime'):
			tuplas_finais.append((int(tupla[0]), 4, tupla[2]))

	return tuplas_finais

def monta_pacote_comando(tupla_comando, id, ip_origem, ip_destino):

	# Version: 2
	Version = '0010'

	# IHL: vai ser calculado abaixo!
	IHL = '0000'

	#Type of Service: 0
	TypeOfService = '00000000'

	# Total Length: vai ser calculado abaixo!
	TotalLength = '0000000000000000'

	# Identification: posicao do comando na lista de comandos
	Identification = "{0:{fill}16b}".format(id, fill='0')

	# Flags: 000 (Requisicao)
	Flags = '000'

	# Fragment Offset: 0
	FragmentOffset = '0000000000000'

	# Time to Live: Pode ser qualquer valor	
	TimeToLive = '10000000'	

	# Protocol: depende do comando passado (ps, df, finger, uptime)
	Protocol = "{0:{fill}8b}".format(tupla_comando[1], fill='0')

	# Header Checksum: PRECISO FAZER (NAO ENTENDI O QUE EH PRA SER FEITO)!!!
	HeaderChecksum = '0000000000000000'

	# Source Address: 		
	SourceAddress = ''.join([bin(int(x)+256)[3:] for x in ip_origem.split('.')])

	# Destination Address: 
	DestinationAddress = ''.join([bin(int(x)+256)[3:] for x in ip_destino.split('.')])

	# Options: de acordo com o comando passado (pode ser vazio)
	Options = ''.join('{0:08b}'.format(ord(x), 'b') for x in tupla_comando[2])

	# Tamanho do pacote completo. Usado para calcular TotalLength e IHL corretamente
	tamanho_pacote = len(Version + IHL + TypeOfService + TotalLength + Identification + Flags \
						+ FragmentOffset + TimeToLive + Protocol + HeaderChecksum + SourceAddress \
						+ DestinationAddress + Options)

	# Numero de words de 32-bits necessario para o pacote
	numero_words_necessario = int(math.ceil(float(tamanho_pacote) / 32.0))

	# Atualizacao de IHL
	IHL = "{0:{fill}4b}".format(numero_words_necessario, fill='0')

	# Atualizacao de TotalLength
	TotalLength = "{0:{fill}16b}".format(numero_words_necessario * 32, fill='0')

	pacote_pronto = (Version + IHL + TypeOfService + TotalLength + Identification + Flags \
					+ FragmentOffset + TimeToLive + Protocol + HeaderChecksum + SourceAddress \
					+ DestinationAddress + Options).ljust(numero_words_necessario * 32, '0')

	return pacote_pronto


# -------------------------------------------
#                  M A I N                   |
# -------------------------------------------

print "Content-type: text/html\r\n\r\n";
print "<font size=+1>Environment</font></br>";

print "<pre>"

TCP_IP = '127.0.0.1'
TCP_PORT_BASE = 8000
BUFFER_SIZE = 1024
MESSAGE = "Hello, World!"

# Recebe os comandos a serem passados para as maquinas
lista_comandos = le_parametros_html()

for comando in lista_comandos:
	DAEMON_PORT = TCP_PORT_BASE + comando[0]
	pacote = monta_pacote_comando(comando, lista_comandos.index(comando), TCP_IP, TCP_IP)
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((TCP_IP, DAEMON_PORT))
		s.send(pacote)
		data = s.recv(BUFFER_SIZE)
		#s.close()
		print "Received data:", data, "from Daemon", comando[0]
	finally:
		# Fecha a conexao
		s.close()

print "</pre>"

