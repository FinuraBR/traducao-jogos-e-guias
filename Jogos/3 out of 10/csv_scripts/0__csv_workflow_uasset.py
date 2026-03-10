import os
import subprocess
import shutil
import sys

# ==============================================================================
#                               CONFIGURAÇÕES
# ==============================================================================

# Caminho para o executável da ferramenta
TOOL_PATH = r"D:\Ferramentas\UE4LocalizationsTool.exe"

# Pasta onde estão os seus arquivos .uasset (ex: PASTA_FILTRADO)
INPUT_UASSET_DIR = r"D:\EP1\2_FILTRADO"

# Pasta onde você quer salvar os arquivos para tradução (CSV/TXT)
OUTPUT_CSV_DIR = r"D:\EP1\1_RAW"

# Flags de segurança:
# -nn: NoName (Ignora IDs de lógica/programação que causam crash)
# -f: Filter (Aplica os filtros que você configurou na interface da ferramenta)
FLAGS = ["-nn"]

# ==============================================================================
#                               EXECUÇÃO
# ==============================================================================

def exportar_para_traducao():
    # Validações iniciais
    if not os.path.exists(TOOL_PATH):
        print(f"❌ Erro: Ferramenta não encontrada em {TOOL_PATH}")
        return

    if not os.path.exists(INPUT_UASSET_DIR):
        print(f"❌ Erro: Pasta de entrada não encontrada em {INPUT_UASSET_DIR}")
        return

    # Criar pasta de saída se não existir
    os.makedirs(OUTPUT_CSV_DIR, exist_ok=True)

    # Buscar todos os uassets
    arquivos_uasset = []
    for root, _, files in os.walk(INPUT_UASSET_DIR):
        for file in files:
            if file.endswith(".uasset"):
                arquivos_uasset.append(os.path.join(root, file))

    print(f"🚀 Iniciando exportação de {len(arquivos_uasset)} arquivos...")

    sucessos = 0
    vazios = 0

    for i, uasset_path in enumerate(arquivos_uasset, 1):
        rel_path = os.path.relpath(uasset_path, INPUT_UASSET_DIR)
        print(f"[{i}/{len(arquivos_uasset)}] Exportando: {rel_path}...", end=" ", flush=True)

        try:
            # O comando da ferramenta: export <arquivo> -nn -f
            comando = [TOOL_PATH, "export", os.path.abspath(uasset_path)] + FLAGS
            
            # Executa o comando
            resultado = subprocess.run(comando, capture_output=True, text=True)

            if resultado.returncode == 0:
                # A ferramenta gera um arquivo com o mesmo nome + .txt no local do uasset
                txt_gerado = uasset_path + ".txt"
                
                if os.path.exists(txt_gerado):
                    # Define o destino (mudando a extensão para .csv para facilitar abertura)
                    # Se preferir manter .txt, basta mudar abaixo
                    nome_csv = rel_path + ".csv" 
                    destino_final = os.path.join(OUTPUT_CSV_DIR, nome_csv)
                    
                    # Cria a subpasta no destino se não existir
                    os.makedirs(os.path.dirname(destino_final), exist_ok=True)
                    
                    # Move e renomeia
                    shutil.move(txt_gerado, destino_final)
                    print("✅")
                    sucessos += 1
                else:
                    # Se o arquivo não foi gerado, é porque o filtro -f barrou tudo (arquivo técnico)
                    print("⏩ (Ignorado pelo filtro)")
                    vazios += 1
            else:
                print(f"❌ Erro na ferramenta: {resultado.stderr}")

        except Exception as e:
            print(f"💥 Falha crítica: {e}")

    print(f"\n{'='*60}")
    print(f"🏁 PROCESSO FINALIZADO!")
    print(f"✅ Exportados com sucesso: {sucessos}")
    print(f"⏩ Ignorados (sem texto útil): {vazios}")
    print(f"📁 Pasta de saída: {OUTPUT_CSV_DIR}")
    print(f"{'='*60}")

if __name__ == "__main__":
    exportar_para_traducao()