# 🔖 Flyer
**Um script em Python para editar arquivos PSD do Photoshop para automatizar a criação de panfletos de ofertas.**

Desenvolvido para uso real, o script automaticamente tira o fundo das imagens dos produtos e altera todos os textos (nome do produto, unidade e preço) de forma rápida e eficiente, permitindo a estilização com todos os recursos do Photoshop.
Criado com Python e ExtendScript (JavaScript do Photoshop).

### Preparações no arquivo .PSD:
```
Antes de utilizar, o arquivo template deve ser modificado para garantir o funcionamento correto do script.
Os requerimentos do script é:
1. Todo produto deve ser um SmartObject dedicado, e ter o nome e item<1 até 7>.
2. Esse SmartObject deve ter os seguintes campos com os nomes específicos:
   txt_produto  :  nome do produto
   txt_unidade  :  unidade do produto (kg, g, lt, und)
   txt_preco    :  preço do produto

[!] A imagem do produto sempre será re-ordenada para ficar abaixo do txt_produto.
```

### Como utilizar:
```
1. Alterar as informações do arquivo ofertas.txt:
   a primeira linha sempre será utilizada para ditar até quando as ofertas são válidas.
   a formatação deve seguir o seguinte padrão: <nome do produto> <unidade (kg, und, lt)> <preço>

2. Execute o script app_ofertas.py
   o script deve, automaticamente, preencher os campos de texto com as informações corretas da lista.
   a imagem será puxada da pasta /fotos/ e deve conter o exato mesmo nome do produto.
   caso o app não encontre uma imagem correspondente ao do produto, continuará normalmente até o fim do loop.
   o panfleto será exportado automaticamente caso não houver erro, e será salvo na pasta /saida/.
```
