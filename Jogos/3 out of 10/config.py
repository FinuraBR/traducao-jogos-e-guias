import os
from typing import List

# === CONFIGURAÇÃO BÁSICA ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PASTA_RAW = r"D:\EP1\1_RAW"
PASTA_FILTRADO = r"D:\EP1\2_FILTRADO"

# === CONFIGURAÇÃO DE FERRAMENTAS EXTERNAS ===
UASSET_GUI_PATH = r"D:\Ferramentas\UAssetGUI.exe"
UE_VERSION = "4.24"

LIMITE_CARACTERES_POR_PARTE = 3000

# --- CONFIGURAÇÃO OPENROUTER ---
USA_EXTERNO = True
API_KEY = ""
# Modelo DeepSeek V3 (ou R1 para raciocínio pesado)
MODELO_EXTERNO = ["qwen/qwen3.5-122b-a10b"] # 'qwen/qwen3.5-397b-a17b' ou 'qwen/qwen3.5-122b-a10b' ou 'openai/gpt-4o' Ou 'google/gemini-3.1-flash-lite-preview' ou outro modelo Puter/OpenRouter

# === CONFIGURAÇÃO DA IA ===
MODELO_IA = "deepseek-v3.1:671b-cloud" # "qwen3:8b", "deepseek-v3.1:671b-cloud"
TEMP_TRADUCAO = 0.6          # Temperatura mais criativa para tradução
TEMP_VERIFICACAO = 0.3       # Temperatura mais conservadora para verificação
CONTEXTO_IA = 16384          # Context window size
LIMITE_RESPOSTA = 8192       # Limite de tokens por resposta

# === ESTRUTURA DE PASTAS ===
# Pastas de origem e destino
PASTA_JSON_ORIGINAL = os.path.join(BASE_DIR, "3_JSON_ORIGINAL")
PASTA_MOD_FINAL = os.path.join(BASE_DIR, "Traducao_PTBR_P")

# Pastas de processamento intermediário
PASTA_PARTES_1 = os.path.join(BASE_DIR, "4_partes_para_traduzir")      # Dividido
PASTA_PARTES_2 = os.path.join(BASE_DIR, "5_partes_traduzidas")         # Traduzido
PASTA_PARTES_3 = os.path.join(BASE_DIR, "6_partes_verificadas")       # Verificado

# === ARQUIVOS DE CONTROLE ===
ARQUIVO_JSON_TRADUZIDO = os.path.join(BASE_DIR, "json_PTBR.json")      # JSON final traduzido
ARQUIVO_STATUS = os.path.join(BASE_DIR, "projeto_status.json")        # Status do processamento atual

# === VALIDAÇÃO DE CONFIGURAÇÃO ===
def validar_configuracao():
    """Valida se todas as configurações estão corretas"""
    problemas = []
    
    # Verificar se UAssetGUI existe
    if not os.path.exists(UASSET_GUI_PATH):
        problemas.append(f"❌ UAssetGUI não encontrado: {UASSET_GUI_PATH}")
    
    # Verificar se pastas principais existem
    pastas_obrigatorias = [
        PASTA_JSON_ORIGINAL,
        PASTA_MOD_FINAL
    ]
    
    for pasta in pastas_obrigatorias:
        if not os.path.exists(pasta):
            problemas.append(f"⚠️ Pasta não existe: {pasta}")
    
    # Verificar se pastas de trabalho podem ser criadas
    pastas_trabalho = [
        PASTA_PARTES_1,
        PASTA_PARTES_2,
        PASTA_PARTES_3
    ]
    
    for pasta in pastas_trabalho:
        try:
            os.makedirs(pasta, exist_ok=True)
        except Exception as e:
            problemas.append(f"❌ Não foi possível criar pasta {pasta}: {e}")
    
    return problemas

# === KEYWORDS PARA FILTRO BINÁRIO (Passo 0) ===
KEYWORDS_BINARIAS: List[bytes] = [
    # UTF-8
    b"LocalizedString",
    b"CultureInvariantString", 
    b"TextProperty",
    b"SourceString",
    
    # UTF-16 Little Endian (com null bytes)
    b"L\x00o\x00c\x00a\x00l\x00i\x00z\x00e\x00d\x00S\x00t\x00r\x00i\x00n\x00g\x00",
    b"C\x00u\x00l\x00t\x00u\x00r\x00e\x00I\x00n\x00v\x00a\x00r\x00i\x00a\x00n\x00t\x00S\x00t\x00r\x00i\x00n\x00g\x00",
    b"T\x00e\x00x\x00t\x00P\x00r\x00o\x00p\x00e\x00r\x00t\x00y\x00",
    b"S\x00o\x00u\x00r\x00c\x00e\x00S\x00t\x00r\x00i\x00n\x00g\x00"
]

# === CONSTANTES ÚTEIS ===
TIMEOUT_PADRAO = 3600  # 1 hora em segundos
MAX_WORKERS_PADRAO = 1  # Número padrão de workers paralelos

# === FUNÇÕES ÚTEIS ===
def criar_estrutura_pastas():
    """Cria todas as pastas necessárias para o processo"""
    pastas = [
        PASTA_JSON_ORIGINAL,
        PASTA_MOD_FINAL,
        PASTA_PARTES_1,
        PASTA_PARTES_2,
        PASTA_PARTES_3
    ]
    
    for pasta in pastas:
        os.makedirs(pasta, exist_ok=True)
        print(f"✅ Pasta garantida: {pasta}")

def limpar_arquivos_temporarios():
    """Limpa arquivos temporários de processamento"""
    arquivos_temp = [
        ARQUIVO_JSON_TRADUZIDO,
        ARQUIVO_STATUS
    ]
    
    for arquivo in arquivos_temp:
        try:
            if os.path.exists(arquivo):
                os.remove(arquivo)
                print(f"🧹 Limpo: {arquivo}")
        except Exception as e:
            print(f"⚠️ Não foi possível limpar {arquivo}: {e}")

# === VALIDAÇÃO INICIAL ===
if __name__ == "__main__":
    print("🔍 Validando configuração...")
    problemas = validar_configuracao()
    
    if problemas:
        print("\n⚠️ PROBLEMAS ENCONTRADOS:")
        for problema in problemas:
            print(f"   {problema}")
    else:
        print("✅ Configuração válida!")
    
    # Criar estrutura de pastas
    criar_estrutura_pastas()