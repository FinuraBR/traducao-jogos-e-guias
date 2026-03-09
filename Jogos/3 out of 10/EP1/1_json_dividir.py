import json
import os
import sys

# --- IMPORTANDO CONFIGURAÇÕES GLOBAIS ---
from config import (
    PASTA_JSON_ORIGINAL, 
    PASTA_PARTES_1, 
    ARQUIVO_STATUS
)

LIMITE_CARACTERES_POR_PARTE = 3000

def extrair_textos_simplificado(obj, lista, path=""):
    """
    Extrai textos priorizando LocalizedString, mas usando SourceString 
    ou CultureInvariantString como referência para a tradução.
    O path (p) sempre apontará para 'LocalizedString'.
    """
    if isinstance(obj, dict):
        # Verifica as chaves comuns em objetos de texto da Unreal
        source = obj.get("SourceString")
        invariant = obj.get("CultureInvariantString")
        localized = obj.get("LocalizedString")

        # Define a referência para tradução (Source > Invariant)
        # Se houver LocalizedString já preenchida, ela poderia ser a referência, 
        # mas conforme sua regra, usamos Source/Invariant como base.
        referencia = source if source is not None else invariant
        
        # Se não houver Source nem Invariant, mas houver Localized, usamos Localized
        if referencia is None:
            referencia = localized

        # Critérios para processar este objeto como um texto traduzível:
        # Deve ter algum conteúdo e não ser apenas "null" ou vazio
        if referencia and str(referencia).strip() and referencia != "null":
            # O caminho de destino será SEMPRE o LocalizedString
            # Se ele não existir no JSON original, o script de aplicação irá criá-lo
            lista.append({
                "p": f"{path}.LocalizedString" if path else "LocalizedString",
                "t": referencia
            })
            # Como já processamos este objeto como um texto, não precisamos 
            # percorrer suas chaves internas (evita pegar a mesma string duas vezes)
            return

        # Se não for um objeto de texto, continua a recursão normal pelas chaves
        for k, v in obj.items():
            novo_path = f"{path}.{k}" if path else k
            extrair_textos_simplificado(v, lista, novo_path)
                
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            novo_path = f"{path}[{i}]"
            extrair_textos_simplificado(item, lista, novo_path)

def limpar_pasta_partes():
    if not os.path.exists(PASTA_PARTES_1): os.makedirs(PASTA_PARTES_1)
    for f in os.listdir(PASTA_PARTES_1):
        if f.endswith(".json"): os.remove(os.path.join(PASTA_PARTES_1, f))

def main():
    print("\n🔍 Preparando extração focada em LocalizedString...")
    
    alvo = None
    for root, _, files in os.walk(PASTA_JSON_ORIGINAL):
        for f in files:
            if f.endswith(".json") and not f.endswith(".bak"):
                alvo = {"nome": f.replace(".json", ""), "subpath": os.path.relpath(root, PASTA_JSON_ORIGINAL)}
                break
        if alvo: break

    if not alvo: return print("✨ Tudo traduzido!")

    arquivo_caminho_completo = os.path.join(PASTA_JSON_ORIGINAL, alvo['subpath'], alvo['nome'] + ".json")
    print(f"📦 Alvo encontrado: {alvo['subpath']}\\{alvo['nome']}.json")

    with open(arquivo_caminho_completo, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    with open(ARQUIVO_STATUS, 'w', encoding='utf-8') as f: 
        json.dump(alvo, f, indent=2)

    limpar_pasta_partes()
    
    lista_para_traduzir = []
    extrair_textos_simplificado(dados, lista_para_traduzir)
    
    if not lista_para_traduzir:
        print("⚠️ Nenhum texto traduzível encontrado. Verifique a estrutura do JSON.")
        sys.exit(10)
        return

    # Divisão por caracteres para não estourar o limite do tradutor
    partes = []
    bloco_atual = []
    caracteres_acumulados = 0

    for item in lista_para_traduzir:
        tamanho = len(json.dumps(item, ensure_ascii=False))
        if (caracteres_acumulados + tamanho) > LIMITE_CARACTERES_POR_PARTE and bloco_atual:
            partes.append(bloco_atual)
            bloco_atual = []
            caracteres_acumulados = 0
        bloco_atual.append(item)
        caracteres_acumulados += tamanho

    if bloco_atual: partes.append(bloco_atual)

    for idx, conteudo in enumerate(partes):
        nome_arquivo = f'parte_{idx+1:03d}.json'
        with open(os.path.join(PASTA_PARTES_1, nome_arquivo), 'w', encoding='utf-8') as f:
            json.dump(conteudo, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Extraídos {len(lista_para_traduzir)} textos em {len(partes)} partes.")
    sys.exit(0)

if __name__ == '__main__':
    main()