import os
import ollama
import re
import time

# --- CONFIGURAÇÃO DE PASTAS ---
caminho_do_projeto = os.path.dirname(os.path.abspath(__file__))
input_folder = os.path.join(caminho_do_projeto, "2_partes_traduzidas")  
output_folder = os.path.join(caminho_do_projeto, "3_partes_verificadas")   

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# --- PROMPT DE LQA (CONTROLE DE QUALIDADE) ---
prompt_sistema = """YOU ARE A SENIOR LOCALIZATION QA SPECIALIST (LQA). 
Your ONLY output is the corrected and finalized CSV content.

Task:
Review and FIX the provided CSV file.

Checklist:
1. **TAGS:** Ensure {0}, %s, <cf>, \\n, etc., are identical to the source and correctly placed.
2. **CSV QUOTING:** If a translation contains a COMMA (,), the entire field MUST be in double quotes (e.g., "Olá, amigo").
3. **QUALITY:** Fix literal/robotic translations to sound natural in pt-BR.
4. **NO CHANGES:** If a line is already perfect, do not change it.

Rules:
- Keep `key,source,Translation` format.
- Output ONLY the raw CSV text.
- No markdown (```), no introductory text, no explanations.
"""

def limpar_resposta_lqa(texto_bruto, cabecalho_original):
    """
    Remove blocos de código e conversas, garantindo a integridade do CSV final.
    """
    if not texto_bruto or not texto_bruto.strip():
        return None

    # 1. Remove qualquer bloco de código markdown
    texto = re.sub(r"```(?:csv|text)?\n?", "", texto_bruto)
    texto = texto.replace("```", "").strip()
    
    linhas = texto.split('\n')
    linhas_limpas = []
    
    # Cabeçalho para comparação
    cabecalho_fixo = cabecalho_original.strip()

    for linha in linhas:
        linha_limpa = linha.strip()
        if not linha_limpa: continue
        
        # Pula frases típicas de conversa da IA
        if linha_limpa.lower().startswith(('here is', 'corrected', 'below', 'sure', 'i have', 'translation', 'csv')):
            continue
            
        # Pula se a IA repetir o cabeçalho no meio
        if "key,source,translation" in linha_limpa.lower():
            continue

        # Adiciona se tiver estrutura de CSV (mínimo 2 vírgulas para as 3 colunas)
        if linha_limpa.count(',') >= 2:
            linhas_limpas.append(linha_limpa)
            
    if not linhas_limpas:
        return None

    # Monta o resultado final com o cabeçalho original no topo
    resultado = [cabecalho_fixo] + linhas_limpas
    return "\n".join(resultado)

# --- LOOP DE VERIFICAÇÃO ---
arquivos = sorted([f for f in os.listdir(input_folder) if f.endswith(".csv")])

print(f"--- INICIANDO LQA CSV COM DEEPSEEK (SISTEMA DE RETENTATIVA) ---\n")

for nome_arquivo in arquivos:
    caminho_in = os.path.join(input_folder, nome_arquivo)
    caminho_out = os.path.join(output_folder, nome_arquivo)
    
    if os.path.exists(caminho_out):
        print(f"[{nome_arquivo}] Já verificado. Pulando...")
        continue

    tentativas_maximas = 3
    sucesso = False

    for tentativa in range(1, tentativas_maximas + 1):
        try:
            with open(caminho_in, 'r', encoding='utf-8') as f:
                linhas_originais = f.readlines()
                cabecalho_original = linhas_originais[0]
                conteudo_atual = "".join(linhas_originais)

            msg_tentativa = f" (Tentativa {tentativa}/{tentativas_maximas})" if tentativa > 1 else ""
            print(f"Revisando: {nome_arquivo}{msg_tentativa}...", end="", flush=True)

            response = ollama.generate(
                model='deepseek-v3.1:671b-cloud',
                system=prompt_sistema,
                prompt=f"REVIEW AND FIX THIS CSV CONTENT:\n\n{conteudo_atual}",
                stream=False,
                options={
                    "temperature": 0.2,  # Baixa temperatura para correção técnica precisa
                    "num_ctx": 16384,
                    "top_p": 0.9,
                    "num_predict": 8192
                }
            )
            
            res_raw = response.get('response', "").strip()
            texto_final = limpar_resposta_lqa(res_raw, cabecalho_original)
            
            # Valida se o resultado tem o cabeçalho + as linhas de dados
            if texto_final and len(texto_final.split('\n')) > 1:
                with open(caminho_out, 'w', encoding='utf-8') as f:
                    f.write(texto_final + '\n')
                print(" ✅ Verificado!")
                sucesso = True
                break
            else:
                raise ValueError("Resposta vazia ou sem linhas de dados válidas")

        except Exception as e:
            if tentativa < tentativas_maximas:
                print(f" ⚠️ Falha no LQA. Tentando novamente em 3s...")
                time.sleep(3)
            else:
                print(f"\n❌ FALHA CRÍTICA em {nome_arquivo} após {tentativas_maximas} tentativas: {e}")

print("\n--- PROCESSO DE LQA CONCLUÍDO! ---")