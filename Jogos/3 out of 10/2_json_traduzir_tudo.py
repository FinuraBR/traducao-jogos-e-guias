import os
import json
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CONFIGURAÇÕES GLOBAIS ---
from config import (
    PASTA_PARTES_1,
    MAX_WORKERS_PADRAO, 
    PASTA_PARTES_3,
    USA_EXTERNO, 
    MODELO_IA,
    MODELO_EXTERNO,
    API_KEY
)

# Inicialização segura do SDK Puter/Ollama
if USA_EXTERNO:
    from puter import ChatCompletion  
else:
    import ollama

input_folder = PASTA_PARTES_1
output_folder = PASTA_PARTES_3

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# --- PROMPT REFINADO (PROTEÇÃO DE ENGINE) ---
prompt_sistema = """Senior Localization (EN -> PT-BR).
Output: Valid JSON array ONLY.
Task: Translate/localization 't' values. Use surrounding items for context.
Rule 1: Keep 'p' keys identical.
Rule 2: No explanations, no markdown, no thinking tags.
Format: [{"p": "path", "t": "translation/localization"}]"""

def validar_integridade_tags(original, traduzido):
    """
    Verifica se as variáveis e tags foram mantidas na tradução.
    Retorna True se estiver ok, False se algo foi corrompido.
    """
    # Procura por {var}, <tag>, </tag>, %s, %d
    pattern = re.compile(r'\{.*?\}|<.*?>|%[sd]')
    tags_originais = pattern.findall(original)
    tags_traduzidas = pattern.findall(traduzido)
    
    return len(tags_originais) == len(tags_traduzidas)

def limpar_resposta_ia(texto_bruto):
    """Remove tags de raciocínio e extrai apenas o conteúdo do array JSON"""
    if not texto_bruto: return ""
    
    texto_str = str(texto_bruto)
    
    # Remove tags <think> geradas por modelos de raciocínio (DeepSeek etc)
    texto_limpo = re.sub(r'<think>.*?</think>', '', texto_str, flags=re.DOTALL)
    
    # Isola apenas a parte do array JSON
    try:
        inicio = texto_limpo.find('[')
        fim = texto_limpo.rfind(']') + 1
        if inicio != -1 and fim != 0:
            return texto_limpo[inicio:fim].strip()
    except Exception:
        pass
        
    return texto_limpo.strip()

def traduzir_com_puter(texto):
    """Tradução via Puter (Cloud)"""
    try:
        mensagens = [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": texto}
        ]
        
        resposta = ChatCompletion.create(
            model=MODELO_EXTERNO, 
            messages=mensagens,
            api_key=API_KEY
        )
        
        texto_extraido = ""
        if isinstance(resposta, dict):
            if not resposta.get('success', True):
                print(f"⚠️ Erro Puter: {resposta.get('error')}")
                return ""
            
            # Navegação no objeto de resposta (suporte a variações de chaves)
            if 'reesult' in resposta: # Caso o erro de typo persista no SDK
                texto_extraido = resposta['reesult']['message']['content']
            elif 'result' in resposta:
                texto_extraido = resposta['result']['message']['content']
            elif 'choices' in resposta:
                texto_extraido = resposta['choices'][0]['message']['content']
        else:
            texto_extraido = str(resposta)
            
        return limpar_resposta_ia(texto_extraido)
    except Exception as e:
        print(f"⚠️ Erro Puter: {e}")
        return ""

def traduzir_com_ollama(texto):
    """Tradução local via Ollama"""
    try:
        response = ollama.generate(
            model=MODELO_IA, 
            system=prompt_sistema, 
            prompt=texto, 
            format='json', 
            stream=False
        )
        return response.get('response', '').strip()
    except Exception as e:
        print(f"⚠️ Erro Ollama: {e}")
        return ""

def traduzir_texto_com_ia(texto_original):
    if USA_EXTERNO:
        return traduzir_com_puter(texto_original)
    else:
        return traduzir_com_ollama(texto_original)

def processar_arquivo(nome_arquivo):
    caminho_in = os.path.join(input_folder, nome_arquivo)
    caminho_out = os.path.join(output_folder, nome_arquivo)
    
    if os.path.exists(caminho_out):
        return {"arquivo": nome_arquivo, "status": "pulado"}

    for tentativa in range(1, 4):
        try:
            with open(caminho_in, 'r', encoding='utf-8') as f:
                dados_originais = json.load(f)
            
            qtd_esperada = len(dados_originais)
            print(f"🚀 {nome_arquivo} - Tentativa {tentativa}/3 (Itens: {qtd_esperada})")
            
            resposta_raw = traduzir_texto_com_ia(json.dumps(dados_originais, ensure_ascii=False))
            
            if not resposta_raw: 
                raise ValueError("Resposta da IA vazia")

            dados_traduzidos = json.loads(resposta_raw)
            
            # Normalização caso venha envolto em objeto pai
            if isinstance(dados_traduzidos, dict):
                for key in dados_traduzidos:
                    if isinstance(dados_traduzidos[key], list):
                        dados_traduzidos = dados_traduzidos[key]
                        break

            # Validação de Quantidade
            if not isinstance(dados_traduzidos, list) or len(dados_traduzidos) != qtd_esperada:
                raise ValueError(f"Contagem incorreta! Esperado: {qtd_esperada}")

            # Validação de Integridade de Tags e Variáveis
            for i in range(qtd_esperada):
                orig = dados_originais[i]['t']
                trad = dados_traduzidos[i]['t']
                if not validar_integridade_tags(orig, trad):
                    print(f"⚠️ Erro de Tags na linha {i} de {nome_arquivo}. Refazendo...")
                    raise ValueError("Tags corrompidas")

            # Salva o arquivo de sucesso
            with open(caminho_out, 'w', encoding='utf-8') as f:
                json.dump(dados_traduzidos, f, indent=2, ensure_ascii=False)
            
            print(f"✅ {nome_arquivo} - Sucesso!")
            return {"arquivo": nome_arquivo, "status": "sucesso"}
            
        except json.JSONDecodeError as je:
            print(f"❌ JSON inválido em {nome_arquivo}: {je}")
            if tentativa < 3: time.sleep(2)
        except Exception as e:
            print(f"❌ Erro em {nome_arquivo}: {e}")
            if tentativa < 3: time.sleep(2) 
            
    return {"arquivo": nome_arquivo, "status": "falha"}

def executar_traducao_paralela():
    arquivos = sorted([f for f in os.listdir(input_folder) if f.endswith(".json")])
    arquivos_para_processar = [f for f in arquivos if not os.path.exists(os.path.join(output_folder, f))]
    
    if not arquivos_para_processar: 
        print("✅ Nada para traduzir.")
        return True
    
    modo = "PUTER (CLOUD)" if USA_EXTERNO else "OLLAMA (LOCAL)"
    print(f"\n🤖 [TRADUÇÃO: {modo} - {len(arquivos_para_processar)} ARQUIVOS]")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_PADRAO) as executor:
        futuros = [executor.submit(processar_arquivo, arq) for arq in arquivos_para_processar]
        for futuro in as_completed(futuros):
            futuro.result()
            if USA_EXTERNO:
                time.sleep(0.5) 
    return True

def main():
    if executar_traducao_paralela():
        print("\n🏁 Processo de tradução finalizado.")

if __name__ == '__main__':
    main()