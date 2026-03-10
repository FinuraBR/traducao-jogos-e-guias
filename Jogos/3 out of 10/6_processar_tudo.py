import os
import subprocess
import sys
import msvcrt  # Biblioteca para detectar teclas no Windows

from config import (
    PASTA_JSON_ORIGINAL, 
    PASTA_MOD_FINAL, 
    PASTA_PARTES_1, 
    PASTA_PARTES_2, 
    PASTA_PARTES_3
)

def verificar_pausa():
    """Verifica se a tecla 'Q' foi pressionada para pausar o processo."""
    if msvcrt.kbhit():
        tecla = msvcrt.getch().decode('utf-8').lower()
        if tecla == 'q':
            print("\n\n🛑 PAUSA SOLICITADA! Finalizando arquivo atual e parando...")
            return True
    return False

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
    try:
        arquivos_alvo = []
        for root, _, files in os.walk(PASTA_JSON_ORIGINAL):
            for f in files:
                if f.endswith(".json") and not f.endswith(".bak"):
                    arquivos_alvo.append({
                        "nome": f.replace(".json", ""),
                        "subpath": os.path.relpath(root, PASTA_JSON_ORIGINAL)
                    })

        print(f"🚀 {len(arquivos_alvo)} arquivos encontrados para processar.")
        print("⌨️  DICA: Pressione 'Q' a qualquer momento para PARAR após o arquivo atual.\n")

        for i, item in enumerate(arquivos_alvo, 1):
            # --- VERIFICAÇÃO DE PAUSA NO INÍCIO DO LOOP ---
            if verificar_pausa(): break

            nome = item["nome"]
            subpath = item["subpath"]
            caminho_json_original = os.path.join(PASTA_JSON_ORIGINAL, subpath, f"{nome}.json")
            
            uasset_final = os.path.join(PASTA_MOD_FINAL, subpath, f"{nome}.uasset")
            if os.path.exists(uasset_final):
                print(f"⏩ [{i}/{len(arquivos_alvo)}] {nome} já concluído. Pulando...")
                continue 

            print(f"\n{'='*60}\n📦 [{i}/{len(arquivos_alvo)}] PROCESSANDO: {nome}\n📂 PASTA: {subpath}\n{'='*60}")

            try:
                # Passo 1: Dividir
                resultado_dividir = subprocess.run([sys.executable, "1_json_dividir.py", nome, subpath])

                if resultado_dividir.returncode == 10:
                    if os.path.exists(caminho_json_original):
                        novo_nome_bak = caminho_json_original + ".bak"
                        if os.path.exists(novo_nome_bak): os.remove(novo_nome_bak)
                        os.rename(caminho_json_original, novo_nome_bak)
                        print(f"📦 Arquivo original renomeado para: {nome}.json.bak")
                    continue 

                if resultado_dividir.returncode != 0:
                    print(f"❌ Erro crítico no Passo 1 para o arquivo {nome}.")
                    break

                # Passo 2: Traduzir
                subprocess.run([sys.executable, "2_json_traduzir_tudo.py"], check=True)

                # Passo 4: Juntar
                print(f"💉 Verificando e Injetando traduções em {nome}...")
                resultado_juntar = subprocess.run([sys.executable, "4_json_juntar.py", nome, subpath])

                if resultado_juntar.returncode == 10:
                    print(f"✨ {nome}: Textos idênticos ao original. Pulando...")
                    limpar_workflow()
                    if os.path.exists(caminho_json_original):
                        novo_nome_bak = caminho_json_original + ".bak"
                        if os.path.exists(novo_nome_bak): os.remove(novo_nome_bak)
                        os.rename(caminho_json_original, novo_nome_bak)
                    continue 

                if resultado_juntar.returncode != 0:
                    print(f"❌ Erro crítico no Passo 4 para o arquivo {nome}.")
                    break

                # Passo 5: Corrigir Corrupção e UAssetGUI
                print(f"🛠️  Finalizando e convertendo {nome}...")
                subprocess.run([sys.executable, "5_json_corrigir_corrupcao.py", nome, subpath], check=True)

                print(f"\n✅ SUCESSO: {nome} finalizado.")
                
            except subprocess.CalledProcessError as e:
                print(f"\n❌ ERRO no subprocesso: {e}")
                break 
            
            # --- VERIFICAÇÃO DE PAUSA NO FINAL DO LOOP ---
            if verificar_pausa(): break

    except KeyboardInterrupt:
        print("\n\n👋 Interrupção forçada pelo usuário (Ctrl+C). Saindo com segurança...")
    except Exception as e:
        print(f"\n⚠️ Erro inesperado: {e}")
    finally:
        print("\n🏁 Automação encerrada.")

if __name__ == "__main__":
    iniciar_automacao()