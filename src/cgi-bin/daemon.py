#!/usr/bin/env python
import socket
import sys
import binascii
import subprocess
import thread
import math

# -------------------------------------------
#           C O N F I G U R A C O E S        |
# -------------------------------------------

TCP_IP = '127.0.0.1'
# Passagem da porta do Daemon como argumento
if len(sys.argv) < 2:
	print("Necessario passar a porta do Daemon")
	sys.exit(1)
else:
	TCP_PORT = int(sys.argv[1])
BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

# -------------------------------------------
#      F U N C O E S   A U X I L I A R E S   |
# -------------------------------------------

# Dicionarios para conversao dos comandos
dic_comando_str_para_int = {'ps' : 1, 'df' : 2, 'finger' : 3, 'uptime' : 4}
dic_comando_int_para_str = {1 : 'ps', 2 : 'df', 3 : 'finger', 4 : 'uptime'}

# Funcao que calcula o Checksum de um pacote, baseado no conteudo em:
# https://www.codeproject.com/Tips/460867/Python-Implementation-of-IP-Checksum
def checksum(header):
	tamanho = 0
	lista_duplo_bytes = []
	for i in range(0, len(header), 2):
		lista_duplo_bytes.append(header[i:i+2])
		tamanho += 1
	checksum = 0
	pointer = 0
	while tamanho > 1:
		checksum += int((lista_duplo_bytes[pointer] + lista_duplo_bytes[pointer + 1]), 16)
		tamanho -= 2
		pointer += 2
	if tamanho:
		checksum += lista_duplo_bytes[pointer]
	checksum = (checksum >> 16) + (checksum & 0xffff)
	checksum += (checksum >>16)
	return "{0:{fill}16b}".format(int((~checksum) & 0xFFFF), fill='0')

# Funcao que compara checksum
def valida_checksum(pacote_desmontado):
	'''
	Recebe um pacote DESMONTADO e verifica se a validade do Header Checksum
	'''
	# Pega o campo de checksum
	checksum_recebido = pacote_desmontado[9]
	# Monta um pacote cujo campo HeaderChecksum esta zerado ('0000000000000000')
	checksum_zerado = pacote_desmontado[13][0:80] + '0000000000000000' + pacote_desmontado[13][96:]
	# Calcula o checksum do pacote acim
	checksum_calculado = checksum(checksum_zerado)
	# Por fim, valida se sao iguais ou nao
	if(checksum_recebido ==  checksum_calculado):
		return True
	else:
		return False

# Desmontagem do pacote de requisicao, enviado pelo webserver
def desmonta_pacote_comando(pacote):
	'''
	Desmonta o pacote de requisicao, retornando uma tupla com os campos. 
	Nota-se que nesse pacote NAO HA um campo de dados. Porem, pode conter
	um campo de Options (argumento do comando)!
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
	if (int(IHL, 2) > 5):
		Options = binascii.unhexlify('%x' % int(pacote[160:int(TotalLength, 2)], 2)).replace('\x00', '')
	else:
		Options = ''
	Cabecalho = pacote
	# Ultimo elemento eh o proprio cabecalho/pacote (util para conferir o checksum)
	return (Versao, IHL, TypeOfService, TotalLength, Identification, Flags,\
			FragmentOffset, TimeToLive, Protocol, HeaderChecksum, SourceAddress,\
			DestinationAddress, Options, Cabecalho)

# Executa um comando utilizando a biblioteca subprocess
def executa_comando(tupla_pacote):
	'''
	Executa um comando, retornando o seu output (pode ser um erro)
	'''
	# Identifica o comando da tupla
	comando = dic_comando_int_para_str[tupla_pacote[8]]

	# Identifica o parametro (options) da tupla e o valida
	# 	(nao pode ser '|', ';' e '>')
	parametro = tupla_pacote[12]
	if(parametro == '|' or parametro == ';' or parametro == '>'):
		output = 'Comando \'' + comando + '\' com parametro \'' + parametro + '\' ilegal!'
		return output

	# Se o parametro for valido, tenta executar o comando e retornar seu output
	while True:
		try:
			output = subprocess.check_output([(comando + ' ' + parametro),], stderr=subprocess.STDOUT, shell=True)
			break
		except subprocess.CalledProcessError as e:
			output = e.output
			break
	return output

# Montagem do pacote de resposta
def monta_pacote_resposta(resposta, id, ip_origem, ip_destino):
	'''
	Monta um pacote de resposta com o output do comando solicitado (mesmo cabecalho do pacote de
	requisicao). Entretanto, NAO HA um campo de Options, pois o output sera enviado como DATA!
	'''
	# Version: 2
	Version = '0010'
	# IHL: fixo em 5, pois nao ha campo de options na resposta!
	IHL = '0101'
	#Type of Service: 0
	TypeOfService = '00000000'
	# Total Length: vai ser calculado abaixo!
	TotalLength = '0000000000000000'
	# Identification: NO MOMENTO, QUALQUER VALOR (NO CASO, 0)
	Identification = "{0:{fill}16b}".format(id, fill='0')
	# Flags: 111 (Resposta)
	Flags = '111'
	# Fragment Offset: 0
	FragmentOffset = '0000000000000'
	# Time to Live: Pode ser qualquer valor	
	TimeToLive = '10000000'	
	# Protocol: vazio, pois se trata da resposta!
	Protocol = "{0:{fill}8b}".format(0, fill='0')
	# Header Checksum: vai ser calculado abaixo!
	HeaderChecksum = '0000000000000000'
	# Source Address: passado como parametro		
	SourceAddress = ip_origem
	# Destination Address: passado como parametro
	DestinationAddress = ip_destino
	#DATA: parte do output do comando executado
	Data = ''.join('{0:08b}'.format(ord(x), 'b') for x in resposta)
	# Tamanho do pacote completo. Usado para calcular TotalLength corretamente
	tamanho_pacote = len(Version + IHL + TypeOfService + TotalLength + Identification + Flags \
						+ FragmentOffset + TimeToLive + Protocol + HeaderChecksum + SourceAddress \
						+ DestinationAddress + Data)
	# Numero de words de 32-bits necessario para o pacote
	numero_words_necessario = int(math.ceil(float(tamanho_pacote) / 32.0))
	# Atualizacao de TotalLength
	TotalLength = "{0:{fill}16b}".format(numero_words_necessario * 32, fill='0')
	# Atualiza o campo Header Checksum
	HeaderChecksum = checksum((Version + IHL + TypeOfService + TotalLength + Identification + Flags \
								+ FragmentOffset + TimeToLive + Protocol + HeaderChecksum + SourceAddress \
								+ DestinationAddress).ljust(numero_words_necessario * 32, '0'))
	# Montagem do pacote ja com padding
	pacote_pronto = (Version + IHL + TypeOfService + TotalLength + Identification + Flags \
					+ FragmentOffset + TimeToLive + Protocol + HeaderChecksum + SourceAddress \
					+ DestinationAddress + Data).ljust(numero_words_necessario * 32, '0')
	return pacote_pronto

# Thread que executa os comandos passados para o Daemon
def thread_comando(conn):
	'''
	Thread para execucao do comando recebido e envio do output de volta
	para o webserver
	'''
	data = conn.recv(BUFFER_SIZE)
	
	if data:

		# Pacote recebido
		pacote = desmonta_pacote_comando(data)

		# Valida o checksum e verifica se o pacote eh de requisicao
		if(valida_checksum(pacote) and pacote[5] == '000'):

			# Identifica o comando da tupla
			comando = dic_comando_int_para_str[pacote[8]]

			# Executa o comando
			output = executa_comando(pacote)
			
			# Deixando o output num formato mais organizado
			resposta = "----------------------------------------------------------------------------\n" + \
						("    Output do comando " + comando + " " + pacote[12]).ljust(76, ' ') + "|\n" + \
						"----------------------------------------------------------------------------\n" + \
						output + "\n"
			
			# Imprime o output do comando no daemon
			print resposta

			# Calcula quantos chunks de 2048 sao necessarios para enviar toda a resposta
			numero_chunks = int(math.ceil(float(len(resposta) * 8) / float(BUFFER_SIZE - 160)))
			# Note que, para cada pacote de resposta a ser enviado, 160 bits (5 words de 32-bit)
			# sao necessarios para o cabecalho
			tamanho_campo_dados = (BUFFER_SIZE - 160)/8
			# Assim, divide o output em pacotes e envia para o webserver
			for i in range(0, numero_chunks):
				parte_resposta = resposta[(i*((BUFFER_SIZE-160)/8)) : ((i+1)*((BUFFER_SIZE-160)/8))]
				pacote_parcial = monta_pacote_resposta(parte_resposta, 0, pacote[11], pacote[10])
				conn.send(pacote_parcial)
			
	# Fecha a conexao
	conn.close()

# -------------------------------------------
#                  M A I N                   |
# -------------------------------------------

while 1:
	conn, addr = s.accept()
	print 'Connection address:', addr

	# Cria uma nova thread para tratar do comando
	thread.start_new_thread(thread_comando, (conn,))