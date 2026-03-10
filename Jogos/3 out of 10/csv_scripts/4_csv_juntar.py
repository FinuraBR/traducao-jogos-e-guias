import os
import glob

# --- CONFIGURAÇÕES ---
caminho_do_projeto = os.path.dirname(os.path.abspath(__file__))
# Pasta onde estão os arquivos traduzidos e revisados
pasta_arquivos_traduzidos = os.path.join(caminho_do_projeto, '2_partes_traduzidas') # Ajuste se usar '3_partes_verificadas'
arquivo_final = os.path.join(caminho_do_projeto, 'csv_PTBR.locres.csv')

def juntar_csv_seguro():
    # Pega todos os arquivos .csv em ordem (parte_001, parte_002...)
    arquivos_partes = sorted(glob.glob(os.path.join(pasta_arquivos_traduzidos, '*.csv')))

    if not arquivos_partes:
        print(f"❌ Nenhum arquivo CSV encontrado em: {pasta_arquivos_traduzidos}")
        return

    print(f"--- INICIANDO UNIÃO DE {len(arquivos_partes)} ARQUIVOS ---")
    
    linhas_totais = 0
    primeiro_arquivo = True

    with open(arquivo_final, 'w', encoding='utf-8') as f_out:
        for arquivo in arquivos_partes:
            nome_simples = os.path.basename(arquivo)
            
            with open(arquivo, 'r', encoding='utf-8') as f_in:
                linhas = f_in.readlines()
                
                if not linhas:
                    print(f"⚠️ Aviso: O arquivo {nome_simples} está vazio. Pulando...")
                    continue

                # No primeiro arquivo, pegamos o cabeçalho (linha 0)
                if primeiro_arquivo:
                    f_out.write(linhas[0])
                    primeiro_arquivo = False
                    # Se o arquivo só tiver o cabeçalho, pula
                    if len(linhas) < 2: continue
                
                # Para todos os arquivos, pegamos da linha 1 em diante (pulando o cabeçalho)
                dados_traduzidos = linhas[1:]
                
                for linha in dados_traduzidos:
                    conteudo = linha.strip()
                    if conteudo:  # Só escreve se a linha não for apenas espaços/vazia
                        # Escreve a linha e garante que tenha UMA quebra de linha no final
                        f_out.write(conteudo + '\n')
                        linhas_totais += 1
            
            print(f"✅ Integrado: {nome_simples}")

    print("-" * 30)
    print(f"🚀 SUCESSO! Arquivo final gerado: {os.path.basename(arquivo_final)}")
    print(f"📊 Total de linhas de tradução unidas: {linhas_totais}")
    print("DICA: Compare este número com o total de linhas do arquivo original antes da divisão.")

if __name__ == '__main__':
    juntar_csv_seguro()