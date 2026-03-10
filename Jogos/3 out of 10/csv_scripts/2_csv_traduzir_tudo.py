import os
import ollama
import re
import time

# --- CONFIGURAÇÃO DE PASTAS ---
caminho_do_projeto = os.path.dirname(os.path.abspath(__file__))
input_folder = os.path.join(caminho_do_projeto, "1_partes_para_traduzir")  
output_folder = os.path.join(caminho_do_projeto, "2_partes_traduzidas")   

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# --- PROMPT DE LOCALIZAÇÃO DE ALTO NÍVEL ---
prompt_sistema = """YOU ARE A SENIOR GAME LOCALIZATION EXPERT (EN to PT-BR).
Your ONLY output is the processed CSV content.

TASK:
Localize the 3rd column (Translation) based on the 2nd column (source).

STRICT RULES:
1. FORMAT: key,source,Translation
2. DO NOT modify "key" or "source" columns.
3. CSV SAFETY: If the translation contains a comma (,), YOU MUST enclose it in double quotes (").
   Example: Hello, friend -> "Olá, amigo"
4. TAGS: Keep all tags like <cf>, {0}, %s, \\n intact.
5. NO CHATTER: No markdown (```csv), no introductory text, no explanations.
6. OVERWRITE: Fill the 3rd column even if it was empty or had old text.

LOCALIZATION STYLE:
- Natural Brazilian Portuguese.
- Adapt idioms (don't translate literally).
- Maintain the tone of the game.

START PROCESSING NOW."""

def limpar_resposta_ia(texto_bruto, cabecalho_original):
    """
    Remove blocos de código e textos de conversa da IA, mantendo apenas o CSV.
    """
    if not texto_bruto or not texto_bruto.strip():
        return None

    # 1. Remove blocos de código markdown se existirem
    texto = re.sub(r"```(?:csv|text)?\n?", "", texto_bruto)
    texto = texto.replace("```", "").strip()

    linhas = texto.split('\n')
    linhas_limpas = []
    
    # Padroniza o cabeçalho para comparação
    cabecalho_comparar = cabecalho_original.strip().lower()

    for linha in linhas:
        linha_strip = linha.strip()
        
        # Ignora linhas vazias ou conversas comuns da IA
        if not linha_strip: continue
        if linha_strip.lower().startswith(('here', 'sure', 'below', 'note', 'the', '###', 'translation', 'csv')): 
            continue

        # Evita repetir o cabeçalho no meio do arquivo
        if linha_strip.lower() == cabecalho_comparar:
            continue
            
        # Verifica se a linha parece um CSV válido (tem pelo menos duas vírgulas)
        if linha_strip.count(',') >= 2:
            linhas_limpas.append(linha_strip)

    if not linhas_limpas:
        return None

    # Garante que o cabeçalho original seja a primeira linha
    resultado = [cabecalho_original.strip()] + linhas_limpas
    return "\n".join(resultado)

# --- LOOP DE TRADUÇÃO ---
arquivos = sorted([f for f in os.listdir(input_folder) if f.endswith(".csv")])

print(f"--- INICIANDO TRADUÇÃO DE CSV COM DEEPSEEK (SISTEMA DE RETENTATIVA) ---\n")

for nome_arquivo in arquivos:
    caminho_in = os.path.join(input_folder, nome_arquivo)
    caminho_out = os.path.join(output_folder, nome_arquivo)
    
    # Pula se já existir
    if os.path.exists(caminho_out):
        print(f"[{nome_arquivo}] Já existe. Pulando...")
        continue
        
    tentativas_maximas = 3
    sucesso = False

    for tentativa in range(1, tentativas_maximas + 1):
        try:
            with open(caminho_in, 'r', encoding='utf-8') as f:
                linhas_originais = f.readlines()
                cabecalho = linhas_originais[0]
                conteudo_para_ia = "".join(linhas_originais)

            msg_tentativa = f" (Tentativa {tentativa}/{tentativas_maximas})" if tentativa > 1 else ""
            print(f"Traduzindo: {nome_arquivo}{msg_tentativa}...", end="", flush=True)
            
            response = ollama.generate(
                model='deepseek-v3.1:671b-cloud', 
                system=prompt_sistema,
                prompt=conteudo_para_ia,
                stream=False,
                options={
                    "temperature": 0.6,
                    "num_ctx": 16384,
                    "top_p": 0.95,
                    "num_predict": 8192
                }
            )

            res_raw = response.get('response', "").strip()
            texto_final = limpar_resposta_ia(res_raw, cabecalho)

            if texto_final and len(texto_final.split('\n')) > 1:
                with open(caminho_out, 'w', encoding='utf-8') as f:
                    f.write(texto_final + '\n')
                print(" ✅ OK!")
                sucesso = True
                break
            else:
                raise ValueError("Resposta vazia ou formato CSV inválido")

        except Exception as e:
            if tentativa < tentativas_maximas:
                print(f" ⚠️ Erro na IA/Rede. Tentando novamente em 3s...")
                time.sleep(3)
            else:
                print(f"\n❌ FALHA CRÍTICA em {nome_arquivo} após {tentativas_maximas} tentativas: {e}")

print("\n--- PROCESSO DE TRADUÇÃO CSV CONCLUÍDO! ---")