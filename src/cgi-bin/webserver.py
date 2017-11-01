#!/usr/bin/env python
import cgi
import cgitb
import os
import socket

cgitb.enable()

# -------------------------------------------
#      F U N C O E S   A U X I L I A R E S   |
# -------------------------------------------

def le_parametros_html():

	# Efetua a leitura dos parametros passados pelo HTML, retornando uma lista de comandos
	# no seguinte formato: (nro_maquina, nro_comando, argumento_comando)
	#	nro_comando:
	#		1 - ps
	#		2 - df
	#		3 - finger
	#		4 - uptime

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


# -------------------------------------------
#                  M A I N                   |
# -------------------------------------------

print "Content-type: text/html\r\n\r\n";
print "<font size=+1>Environment</font></br>";

print "<pre>"

# Recebe os comandos a serem passados para as maquinas
lista_comandos = le_parametros_html()

# Mostra os comandos identificados na tela
for x in lista_comandos:
	print x
	print "<br>"


# TESTANDO SOCKET
# Exemplo retirado de:
# 	https://wiki.python.org/moin/TcpCommunication
TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 1024
MESSAGE = "Hello, World!"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(MESSAGE)
data = s.recv(BUFFER_SIZE)
s.close()

print "received data:", data

print "</pre>"

