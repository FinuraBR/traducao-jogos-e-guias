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
    USA_EXTERNO, # Interpretado como usar Puter (Cloud)
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

# PROMPT ULTRA-DIRETO (Formato p/t)
prompt_sistema = """Senior Localization (EN -> PT-BR).
Output: Valid JSON array ONLY.
Task: Translate/localization 't' values. Use surrounding items for context.
Rule 1: Keep 'p' keys identical.
Rule 2: No explanations, no markdown, no thinking tags.
Format: [{"p": "path", "t": "translation/localization"}]"""


def limpar_resposta_ia(texto_bruto):
    """Remove tags de raciocínio e extrai apenas o conteúdo do array JSON"""
    if not texto_bruto: return ""
    
    texto_str = str(texto_bruto)
    
    # Remove tags <think> geradas por modelos de raciocínio
    texto_limpo = re.sub(r'<think>.*?</think>', '', texto_str, flags=re.DOTALL)
    
    # Isola apenas a parte do array
    try:
        inicio = texto_limpo.find('[')
        fim = texto_limpo.rfind(']') + 1
        if inicio != -1 and fim != 0:
            return texto_limpo[inicio:fim].strip()
    except Exception:
        pass
        
    return texto_limpo.strip()

def traduzir_com_puter(texto):
    """Tradução via pacote Python 'puter' lidando com a estrutura customizada/OpenRouter"""
    try:
        mensagens =[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": f"JSON to translate:\n{texto}"}
        ]
        
        # Chamada original mantida (a sua já deu certo e chegou lá!)
        resposta = ChatCompletion.create(
            model=MODELO_EXTERNO, 
            messages=mensagens,
            api_key=API_KEY
        )
        
        texto_extraido = ""
        
        # Mapeamento do formato que você acabou de receber:
        if isinstance(resposta, dict):
            if not resposta.get('success', True):
                print(f"⚠️ Erro retornado pela IA: {resposta.get('error')}")
                return ""
                
            # Procura no formato com erro de digitação deles ('reesult')
            if 'reesult' in resposta:
                texto_extraido = resposta['reesult']['message']['content']
            # Prevenção caso eles corrijam o erro de digitação para 'result' um dia
            elif 'result' in resposta:
                texto_extraido = resposta['result']['message']['content']
            # Prevenção caso passem a usar o padrão puro da OpenAI
            elif 'choices' in resposta:
                texto_extraido = resposta['choices'][0]['message']['content']
            else:
                print(f"⚠️ Chave de texto não encontrada. Retorno: {resposta}")
                return ""
        else:
            # Fallback caso seja um objeto da biblioteca
            texto_extraido = str(resposta)
            
        return limpar_resposta_ia(texto_extraido)
        
    except Exception as e:
        print(f"⚠️ Erro na chamada Puter: {e}")
        return ""

def traduzir_com_ollama(texto):
    """Tradução local via Ollama"""
    response = ollama.generate(
        model=MODELO_IA, 
        system=prompt_sistema, 
        prompt=texto, 
        format='json', 
        stream=False
    )
    return response.get('response', '').strip()

def traduzir_texto_com_ia(texto_original):
    try:
        if USA_EXTERNO:
            return traduzir_com_puter(texto_original)
        else:
            return traduzir_com_ollama(texto_original)
    except Exception as e:
        print(f"\n❌ Erro Geral na IA: {e}")
        return ""

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
            
            # Executa a IA
            resposta_raw = traduzir_texto_com_ia(json.dumps(dados_originais, ensure_ascii=False))
            
            if not resposta_raw: 
                raise ValueError("Resposta da IA retornou vazia")

            # Analisa o retorno da IA
            dados_traduzidos = json.loads(resposta_raw)
            
            # Normalização caso a IA coloque o array dentro de um objeto pai: {"data": [...]}
            if isinstance(dados_traduzidos, dict):
                for key in dados_traduzidos:
                    if isinstance(dados_traduzidos[key], list):
                        dados_traduzidos = dados_traduzidos[key]
                        break

            # Validação final do tipo e quantidade
            if not isinstance(dados_traduzidos, list) or len(dados_traduzidos) != qtd_esperada:
                rec = len(dados_traduzidos) if isinstance(dados_traduzidos, list) else 'Formato Inválido'
                raise ValueError(f"Contagem incorreta! Esperado: {qtd_esperada} vs Recebido: {rec}")

            # Salva o arquivo de sucesso
            with open(caminho_out, 'w', encoding='utf-8') as f:
                json.dump(dados_traduzidos, f, indent=2, ensure_ascii=False)
            
            print(f"✅ {nome_arquivo} - Sucesso!")
            return {"arquivo": nome_arquivo, "status": "sucesso"}
            
        except json.JSONDecodeError as je:
            print(f"❌ Erro de formato JSON em {nome_arquivo}: {je}")
            if tentativa < 3: time.sleep(2)
        except Exception as e:
            print(f"❌ Erro no processamento de {nome_arquivo}: {e}")
            if tentativa < 3: time.sleep(2) 
            
    return {"arquivo": nome_arquivo, "status": "falha"}


def executar_traducao_paralela():
    arquivos = sorted([f for f in os.listdir(input_folder) if f.endswith(".json")])
    arquivos_para_processar =[f for f in arquivos if not os.path.exists(os.path.join(output_folder, f))]
    
    if not arquivos_para_processar: 
        print("✅ Nada para traduzir nas pastas de entrada.")
        return True
    
    modo = "PUTER (CLOUD)" if USA_EXTERNO else "OLLAMA (LOCAL)"
    print(f"\n🤖[INICIANDO TRADUÇÃO VIA {modo} - {len(arquivos_para_processar)} ARQUIVOS]")
    
    # ATENÇÃO: Se usar o Puter, um MAX_WORKERS > 3~5 pode gerar bloqueio de "Too Many Requests". 
    # Sugere-se manter baixo se o uso for free-tier da nuvem.
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_PADRAO) as executor:
        futuros =[executor.submit(processar_arquivo, arq) for arq in arquivos_para_processar]
        for futuro in as_completed(futuros):
            futuro.result()
            
            # Pausa de segurança suave ao usar nuvem para não esgotar limite de requisições
            if USA_EXTERNO:
                time.sleep(0.5) 

    return True

def main():
    if executar_traducao_paralela():
        print("\n🏁 Processo de tradução finalizado.")

if __name__ == '__main__':
    main()