import json
import os
import glob
import re
import sys
from config import PASTA_JSON_ORIGINAL, PASTA_PARTES_3, ARQUIVO_JSON_TRADUZIDO, ARQUIVO_STATUS

# Lista de chaves que devem ser sincronizadas com a tradução
CHAVES_DE_TEXTO = ["SourceString", "LocalizedString", "CultureInvariantString", "DisplayString"]

def navegar_e_injetar(obj, path, texto_vindo_da_traducao):
    """
    Navega até o objeto e injeta a tradução em TODAS as chaves de texto do bloco.
    """
    try:
        if texto_vindo_da_traducao is None:
            return False

        # Divide o path (ex: Exports[0].Data[1].LocalizedString)
        partes = re.findall(r'([^.\[\]]+)', path)
        caminho_pai = partes[:-1]
        chave_original_alvo = partes[-1] 
        
        # Navega até o objeto pai (o bloco que contém as chaves de texto)
        atual = obj
        for parte in caminho_pai:
            if parte.isdigit():
                atual = atual[int(parte)]
            else:
                atual = atual[parte]

        mudou_algo = False
        
        # --- LÓGICA DE INJEÇÃO REDUNDANTE ---
        # Em vez de mudar apenas a chave que veio no 'path', 
        # mudamos todas as chaves de texto que existirem nesse bloco.
        
        for chave in CHAVES_DE_TEXTO:
            if chave in atual:
                valor_antigo = atual.get(chave)
                
                # Só aplicamos se o texto for diferente ou se a chave alvo for a principal
                if valor_antigo != texto_vindo_da_traducao:
                    atual[chave] = texto_vindo_da_traducao
                    mudou_algo = True
                
        # Caso a chave específica do path não estivesse na nossa lista (segurança)
        if chave_original_alvo not in atual:
            atual[chave_original_alvo] = texto_vindo_da_traducao
            mudou_algo = True

        return mudou_algo

    except Exception as e:
        # print(f"Erro ao injetar: {e}")
        return False

def main():
    if not os.path.exists(ARQUIVO_STATUS): 
        sys.exit(1)
    
    with open(ARQUIVO_STATUS, 'r', encoding='utf-8') as f: 
        status = json.load(f)

    molde_path = os.path.join(PASTA_JSON_ORIGINAL, status['subpath'], status['nome'] + ".json")
    
    if not os.path.exists(molde_path):
        print(f"❌ Molde não encontrado: {molde_path}")
        sys.exit(1)

    with open(molde_path, 'r', encoding='utf-8') as f: 
        dados_originais = json.load(f)
    
    arquivos_partes = sorted(glob.glob(os.path.join(PASTA_PARTES_3, 'parte_*.json')))
    if not arquivos_partes:
        print("⚠️ Nenhuma parte traduzida encontrada.")
        sys.exit(1)

    total_injetado = 0
    for arq in arquivos_partes:
        with open(arq, 'r', encoding='utf-8') as f: 
            try:
                lista_traducao = json.load(f)
            except json.JSONDecodeError:
                continue

            for item in lista_traducao:
                path = item.get('p')
                t = item.get('t')
                
                if path and t is not None:
                    if navegar_e_injetar(dados_originais, path, t):
                        total_injetado += 1

    # Salva o arquivo final com as injeções
    os.makedirs(os.path.dirname(ARQUIVO_JSON_TRADUZIDO), exist_ok=True)
    with open(ARQUIVO_JSON_TRADUZIDO, 'w', encoding='utf-8') as f:
        json.dump(dados_originais, f, indent=2, ensure_ascii=False)
    
    if total_injetado == 0:
        print(f"ℹ️ {status['nome']}: Nenhuma alteração necessária (já traduzido ou igual).")
        sys.exit(10)
    
    print(f"✅ Sucesso: {total_injetado} blocos de texto sincronizados em {status['nome']}.")
    sys.exit(0)

if __name__ == '__main__': 
    main()