import json
import os
import glob
import re
import sys
from config import PASTA_JSON_ORIGINAL, PASTA_PARTES_3, ARQUIVO_JSON_TRADUZIDO, ARQUIVO_STATUS

def navegar_e_injetar(obj, path, texto_vindo_da_traducao):
    """
    Navega até o objeto e aplica a tradução baseada na regra de igualdade literal.
    """
    try:
        # Divide o path (ex: Root.Items[0].LocalizedString)
        partes = re.findall(r'([^.\[\]]+)', path)
        caminho_pai = partes[:-1]
        chave_alvo = partes[-1] # Geralmente 'LocalizedString'
        
        # Navega até o objeto pai
        atual = obj
        for parte in caminho_pai:
            if parte.isdigit():
                atual = atual[int(parte)]
            else:
                atual = atual[parte]

        # 1. Pega o texto de referência original (Source ou Invariant)
        # Usamos exatamente a mesma lógica de prioridade do Script 1
        source_original = atual.get("SourceString")
        if source_original is None:
            source_original = atual.get("CultureInvariantString")
        
        # 2. Verifica se a chave LocalizedString já existe fisicamente no arquivo
        existe_no_molde = chave_alvo in atual

        # --- REGRA DE INJEÇÃO ---
        
        # Caso A: O texto traduzido é DIFERENTE do original (Tradução real aconteceu)
        if texto_vindo_da_traducao != source_original:
            atual[chave_alvo] = texto_vindo_da_traducao
            return True # Houve mudança real

        # Caso B: O texto traduzido é LITERALMENTE IGUAL ao original
        else:
            if existe_no_molde:
                # "se for igual... ele n exclui a chave"
                atual[chave_alvo] = texto_vindo_da_traducao
                # Retorna False para o contador pois não houve "tradução", apenas manutenção
                return False 
            else:
                # "se n tiver apenas n adiciona"
                return False

    except Exception:
        return False

def main():
    if not os.path.exists(ARQUIVO_STATUS): sys.exit(1)
    
    with open(ARQUIVO_STATUS, 'r', encoding='utf-8') as f: 
        status = json.load(f)

    molde_path = os.path.join(PASTA_JSON_ORIGINAL, status['subpath'], status['nome'] + ".json")
    
    with open(molde_path, 'r', encoding='utf-8') as f: 
        dados_originais = json.load(f)
    
    arquivos_partes = sorted(glob.glob(os.path.join(PASTA_PARTES_3, 'parte_*.json')))
    if not arquivos_partes:
        sys.exit(1)

    mudancas_reais = 0
    for arq in arquivos_partes:
        with open(arq, 'r', encoding='utf-8') as f: 
            lista_traducao = json.load(f)
            for item in lista_traducao:
                path = item.get('p')
                t = item.get('t')
                
                if path and t is not None:
                    # Se houver tradução real, incrementamos o contador
                    if navegar_e_injetar(dados_originais, path, t):
                        mudancas_reais += 1

    # Se ao final de todas as partes, nenhuma tradução real foi injetada...
    if mudancas_reais == 0:
        # Saímos com código 10 para o Gerente saber que deve pular este arquivo
        sys.exit(10)

    # Se houve mudanças, salvamos o arquivo final
    os.makedirs(os.path.dirname(ARQUIVO_JSON_TRADUZIDO), exist_ok=True)
    with open(ARQUIVO_JSON_TRADUZIDO, 'w', encoding='utf-8') as f:
        json.dump(dados_originais, f, indent=2, ensure_ascii=False)
    
    sys.exit(0)

if __name__ == '__main__': 
    main()