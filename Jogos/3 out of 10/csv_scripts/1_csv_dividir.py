import os
import csv
import io

# --- CONFIGURAÇÕES ---
caminho_do_projeto = os.path.dirname(os.path.abspath(__file__))
arquivo_original = os.path.join(caminho_do_projeto, 'E05.locres.csv')
pasta_saida = os.path.join(caminho_do_projeto, '1_partes_para_traduzir')

# LIMITE PARA IA (DeepSeek/Ollama)
# 8000 caracteres garante que a IA processe e devolva a tradução sem "cortar" o texto.
LIMITE_CARACTERES_POR_ARQUIVO = 3000 

def dividir_csv_inteligente():
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)

    print(f"Lendo {arquivo_original}...")

    try:
        with open(arquivo_original, 'r', encoding='utf-8', newline='') as f:
            # Usamos o csv.DictReader para entender as colunas automaticamente
            leitor = csv.DictReader(f)
            cabecalho = leitor.fieldnames
            linhas_data = list(leitor)
    except Exception as e:
        print(f"❌ ERRO ao ler arquivo: {e}")
        return

    if not linhas_data:
        print("O arquivo está vazio!")
        return

    print(f"✅ Encontrados {len(linhas_data)} registros. Dividindo por tamanho de texto...")

    buffer_linhas = []
    tamanho_atual_buffer = 0
    contador_arquivos = 1

    for row in linhas_data:
        # Transformamos a linha em string para medir o tamanho real que a IA verá
        output = io.StringIO()
        escritor_temp = csv.DictWriter(output, fieldnames=cabecalho)
        escritor_temp.writerow(row)
        linha_texto = output.getvalue()
        
        tamanho_linha = len(linha_texto)

        # Se estourar o limite, salva o buffer atual
        if (tamanho_atual_buffer + tamanho_linha) > LIMITE_CARACTERES_POR_ARQUIVO and buffer_linhas:
            salvar_parte_csv(cabecalho, buffer_linhas, contador_arquivos)
            contador_arquivos += 1
            buffer_linhas = []
            tamanho_atual_buffer = 0

        buffer_linhas.append(row)
        tamanho_atual_buffer += tamanho_linha

    # Salva o que sobrou
    if buffer_linhas:
        salvar_parte_csv(cabecalho, buffer_linhas, contador_arquivos)

    print(f"\n🚀 Sucesso! {len(linhas_data)} entradas divididas em {contador_arquivos} arquivos.")
    print(f"Pasta: {pasta_saida}")

def salvar_parte_csv(cabecalho, dados, numero_parte):
    nome_arquivo = os.path.join(pasta_saida, f'parte_{numero_parte:03d}.csv')
    
    with open(nome_arquivo, 'w', encoding='utf-8', newline='') as f_out:
        escritor = csv.DictWriter(f_out, fieldnames=cabecalho)
        escritor.writeheader() # Escreve key,source,Translation
        escritor.writerows(dados)
    
    print(f"  -> Gerado: parte_{numero_parte:03d}.csv ({len(dados)} entradas)")

if __name__ == '__main__':
    dividir_csv_inteligente()