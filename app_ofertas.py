import re
import os
import platform
import subprocess
import textwrap
import requests
from pathlib import Path

# ==========================================
# 1. PROCESSAMENTO DE TEXTO
# ==========================================
def extrair_dados_oferta(texto):
    linhas = [linha.strip() for linha in texto.strip().split('\n') if linha.strip()]
    
    if not linhas:
        return None, []

    texto_validade = linhas[0]
    linhas_ofertas = linhas[1:]
    ofertas_processadas = []
    
    padrao = r"^(.*?)\s+([\d,.]*\s*(?:kg|lt|un|g|ml))\s+([\d,.]+)$"

    for linha in linhas_ofertas:
        resultado = re.match(padrao, linha, re.IGNORECASE)
        if resultado:
            nome_produto = resultado.group(1).upper()
            pedacos_do_nome = textwrap.wrap(nome_produto, width=15)
            nome_quebrado = "\\r".join(pedacos_do_nome) 
            unidade = resultado.group(2).upper()
            preco = resultado.group(3).replace('.', ',')

            ofertas_processadas.append({
                'produto': nome_quebrado,
                'produto_limpo': nome_produto,
                'unidade': unidade,
                'reais': preco
            })
        else:
            print(f"Aviso: A linha '{linha}' nao esta no formato correto e foi ignorada.")
            
    return texto_validade, ofertas_processadas

# ==========================================
# 2. IA DE REMOÇÃO DE FUNDO (NUVEM)
# ==========================================
def preparar_imagem_com_ia(caminho_entrada, caminho_saida):
    API_KEY = "SUA_CHAVE_AQUI" 
    
    if API_KEY == "SUA_CHAVE_AQUI":
        print("AVISO: Voce esqueceu de colocar a sua API_KEY no codigo!")
        return False
        
    print(f"Enviando para a IA na nuvem...")
    try:
        response = requests.post(
            'https://api.remove.bg/v1.0/removebg',
            files={'image_file': open(caminho_entrada, 'rb')},
            data={'size': 'auto'},
            headers={'X-Api-Key': API_KEY},
        )
        if response.status_code == requests.codes.ok:
            with open(caminho_saida, 'wb') as out:
                out.write(response.content)
            print("Fundo removido com sucesso!")
            return True
        else:
            print(f"Erro na API: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Erro de conexao: {e}")
        return False

# ==========================================
# 3. GERADOR DE JSX PARA O PHOTOSHOP
# ==========================================
def gerar_script_jsx(texto_validade, dados_ofertas, caminho_psd_template, caminho_saida_jsx, diretorio_base):
    jsx_code = f"""#target photoshop
    app.displayDialogs = DialogModes.NO;
    var houveErro = false;
    var mensagensErro = [];

    function findLayer(ref, name) {{
        for (var i = 0; i < ref.layers.length; i++) {{
            if (ref.layers[i].name === name) return ref.layers[i];
            if (ref.layers[i].typename === "LayerSet") {{
                var found = findLayer(ref.layers[i], name);
                if (found) return found;
            }}
        }}
        return null;
    }}

    function atualizarConteudoCompleto(nomeSmartObject, dados, caminhoNovaFoto) {{
        var camadaSO = findLayer(doc, nomeSmartObject);
        if (!camadaSO) return;

        // Garante que a camada base esteja visivel caso tenha sido oculta na ultima vez
        camadaSO.visible = true;

        doc.activeLayer = camadaSO;
        var idplacedLayerEditContents = stringIDToTypeID("placedLayerEditContents");
        executeAction(idplacedLayerEditContents, undefined, DialogModes.NO);

        var documentoInterno = app.activeDocument;

        if(findLayer(documentoInterno, "txt_nome"))
            findLayer(documentoInterno, "txt_nome").textItem.contents = dados.produto;
        if(findLayer(documentoInterno, "txt_preco"))
            findLayer(documentoInterno, "txt_preco").textItem.contents = dados.reais;
        if(findLayer(documentoInterno, "txt_unidade"))
            findLayer(documentoInterno, "txt_unidade").textItem.contents = dados.unidade;
        
        var camadaFoto = findLayer(documentoInterno, "img_produto");
        if(camadaFoto) {{
            camadaFoto.remove();
        }}

        var fileRef = new File(caminhoNovaFoto);
        
        if (fileRef.exists) {{
            try {{
                var desc = new ActionDescriptor();
                desc.putPath(charIDToTypeID("null"), fileRef);
                executeAction(charIDToTypeID("Plc "), desc, DialogModes.NO);

                var camadaInserida = documentoInterno.activeLayer;
                camadaInserida.name = "img_produto";
                camadaInserida.resize(120, 120, AnchorPosition.MIDDLECENTER);

                camadaInserida.move(documentoInterno, ElementPlacement.PLACEATEND);

                var camadaAncora = findLayer(documentoInterno, "txt_nome");
                if (camadaAncora) {{
                    documentoInterno.activeLayer = camadaInserida;
                    camadaInserida.move(camadaAncora, ElementPlacement.PLACEAFTER);
                }}

            }} catch (e) {{
                houveErro = true;
                mensagensErro.push("- Erro ao inserir imagem no PS: " + dados.produto);
            }}
        }} else {{
            houveErro = true;
            mensagensErro.push("- Imagem nao encontrada pelo Photoshop: " + dados.produto);
        }}

        documentoInterno.close(SaveOptions.SAVECHANGES);
    }}

    var fileRef = new File("{caminho_psd_template.replace(os.sep, '/')}");
    var doc = app.open(fileRef);

    var camadaData = findLayer(doc, "txt_data");
    if(camadaData) {{
        camadaData.textItem.contents = "{texto_validade}";
    }}
    """

    pasta_fotos = diretorio_base / "fotos"
    total_ofertas = len(dados_ofertas)

    for i, item in enumerate(dados_ofertas):
        numero = i + 1 
        nome_arquivo = item['produto_limpo']
        
        caminho_bruto = None
        for ext in ['.png', '.jpg', '.jpeg', '.webp']:
            if (pasta_fotos / f"{nome_arquivo}{ext}").exists():
                caminho_bruto = pasta_fotos / f"{nome_arquivo}{ext}"
                break
        
        caminho_processado = pasta_fotos / f"{nome_arquivo}_recortado.png"
        caminho_final_pro_ps = ""

        if caminho_processado.exists():
            print(f"\nImagem ja recortada encontrada para: [{nome_arquivo}]. Poupando creditos da API!")
            caminho_final_pro_ps = str(caminho_processado)
            
        elif caminho_bruto:
            print(f"\nProcessando nova imagem na nuvem para: [{nome_arquivo}]")
            sucesso_ia = preparar_imagem_com_ia(str(caminho_bruto), str(caminho_processado))
            caminho_final_pro_ps = str(caminho_processado) if sucesso_ia else str(caminho_bruto)
            
        else:
            print(f"\nFoto original nao encontrada para: [{nome_arquivo}]")
            caminho_final_pro_ps = "FOTO_NAO_ENCONTRADA"

        jsx_code += f"""
        atualizarConteudoCompleto("item{numero}", {{
            produto: "{item['produto']}",
            reais: "{item['reais']}",
            unidade: "{item['unidade']}"
        }}, "{str(caminho_final_pro_ps).replace(os.sep, '/')}");
        """

    # OCULTAR ITENS NÃO UTILIZADOS NO TEMPLATE
    # O loop verifica do próximo número até o 15 (limite seguro caso seu template tenha muitos itens)
    jsx_code += f"""
    for (var idx = {total_ofertas + 1}; idx <= 15; idx++) {{
        var camadaOcultar = findLayer(doc, "item" + idx);
        if (camadaOcultar) {{
            camadaOcultar.visible = false;
        }}
    }}
    """

    caminho_png_final = str(diretorio_base / "saida" / "cartaz_final.png")
    
    jsx_code += f"""
    if (houveErro) {{
        alert("Ocorreram erros:\\n\\n" + mensagensErro.join("\\n") + "\\n\\nA exportacao automatica foi cancelada.");
        app.beeping(); 
    }} else {{
        var arquivoSaida = new File("{caminho_png_final.replace(os.sep, '/')}");
        var opcoesPNG = new PNGSaveOptions();
        opcoesPNG.compression = 5; 
        doc.saveAs(arquivoSaida, opcoesPNG, true, Extension.LOWERCASE);
        doc.close(SaveOptions.DONOTSAVECHANGES);
        alert("Sucesso! Imagem exportada corretamente.");
    }}
    """

    with open(caminho_saida_jsx, 'w', encoding='utf-8') as arquivo_jsx:
        arquivo_jsx.write(jsx_code)

def rodar_no_photoshop(caminho_jsx):
    sistema = platform.system()
    print(f"\nExecutando script JSX no Photoshop...")
    try:
        if sistema == "Windows":
            os.startfile(caminho_jsx)
        elif sistema == "Darwin":  
            subprocess.run(["open", "-b", "com.adobe.Photoshop", caminho_jsx])
    except Exception as e:
        print(f"Erro ao tentar abrir o script JSX: {e}")

# ==========================================
# 4. EXECUÇÃO PRINCIPAL
# ==========================================
if __name__ == "__main__":
    diretorio_script = Path(__file__).parent
    pasta_assets = diretorio_script / "assets"
    
    caminho_template = str(pasta_assets / "template.psd")
    caminho_saida = str(pasta_assets / "atualizar_ofertas.jsx")
    caminho_ofertas = diretorio_script / "ofertas.txt"

    (diretorio_script / "saida").mkdir(exist_ok=True)
    (diretorio_script / "fotos").mkdir(exist_ok=True)
    pasta_assets.mkdir(exist_ok=True)

    if not caminho_ofertas.exists():
        exemplo = "Data valida ate o dia 23/04\nalcatra bovina kg 52,90\npaleta suina kg 15,99"
        caminho_ofertas.write_text(exemplo, encoding='utf-8')
        print(f"O arquivo 'ofertas.txt' foi criado em: {caminho_ofertas}")
        print("Preencha-o com suas ofertas e rode o script novamente!")
    else:
        texto_bruto = caminho_ofertas.read_text(encoding='utf-8')
        
        validade, dados = extrair_dados_oferta(texto_bruto)

        if dados:
            gerar_script_jsx(validade, dados, caminho_template, caminho_saida, diretorio_script)
            rodar_no_photoshop(caminho_saida)