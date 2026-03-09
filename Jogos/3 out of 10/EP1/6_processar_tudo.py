import os
import subprocess
import sys
# Importamos as pastas de partes para poder limpar o workflow
from config import (
    PASTA_JSON_ORIGINAL, 
    PASTA_MOD_FINAL, 
    PASTA_PARTES_1, 
    PASTA_PARTES_2, 
    PASTA_PARTES_3
)

def limpar_workflow():
    """Limpa as pastas temporárias de partes para o próximo arquivo."""
    pastas = [PASTA_PARTES_1, PASTA_PARTES_2, PASTA_PARTES_3]
    for pasta in pastas:
        if os.path.exists(pasta):
            for arquivo in os.listdir(pasta):
                caminho_arquivo = os.path.join(pasta, arquivo)
                try:
                    if os.path.isfile(caminho_arquivo):
                        os.remove(caminho_arquivo)
                except Exception as e:
                    print(f"⚠️ Não foi possível deletar {arquivo}: {e}")

def iniciar_automacao():
    arquivos_alvo = []
    for root, _, files in os.walk(PASTA_JSON_ORIGINAL):
        for f in files:
            # Só pega .json que NÃO sejam .bak
            if f.endswith(".json") and not f.endswith(".bak"):
                arquivos_alvo.append({
                    "nome": f.replace(".json", ""),
                    "subpath": os.path.relpath(root, PASTA_JSON_ORIGINAL)
                })

    print(f"🚀 {len(arquivos_alvo)} arquivos encontrados para processar.")

    for i, item in enumerate(arquivos_alvo, 1):
        nome = item["nome"]
        subpath = item["subpath"]
        caminho_json_original = os.path.join(PASTA_JSON_ORIGINAL, subpath, f"{nome}.json")
        
        # SAVE STATE: Verifica se o .uasset final já existe
        uasset_final = os.path.join(PASTA_MOD_FINAL, subpath, f"{nome}.uasset")
        if os.path.exists(uasset_final):
            print(f"⏩ [{i}/{len(arquivos_alvo)}] {nome} já concluído. Pulando...")
            continue 

        print(f"\n{'='*60}\n📦 [{i}/{len(arquivos_alvo)}] PROCESSANDO: {nome}\n📂 PASTA: {subpath}\n{'='*60}")

        try:
            # Passo 1: Dividir
            resultado_juntar2 = subprocess.run([sys.executable, "1_json_dividir.py", nome, subpath])

            if resultado_juntar2.returncode == 10:

                # 1. Renomeia o arquivo original para .bak para não processá-lo de novo
                if os.path.exists(caminho_json_original):
                    novo_nome_bak = caminho_json_original + ".bak"
                    # Se já existir um .bak antigo, removemos para não dar erro no rename
                    if os.path.exists(novo_nome_bak): os.remove(novo_nome_bak)
                    
                    os.rename(caminho_json_original, novo_nome_bak)
                    print(f"📦 Arquivo original renomeado para: {nome}.json.bak")

                print(f"⏩ Pulando para o próximo arquivo...")
                continue 

            # Se der erro no Passo 4 (que não seja o 10)
            if resultado_juntar2.returncode != 0:
                print(f"❌ Erro crítico no Passo 1 para o arquivo {nome}.")
                break

            # Passo 2: Traduzir
            subprocess.run([sys.executable, "2_json_traduzir_tudo.py"], check=True)

            # Passo 4: Juntar
            print(f"💉 Verificando e Injetando traduções em {nome}...")
            resultado_juntar = subprocess.run([sys.executable, "4_json_juntar.py", nome, subpath])

            # --- LÓGICA DE PULO (CÓDIGO 10) ---
            if resultado_juntar.returncode == 10:
                print(f"✨ {nome}: Textos idênticos ao original detectados.")
                
                # 1. Limpa o workflow (pastas partes_1, 2 e 3)
                print("🧹 Limpando pastas temporárias...")
                limpar_workflow()

                # 2. Renomeia o arquivo original para .bak para não processá-lo de novo
                if os.path.exists(caminho_json_original):
                    novo_nome_bak = caminho_json_original + ".bak"
                    # Se já existir um .bak antigo, removemos para não dar erro no rename
                    if os.path.exists(novo_nome_bak): os.remove(novo_nome_bak)
                    
                    os.rename(caminho_json_original, novo_nome_bak)
                    print(f"📦 Arquivo original renomeado para: {nome}.json.bak")

                print(f"⏩ Pulando para o próximo arquivo...")
                continue 

            # Se der erro no Passo 4 (que não seja o 10)
            if resultado_juntar.returncode != 0:
                print(f"❌ Erro crítico no Passo 4 para o arquivo {nome}.")
                break

            # Passo 5: Corrigir Corrupção (O script 5 geralmente já faz a limpeza final)
            print(f"🛠️  Finalizando e convertendo {nome}...")
            subprocess.run([sys.executable, "5_json_corrigir_corrupcao.py", nome, subpath], check=True)

            print(f"\n✅ SUCESSO: {nome} finalizado.")
            
        except subprocess.CalledProcessError as e:
            print(f"\n❌ ERRO no processo do arquivo {nome}: {e}")
            break 
        except Exception as e:
            print(f"\n⚠️ Erro inesperado: {e}")
            break

if __name__ == "__main__":
    iniciar_automacao()