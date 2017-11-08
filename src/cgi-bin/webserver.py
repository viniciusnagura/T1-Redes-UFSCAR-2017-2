#!/usr/bin/env python
import cgi
import cgitb
import os
import socket
import math

# -------------------------------------------
#           C O N F I G U R A C O E S        |
# -------------------------------------------

cgitb.enable()
TCP_IP = '127.0.0.1'
TCP_PORT_BASE = 8000
BUFFER_SIZE = 1024

# -------------------------------------------
#      F U N C O E S   A U X I L I A R E S   |
# -------------------------------------------

# Dicionarios para conversao dos comandos
dic_comando_str_para_int = {'ps' : 1, 'df' : 2, 'finger' : 3, 'uptime' : 4}
dic_comando_int_para_str = {1 : 'ps', 2 : 'df', 3 : 'finger', 4 : 'uptime'}

# Leitura dos parametros enviados pelo HTML
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
		tuplas_finais.append((int(tupla[0]), dic_comando_str_para_int[tupla[1]], tupla[2]))

	return tuplas_finais

# Montagem do pacote de requisicao
def monta_pacote_comando(tupla_comando, id, ip_origem, ip_destino):
	'''
	Monta um pacote de acordo com o comando solicitado, concatenando cada campo do cabecalho
	em uma string de binarios. Nota-se que nesse pacote nao ha um campo de dados!
	'''
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
	# Source Address: passado como parametro	
	SourceAddress = ''.join([bin(int(x)+256)[3:] for x in ip_origem.split('.')])
	# Destination Address: passado como parametro
	DestinationAddress = ''.join([bin(int(x)+256)[3:] for x in ip_destino.split('.')])
	# Options: de acordo com o comando passado (pode ser vazio, caso nao haja argumento)
	Options = ''.join('{0:08b}'.format(ord(x), 'b') for x in tupla_comando[2])
	# Tamanho do pacote completo. Usado para calcular TotalLength e IHL corretamente
	tamanho_pacote = len(Version + IHL + TypeOfService + TotalLength + Identification + Flags \
						+ FragmentOffset + TimeToLive + Protocol + HeaderChecksum + SourceAddress \
						+ DestinationAddress + Options)
	# Numero de words de 32-bits necessario para o pacote (usado no IHL)
	numero_words_necessario = int(math.ceil(float(tamanho_pacote) / 32.0))
	# Atualizacao de IHL
	IHL = "{0:{fill}4b}".format(numero_words_necessario, fill='0')
	# Atualizacao de TotalLength
	TotalLength = "{0:{fill}16b}".format(numero_words_necessario * 32, fill='0')
	# Montagem do pacote ja com padding
	pacote_pronto = (Version + IHL + TypeOfService + TotalLength + Identification + Flags \
					+ FragmentOffset + TimeToLive + Protocol + HeaderChecksum + SourceAddress \
					+ DestinationAddress + Options).ljust(numero_words_necessario * 32, '0')
	return pacote_pronto

# Desmontagem do pacote de resposta, enviado pelo daemon
def desmonta_pacote_resposta(pacote):
	'''
	Desmonta o pacote de resposta, retornando uma tupla com os campos. 
	Nota-se que nesse pacote HA SIM um campo de dados (contem o output)!
	'''
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
	Data = ''.join(chr(int(pacote[160:][i:i+8], 2)) for i in xrange(0, len(pacote[160:]), 8))
	return (Versao, IHL, TypeOfService, TotalLength, Identification, Flags,\
			FragmentOffset, TimeToLive, Protocol, HeaderChecksum, SourceAddress,\
			DestinationAddress, Data)


# -------------------------------------------
#                  M A I N                   |
# -------------------------------------------

print "Content-type: text/html\r\n\r\n";
print "<pre>"

# Botao para index.html
print "<input type=\"button\" onclick=\"location.href=\'../index.html\'\" value=\"Retornar\" style=\"display: block; margin: 0 auto;\">"

# Recebe os comandos a serem passados para as maquinas
lista_comandos = le_parametros_html()

# Alocacao de uma lista de strings para retorno dos outputs
outputs_daemon = ["\n<h3>MACHINE 1:</h3>", \
					"\n<h3>MACHINE 2:</h3>", \
					"\n<h3>MACHINE 3:</h3>"]

# Para cada comando que foi recebido do HTML:
for comando in lista_comandos:
	
	# Identifica a porta
	DAEMON_PORT = TCP_PORT_BASE + comando[0]

	# Monta o pacote a ser enviado
	pacote = monta_pacote_comando(comando, lista_comandos.index(comando), TCP_IP, TCP_IP)
	
	try:
		# Tenta enviar o pacote
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((TCP_IP, DAEMON_PORT))
		s.send(pacote)

		# Em seguida, aguarda OS PACOTES DE RESPOSTA (mais de 1, normalmente)
		while True:
			data = s.recv(BUFFER_SIZE)
			if not data:
				break
			else:
				# Recebe um dos pacotes de resposta e o desmonta
				pacote_resposta = desmonta_pacote_resposta(data)
				# Verifica se o pacote eh de resposta
				if(pacote_resposta[5] == '111'):
					# Se for, concatena a string de respostacom as respostas ja recebidas
					outputs_daemon[comando[0] - 1]+=(pacote_resposta[12])
	finally:
		# Fecha a conexao
		s.close()

# Imprime os outputs na pagina HTML
for output in outputs_daemon:
	print output

print "</pre>"

