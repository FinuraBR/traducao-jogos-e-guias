import os
from config import PASTA_JSON_ORIGINAL

def restaurar_bak():
    print(f"🔄 Procurando arquivos .bak em {PASTA_JSON_ORIGINAL}...")
    count = 0
    
    # os.walk faz a varredura em todas as subpastas
    for root, _, files in os.walk(PASTA_JSON_ORIGINAL):
        for file in files:
            if file.endswith(".json.bak"):
                old_path = os.path.join(root, file)
                # Remove o ".bak" do final do nome
                new_path = os.path.join(root, file.replace(".json.bak", ".json"))
                
                try:
                    os.rename(old_path, new_path)
                    print(f"✅ Restaurado: {file} -> {os.path.basename(new_path)}")
                    count += 1
                except Exception as e:
                    print(f"❌ Erro ao renomear {file}: {e}")
    
    if count == 0:
        print("✨ Nenhum arquivo .bak encontrado.")
    else:
        print(f"\n🚀 Total de arquivos restaurados: {count}")

if __name__ == '__main__':
    restaurar_bak()