import os
import json
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- IMPORTANDO CONFIGURAÇÕES GLOBAIS ---
from config import (
    MAX_WORKERS_PADRAO,
    PASTA_PARTES_2, 
    PASTA_PARTES_3,
    USA_EXTERNO,      # Seu seletor Nuvem/Local
    API_KEY,  # Reutilizamos esta varíavel para o Token do Puter
    MODELO_IA,           # O modelo (ex: 'gpt-4o' ou o deepseek que deu certo)
    MODELO_EXTERNO
)

# Inicialização Dinâmica
if USA_EXTERNO:
    from puter import ChatCompletion
else:
    import ollama

input_folder = PASTA_PARTES_2
output_folder = PASTA_PARTES_3

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# PROMPT LQA ULTRA-DIRETO (Formato p/t)
prompt_sistema = """Senior Localization QA (PT-BR).
Output: Valid JSON array ONLY.
Task: Fix PT-BR translations in 't'. Ensure natural flow and preserve tags (<cf>, {0}, \\n).
Rule: Keep 'p' keys identical. Return exact same item count.
No talk, no markdown, no notes."""

def limpar_resposta_ia(texto_bruto):
    """Remove conteúdo de raciocínio (tags <think>) e extrai o array JSON puro"""
    if not texto_bruto: return ""
    
    # Prevenção: garante que seja lido como string
    texto_str = str(texto_bruto)
    texto_limpo = re.sub(r'<think>.*?</think>', '', texto_str, flags=re.DOTALL)
    
    try:
        inicio = texto_limpo.find('[')
        fim = texto_limpo.rfind(']') + 1
        if inicio != -1 and fim != 0:
            return texto_limpo[inicio:fim].strip()
    except Exception:
        pass
    return texto_limpo.strip()

def chamar_ia_puter(texto):
    """LQA via pacote Python 'puter' com mapeamento exato do formato de retorno"""
    try:
        mensagens =[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": f"JSON to QA:\n{texto}"}
        ]
        
        resposta = ChatCompletion.create(
            model=MODELO_EXTERNO, 
            messages=mensagens,
            api_key=API_KEY, # Passando a chave que já está no seu config
        )
        
        texto_extraido = ""
        
        if isinstance(resposta, dict):
            # Se for recusado na nuvem (ex: sem créditos ou fora do ar)
            if not resposta.get('success', True):
                print(f"⚠️ Erro retornado pela IA: {resposta.get('error')}")
                return ""
                
            # Identificação da resposta naquele formato problemático do Puter
            if 'reesult' in resposta:
                texto_extraido = resposta['reesult']['message']['content']
            elif 'result' in resposta:
                texto_extraido = resposta['result']['message']['content']
            elif 'choices' in resposta:
                texto_extraido = resposta['choices'][0]['message']['content']
            else:
                print(f"⚠️ Chave de texto não encontrada. Retorno cru: {resposta}")
                return ""
        else:
            texto_extraido = str(resposta)
            
        return limpar_resposta_ia(texto_extraido)
        
    except Exception as e:
        print(f"⚠️ Erro na chamada Puter (LQA): {e}")
        return ""

def chamar_ia_ollama(texto_json):
    """Fallback para Ollama Local"""
    response = ollama.generate(
        model=MODELO_IA,
        system=prompt_sistema,
        prompt=texto_json,
        format='json',
        stream=False
    )
    return response.get('response', '').strip()

def processar_arquivo_lqa(nome_arquivo):
    caminho_in = os.path.join(input_folder, nome_arquivo)
    caminho_out = os.path.join(output_folder, nome_arquivo)
    
    if os.path.exists(caminho_out):
        return {"arquivo": nome_arquivo, "status": "pulado"}

    for tentativa in range(1, 4):
        try:
            with open(caminho_in, 'r', encoding='utf-8') as f:
                dados_originais = json.load(f)
            
            qtd_esperada = len(dados_originais)
            print(f"🚀 {nome_arquivo} - LQA Tentativa {tentativa}/3 (Itens: {qtd_esperada})")
            
            conteudo_texto = json.dumps(dados_originais, ensure_ascii=False)
            
            # Aqui chamamos o Puter ou Ollama
            if USA_EXTERNO:
                resposta_ia = chamar_ia_puter(conteudo_texto)
            else:
                resposta_ia = chamar_ia_ollama(conteudo_texto)

            if not resposta_ia: 
                raise ValueError("Resposta da IA retornou vazia")

            # Desserialização blindada
            try:
                dados_verificados = json.loads(resposta_ia)
            except json.JSONDecodeError as je:
                raise ValueError(f"JSON Incompleto/Inválido: {je}")
            
            # Normalização de lista caso a IA jogue as chaves dentro de um objeto pai
            if isinstance(dados_verificados, dict):
                for key in dados_verificados:
                    if isinstance(dados_verificados[key], list):
                        dados_verificados = dados_verificados[key]
                        break

            # Validação rigorosa do número de itens
            if not isinstance(dados_verificados, list) or len(dados_verificados) != qtd_esperada:
                raise ValueError(f"Contagem incorreta no LQA! Esperado: {qtd_esperada} vs Recebido: {len(dados_verificados) if isinstance(dados_verificados, list) else 'N/A'}")

            # Salvamento Seguro
            with open(caminho_out, 'w', encoding='utf-8') as f:
                json.dump(dados_verificados, f, indent=2, ensure_ascii=False)
            
            print(f"✅ {nome_arquivo} - LQA OK!")
            return {"arquivo": nome_arquivo, "status": "sucesso"}

        except Exception as e:
            print(f"❌ {nome_arquivo} - Erro no LQA: {e}")
            if tentativa < 3:
                time.sleep(2) # Pausa antes de tentar corrigir
            
    return {"arquivo": nome_arquivo, "status": "falha"}

def executar_verificacao_paralela():
    arquivos = sorted([f for f in os.listdir(input_folder) if f.endswith(".json")])
    arquivos_para_processar =[f for f in arquivos if not os.path.exists(os.path.join(output_folder, f))]

    if not arquivos_para_processar:
        print("✅ Nas pastas de entrada não há arquivos novos para verificar!")
        return True

    modo = "PUTER (NUVEM)" if USA_EXTERNO else "OLLAMA (LOCAL)"
    print(f"\n🔍[INICIANDO LQA SIMPLIFICADO VIA {modo} - {len(arquivos_para_processar)} ARQUIVOS]")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS_PADRAO) as executor:
        futuros =[executor.submit(processar_arquivo_lqa, arq) for arq in arquivos_para_processar]
        for futuro in as_completed(futuros):
            futuro.result()
            
            # Pausa Suave Crucial p/ Nuvem
            if USA_EXTERNO:
                time.sleep(1) # Proteção definitiva contra "ban" temporário/Rate Limits na API Free
    
    return True

def main():
    try:
        if executar_verificacao_paralela():
            print("\n🔄 Processo de LQA concluído com sucesso.")
            return True
    except Exception as e:
        print(f"💥 Erro Fatal: {e}")
        return False

if __name__ == '__main__':
    main()