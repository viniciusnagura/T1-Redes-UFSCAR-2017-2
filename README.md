# T1-Redes-UFSCAR-2017-2

Trabalho 1 da disciplina de Redes de Computadores, do 2º Semestre de 2017, da Universidade Federal de São Carlos.

#### Descrição do projeto
[Clique aqui](https://github.com/viniciusnagura/T1-Redes-UFSCAR-2017-2/blob/master/doc/Descri%C3%A7%C3%A3o%20do%20Projeto.pdf).

#### Instruções para rodar o projeto:

* Editar o arquivo apache2.conf em /etc/apache2/apache2.conf
	```
	sudo vi /etc/apache2/apache2.conf
	```
* Em seguida, substituir:
	```
	<Directory /var/www/>
	     Options Indexes FollowSymLinks
	     AllowOverride None
	     Require all granted
	</Directory>
	```
	pelo path da pasta src do projeto. Por exemplo:
	```
	<Directory /home/aluno/Desktop/T1/T1-Redes-UFSCAR-2017-2/src/>
		Options Indexes FollowSymLinks
		AllowOverride None
		Require all granted
	</Directory>
	```
* Depois, adicionar
	```
	ScriptAlias "cgi-bin" "***path_da_pasta_cgi-bin_do_projeto***"
	```
	e substituir
	```
	<Directory /usr/lib/cgi-bin/>
		Options ExecCGI
		SetHandler cgi-script
	</Directory>
	```
	também pelo path da pasta cgi-bin do projeto. Por exemplo:
	```
	 ScriptAlias "/cgi-bin/" "/home/aluno/Desktop/T1/T1-Redes-UFSCAR-2017-2/src/cgi-bin/"
	 <Directory /home/aluno/Desktop/T1/T1-Redes-UFSCAR-2017-2/src/cgi-bin/>
	 		Options ExecCGI
	 		SetHandler cgi-script
	 </Directory>
	 ```
	* Por fim, reiniciar o Apache2
	 ```
	 sudo service apache2 restart