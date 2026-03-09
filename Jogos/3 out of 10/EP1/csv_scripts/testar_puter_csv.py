import os
import re
import sys
# Certifique-se de que a biblioteca 'puter' está instalada: pip install puter
try:
    from puter import ChatCompletion  
except ImportError:
    print("❌ Erro: A biblioteca 'puter' não está instalada.")
    print("Por favor, instale-a usando: pip install puter")
    sys.exit(1)

# --- CONFIGURAÇÕES DE API E MODELO ---
# ATENÇÃO: Substitua 'SUA_API_KEY_AQUI' pela sua chave API do Puter/OpenRouter
# Você pode definir como variável de ambiente PUTER_API_KEY para não precisar colocar aqui
API_KEY = os.getenv("PUTER_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0IjoiZ3VpIiwidiI6IjAuMC4wIiwidSI6Ilp6OGVDUEoxVEJ5TUNLVFNoNHZReGc9PSIsInV1IjoiZUtqd3JzM0lUR3FEWko2UFE4cHV3QT09IiwiaWF0IjoxNzcyOTg1ODQ1fQ.IvMVau5Xfb83sZGWBtHji6Gow1rivZXTc8jNyAJM-eA") 
MODELO_EXTERNO = "qwen/qwen3.5-122b-a10b" # 'qwen/qwen3.5-397b-a17b' ou 'qwen/qwen3.5-122b-a10b' ou 'openai/gpt-4o' Ou 'google/gemini-3.1-flash-lite-preview' ou outro modelo Puter/OpenRouter


# --- PROMPT BASE PARA CSV ---
# Este é o prompt que a IA receberá como "instrução"
DEFAULT_SYSTEM_PROMPT = """Senior Localization (EN -> PT-BR).
Output: Valid CSV format ONLY.
Task: Translate/localization 'source' values. Use surrounding items for context.
Rule 1: If the translation contains a comma (,), YOU MUST enclose it in double quotes (").
Rule 2: Keep 'key' column values identical.
Rule 3: No explanations, no markdown, no thinking tags.
Format: key,source,Translation"""

def limpar_resposta_ia(texto_bruto):
    """Remove tags de raciocínio e markdown, extraindo apenas o texto relevante."""
    if not texto_bruto: return ""
    
    texto_str = str(texto_bruto)
    texto_limpo = re.sub(r'<think>.*?</think>', '', texto_str, flags=re.DOTALL)
    texto_limpo = re.sub(r'```(?:csv|text)?\n?', '', texto_limpo).replace('```', '').strip()
    
    # Tenta isolar o CSV se a IA ainda inseriu alguma conversa
    linhas = texto_limpo.split('\n')
    csv_linhas = []
    em_csv = False
    
    for linha in linhas:
        if linha.lower().startswith('key,source,translation'): # Início do CSV
            em_csv = True
            csv_linhas.append(linha)
        elif em_csv and linha.count(',') >= 2: # Linhas de dados
            csv_linhas.append(linha)
        elif em_csv and not linha.strip(): # Linha vazia dentro do CSV
            csv_linhas.append(linha)
        elif em_csv: # Fim do bloco CSV
            break
            
    return '\n'.join(csv_linhas) if csv_linhas else texto_limpo


def traduzir_com_puter(system_prompt, user_prompt):
    """Envia o prompt para a IA Puter/Cloud e retorna a resposta."""
    print(f"\n📞 Chamando Puter ({MODELO_EXTERNO})...")
    try:
        mensagens = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        resposta = ChatCompletion.create(
            model=MODELO_EXTERNO,
            messages=mensagens,
            api_key=API_KEY
        )
        
        texto_extraido = ""
        
        if isinstance(resposta, dict):
            if not resposta.get('success', True):
                print(f"⚠️ Erro retornado pela IA: {resposta.get('error')}")
                return ""
            
            # Formato de resposta do Puter/OpenRouter (com 'reesult' ou 'result')
            if 'reesult' in resposta:
                texto_extraido = resposta['reesult']['message']['content']
            elif 'result' in resposta:
                texto_extraido = resposta['result']['message']['content']
            # Fallback para o formato padrão da OpenAI (se eles mudarem)
            elif 'choices' in resposta and resposta['choices']:
                texto_extraido = resposta['choices'][0]['message']['content']
            else:
                print(f"⚠️ Chave de texto não encontrada no retorno da IA. Retorno: {resposta}")
                return ""
        else:
            texto_extraido = str(resposta) # Fallback para objeto

        return limpar_resposta_ia(texto_extraido)
        
    except Exception as e:
        print(f"❌ Erro na chamada Puter: {e}")
        return ""

def main():
    input_folder = r"D:\EP1\csv_scripts\1_partes_para_traduzir"
    output_folder = r"D:\EP1\csv_scripts\2_partes_traduzidas"

    # 1. Cria a pasta de saída se ela não existir
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"✅ Pasta de saída '{output_folder}' criada.")

    # 2. Verifica se a pasta de entrada existe
    if not os.path.exists(input_folder):
        print(f"❌ Erro: A pasta de entrada '{input_folder}' não foi encontrada.")
        print("Por favor, crie a pasta e coloque seus arquivos CSV nela.")
        sys.exit(1)

    print(f"Iniciando tradução automática de arquivos CSV da pasta '{input_folder}'...")

    # Usa o prompt do sistema padrão
    system_prompt = DEFAULT_SYSTEM_PROMPT

    translated_count = 0
    csv_files_found = 0

    # 3. Itera através dos arquivos na pasta de entrada
    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            csv_files_found += 1
            input_filepath = os.path.join(input_folder, filename)
            output_filepath = os.path.join(output_folder, filename) # Salva com o mesmo nome na pasta de saída

            print(f"\n--- Processando arquivo: {filename} ---")
            try:
                # 4. Lê o conteúdo do arquivo CSV
                with open(input_filepath, 'r', encoding='utf-8') as f:
                    csv_content = f.read()

                if not csv_content.strip():
                    print(f"⚠️ Aviso: O arquivo '{filename}' está vazio. Pulando tradução.")
                    continue

                # 5. Chama a função de tradução
                response_text = traduzir_com_puter(system_prompt, csv_content)

                # 6. Salva o conteúdo traduzido
                if response_text:
                    with open(output_filepath, 'w', encoding='utf-8') as f:
                        f.write(response_text)
                    print(f"✅ Tradução salva em: '{output_filepath}'")
                    translated_count += 1
                else:
                    print(f"❌ Nenhuma resposta válida recebida para '{filename}'. A tradução não foi salva.")

            except Exception as e:
                print(f"❌ Erro ao processar '{filename}': {e}")
    
    print(f"\n--- Processo de tradução finalizado ---")
    print(f"Total de arquivos CSV encontrados: {csv_files_found}")
    print(f"Total de arquivos CSV traduzidos e salvos: {translated_count}")

    if csv_files_found == 0:
        print(f"Nenhum arquivo CSV encontrado na pasta '{input_folder}'.")
    elif translated_count < csv_files_found:
        print("Alguns arquivos CSV podem não ter sido traduzidos. Verifique os avisos acima.")


if __name__ == '__main__':
    main()