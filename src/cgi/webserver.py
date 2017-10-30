#!/usr/bin/env python
import cgi
import cgitb
import os

cgitb.enable()

print "Content-type: text/html\r\n\r\n";
print "<font size=+1>Environment</font></br>";

print "<pre>"

# Leitura dos parametros do HTML 
parametros_html = cgi.FieldStorage()
lista_nomes = []

# Tuplas de comandos passados pelo HTML
for parametro in parametros_html:
	if(parametro[0:3] == 'maq'):
		if(parametro[4] == '_'):
			lista_nomes.append((parametro[3],parametro[5:len(parametro)], ''))
		else:
			lista_nomes.append((parametro[3],parametro[5:len(parametro)], parametros_html[parametro].value))

# Escrita dos comandos
for x in lista_nomes:
	print x
	print "<br>"

print "</pre>"

