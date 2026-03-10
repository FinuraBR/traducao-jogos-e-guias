import json
import os
import sys
import re

# ==============================================================================
#                      CONFIGURAÇÃO DE REGRAS ESTRITAS
# ==============================================================================

# 1. OBRIGATÓRIO: O HistoryType deve ser exatamente este
REQUIRED_HISTORY_TYPE = "Base"

# 2. PROIBIDO: Se a Flag contiver isso, o item é descartado
FORBIDDEN_FLAG = "Immutable"

# 3. TIPOS DE OBJETO (Mantemos os tipos que carregam propriedades de texto)
WHITELIST_TYPES = [
    "TextProperty", 
    "TextPropertyData", 
    "FStringTable", 
    "StringTableExport"
]

# 4. BLACKLIST TÉCNICA (Não importa se é maiúscula ou minúscula)
# Se o texto for IGUAL a um destes, será ignorado.
BLACKLIST_CONTEUDO = [
    "none", "true", "false", "diffusemap", "normalmap", "specularmap",
    "roughnessmap", "opacitymap", "emissivemap", "maskmap", "parameter",
    "texture", "material", "instance", "actor", "component", "token"
]

# 5. NOMES DE PROPRIEDADE BLOQUEADOS
# Se a variável tiver um destes nomes, ignoramos o conteúdo.
BLACKLIST_NOMES_VARIAVEL = [
    "internalname", "classname", "tagname"
]

# 6. FILTROS DE SEGURANÇA (Regex)
REGEX_TECHNICAL = re.compile(
    r'^/Game/|^/Engine/|'             # Caminhos internos
    r'^[a-fA-F0-9-]{32,}$|'           # GUIDs/Hashes
    r'^[a-zA-Z0-9_/.]+\.[a-zA-Z0-9]{2,4}$' # Nomes de arquivos
)

# ==============================================================================
#                            LÓGICA DE FILTRAGEM
# ==============================================================================

def eh_texto_valido(obj, texto):
    """Verificações básicas de conteúdo para evitar quebra de engine"""
    if not texto or not isinstance(texto, str) or not texto.strip():
        return False
    
    t_limpo = texto.strip()
    t_lower = t_limpo.lower()

    # 1. Verifica Blacklist de Conteúdo (Case-insensitive)
    if t_lower in BLACKLIST_CONTEUDO:
        return False

    # 2. Verifica Nome da Variável (Case-insensitive)
    nome_var = str(obj.get("Name", "")).lower()
    if nome_var in BLACKLIST_NOMES_VARIAVEL:
        return False

    # 3. Ignora se for apenas um ID técnico ou caminho via Regex
    if REGEX_TECHNICAL.match(t_limpo):
        return False
    
    # 4. Se for uma palavra única com underline, geralmente é ID interno
    if " " not in t_limpo and "_" in t_limpo:
        return False

    return True

def extrair_recursivo(obj, lista, path=""):
    if isinstance(obj, dict):
        # --- VERIFICAÇÃO DAS REGRAS ESTRITAS ---
        
        history = obj.get("HistoryType", "")
        flags = str(obj.get("Flags", ""))

        # REGRA 1: HistoryType "Base" | REGRA 2: Sem Flag "Immutable"
        if history == REQUIRED_HISTORY_TYPE and FORBIDDEN_FLAG not in flags:
            
            # Verifica o tipo do objeto
            tipo = obj.get("Type", obj.get("$type", ""))
            if any(t in tipo for t in WHITELIST_TYPES):
                
                # Procura as chaves de conteúdo
                for key in ["LocalizedString", "SourceString", "CultureInvariantString", "DisplayString"]:
                    if key in obj:
                        valor = obj.get(key)
                        # Passamos o objeto 'obj' inteiro para verificar o 'Name' na função
                        if eh_texto_valido(obj, valor):
                            lista.append({
                                "p": f"{path}.{key}" if path else key,
                                "t": valor
                            })
                            return 

        # Continua navegando no JSON
        for k, v in obj.items():
            if k in ["Namespace", "Key", "Guid", "Type", "$type", "Flags", "Class", "Outer"]:
                continue
            extrair_recursivo(v, lista, f"{path}.{k}" if path else k)
                
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            extrair_recursivo(item, lista, f"{path}[{i}]")

# ==============================================================================
#                        EXECUÇÃO E EXPORTAÇÃO
# ==============================================================================

from config import PASTA_JSON_ORIGINAL, PASTA_PARTES_1, ARQUIVO_STATUS, LIMITE_CARACTERES_POR_PARTE

def main():
    print(f"🔍 Extraindo: History='{REQUIRED_HISTORY_TYPE}' (Sem '{FORBIDDEN_FLAG}')")
    
    alvo = None
    for root, _, files in os.walk(PASTA_JSON_ORIGINAL):
        for f in files:
            if f.endswith(".json") and not f.endswith(".bak"):
                alvo = {"nome": f.replace(".json", ""), "subpath": os.path.relpath(root, PASTA_JSON_ORIGINAL)}
                break
        if alvo: break
    
    if not alvo: 
        print("✨ Tudo limpo!")
        return

    arquivo_path = os.path.join(PASTA_JSON_ORIGINAL, alvo['subpath'], alvo['nome'] + ".json")
    with open(arquivo_path, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    with open(ARQUIVO_STATUS, 'w', encoding='utf-8') as f: 
        json.dump(alvo, f, indent=2)

    lista_final = []
    extrair_recursivo(dados, lista_final)
    
    if not lista_final:
        print(f"⚠️ Nenhum item seguro encontrado.")
        sys.exit(10)

    # Divisão para IA
    partes, bloco, count = [], [], 0
    for item in lista_final:
        tamanho = len(json.dumps(item, ensure_ascii=False))
        if (count + tamanho) > LIMITE_CARACTERES_POR_PARTE and bloco:
            partes.append(bloco)
            bloco, count = [], 0
        bloco.append(item)
        count += tamanho
    if bloco: partes.append(bloco)

    os.makedirs(PASTA_PARTES_1, exist_ok=True)
    for idx, conteudo in enumerate(partes):
        with open(os.path.join(PASTA_PARTES_1, f'parte_{idx+1:03d}.json'), 'w', encoding='utf-8') as f:
            json.dump(conteudo, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Extraídos {len(lista_final)} itens em {len(partes)} partes.")
    sys.exit(0)

if __name__ == '__main__':
    main()