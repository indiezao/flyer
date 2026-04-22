#target photoshop
    app.displayDialogs = DialogModes.NO;
    var houveErro = false;
    var mensagensErro = [];

    function findLayer(ref, name) {
        for (var i = 0; i < ref.layers.length; i++) {
            if (ref.layers[i].name === name) return ref.layers[i];
            if (ref.layers[i].typename === "LayerSet") {
                var found = findLayer(ref.layers[i], name);
                if (found) return found;
            }
        }
        return null;
    }

    function atualizarConteudoCompleto(nomeSmartObject, dados, caminhoNovaFoto) {
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
        if(camadaFoto) {
            camadaFoto.remove();
        }

        var fileRef = new File(caminhoNovaFoto);
        
        if (fileRef.exists) {
            try {
                var desc = new ActionDescriptor();
                desc.putPath(charIDToTypeID("null"), fileRef);
                executeAction(charIDToTypeID("Plc "), desc, DialogModes.NO);

                var camadaInserida = documentoInterno.activeLayer;
                camadaInserida.name = "img_produto";
                camadaInserida.resize(120, 120, AnchorPosition.MIDDLECENTER);

                camadaInserida.move(documentoInterno, ElementPlacement.PLACEATEND);

                var camadaAncora = findLayer(documentoInterno, "txt_nome");
                if (camadaAncora) {
                    documentoInterno.activeLayer = camadaInserida;
                    camadaInserida.move(camadaAncora, ElementPlacement.PLACEAFTER);
                }

            } catch (e) {
                houveErro = true;
                mensagensErro.push("- Erro ao inserir imagem no PS: " + dados.produto);
            }
        } else {
            houveErro = true;
            mensagensErro.push("- Imagem nao encontrada pelo Photoshop: " + dados.produto);
        }

        documentoInterno.close(SaveOptions.SAVECHANGES);
    }

    var fileRef = new File("/Users/joaoricardolampugnani/flyer/assets/template.psd");
    var doc = app.open(fileRef);

    var camadaData = findLayer(doc, "txt_data");
    if(camadaData) {
        camadaData.textItem.contents = "27/04";
    }
    
        atualizarConteudoCompleto("item1", {
            produto: "FARINHA\rMANDIOCA DU LEO",
            reais: "11,49",
            unidade: "KG"
        }, "/Users/joaoricardolampugnani/flyer/fotos/FARINHA MANDIOCA DU LEO_recortado.png");
        
        atualizarConteudoCompleto("item2", {
            produto: "REFRIGERANTE\rVIVER",
            reais: "4,99",
            unidade: "2LT"
        }, "/Users/joaoricardolampugnani/flyer/fotos/REFRIGERANTE VIVER_recortado.png");
        
    for (var idx = 3; idx <= 15; idx++) {
        var camadaOcultar = findLayer(doc, "item" + idx);
        if (camadaOcultar) {
            camadaOcultar.visible = false;
        }
    }
    
    if (houveErro) {
        alert("Ocorreram erros:\n\n" + mensagensErro.join("\n") + "\n\nA exportacao automatica foi cancelada.");
        app.beeping(); 
    } else {
        var arquivoSaida = new File("/Users/joaoricardolampugnani/flyer/saida/cartaz_final.png");
        var opcoesPNG = new PNGSaveOptions();
        opcoesPNG.compression = 5; 
        doc.saveAs(arquivoSaida, opcoesPNG, true, Extension.LOWERCASE);
        doc.close(SaveOptions.DONOTSAVECHANGES);
        alert("Sucesso! Imagem exportada corretamente.");
    }
    