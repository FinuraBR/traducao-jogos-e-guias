import os
import subprocess
import shutil
import time
import pyautogui
import pyperclip
import traceback
import sys
from typing import List

# --- IMPORTANDO CONFIGURAÇÕES DO CONFIG.PY ---
from config import (
    UASSET_GUI_PATH, UE_VERSION,
    PASTA_RAW, PASTA_FILTRADO, PASTA_JSON_ORIGINAL,
    KEYWORDS_BINARIAS
)

# Configuração de segurança e estabilidade do Robô
pyautogui.PAUSE = 0.4  # Pausa aumentada para mais estabilidade
pyautogui.FAILSAFE = True  # Mouse no canto superior esquerdo para parar

def validar_pre_requisitos():
    """Valida se todos os pré-requisitos estão atendidos"""
    problemas = []
    
    if not os.path.exists(PASTA_RAW):
        problemas.append(f"❌ Pasta RAW não encontrada: {PASTA_RAW}")
    
    if not os.path.exists(UASSET_GUI_PATH):
        problemas.append(f"❌ UAssetGUI não encontrado: {UASSET_GUI_PATH}")
    
    return problemas

def esperar_janela(titulos: List[str], timeout: int = 10):
    """Espera por uma janela específica aparecer"""
    inicio = time.time()
    while time.time() - inicio < timeout:
        for titulo in titulos:
            try:
                janelas = pyautogui.getWindowsWithTitle(titulo)
                for janela in janelas:
                    if janela.visible:
                        return janela
            except Exception as e:
                print(f"⚠️ Erro ao buscar janela '{titulo}': {e}")
        time.sleep(0.5)
    return None

def arquivo_contem_keywords(caminho_arquivo: str) -> bool:
    """Verifica se o arquivo contém alguma das keywords binárias"""
    try:
        with open(caminho_arquivo, 'rb') as f:
            data = f.read()
            return any(keyword in data for keyword in KEYWORDS_BINARIAS)
    except Exception as e:
        print(f"⚠️ Erro ao ler arquivo {caminho_arquivo}: {e}")
        return False

def passo_1_filtrar():
    """Filtra arquivos UAsset que contêm textos localizáveis"""
    print(f"\n{'='*60}")
    print("🔍 PASSO 1: FILTRANDO ARQUIVOS UASSET")
    print(f"{'='*60}")
    
    if not os.path.exists(PASTA_RAW):
        print(f"❌ Pasta RAW não encontrada: {PASTA_RAW}")
        return False
    
    # Criar pastas de destino
    os.makedirs(PASTA_FILTRADO, exist_ok=True)
    os.makedirs(PASTA_JSON_ORIGINAL, exist_ok=True)
    
    arquivos_encontrados = 0
    arquivos_filtrados = 0
    
    print("📁 Buscando arquivos UAsset...")
    
    for root, _, files in os.walk(PASTA_RAW):
        for file in files:
            if file.endswith(".uasset"):
                arquivos_encontrados += 1
                path_src = os.path.join(root, file)
                
                if arquivo_contem_keywords(path_src):
                    # Calcular caminho relativo e destino
                    rel_path = os.path.relpath(path_src, PASTA_RAW)
                    dest = os.path.join(PASTA_FILTRADO, rel_path)
                    
                    # Criar diretório de destino se necessário
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    
                    # Copiar arquivo UAsset
                    shutil.copy2(path_src, dest)
                    
                    # Copiar arquivo UEXP correspondente se existir
                    uexp_src = path_src.replace(".uasset", ".uexp")
                    uexp_dest = dest.replace(".uasset", ".uexp")
                    if os.path.exists(uexp_src):
                        shutil.copy2(uexp_src, uexp_dest)
                    
                    arquivos_filtrados += 1
                    print(f"✅ Filtrado: {rel_path}")
    
    print(f"\n📊 RESUMO DO FILTRO:")
    print(f"   📁 Arquivos encontrados: {arquivos_encontrados}")
    print(f"   ✅ Arquivos filtrados: {arquivos_filtrados}")
    print(f"   ❌ Arquivos ignorados: {arquivos_encontrados - arquivos_filtrados}")
    
    return arquivos_filtrados > 0

def converter_uasset_para_json(uasset_path: str, json_final_path: str, numero: int, total: int):
    """Converte um arquivo UAsset para JSON usando UAssetGUI"""
    rel_path = os.path.relpath(uasset_path, PASTA_FILTRADO)
    
    print(f"[{numero}/{total}] Convertendo: {rel_path}", end=" ", flush=True)
    
    # Verificar se já existe
    if os.path.exists(json_final_path):
        print("⏩ Já existe, pulando...")
        return True
    
    try:
        # Iniciar UAssetGUI
        proc = subprocess.Popen([UASSET_GUI_PATH, os.path.abspath(uasset_path), UE_VERSION])
    except Exception as e:
        print(f"❌ Erro ao iniciar UAssetGUI: {e}")
        return False
    
    start_time = time.time()
    fase = "ABERTURA"
    sucesso = False
    
    try:
        while proc.poll() is None and time.time() - start_time < 60:  # Timeout de 1 minuto
            # Fechar janelas de erro
            janela_erro = esperar_janela(["Notice", "Uh oh!", "Error", "Warning", "Erro"], 1)
            if janela_erro:
                try:
                    janela_erro.activate()
                    time.sleep(0.4)
                    pyautogui.press('enter')
                    print("⚠️", end="", flush=True)
                    time.sleep(0.4)
                except Exception:
                    pass
            
            # Fase 1: Aguardar abertura e iniciar salvamento
            if fase == "ABERTURA" and time.time() - start_time > 2:
                janela_main = esperar_janela(["UAssetGUI"], 5)
                if janela_main:
                    try:
                        janela_main.activate()
                        time.sleep(0.4)
                        pyautogui.hotkey('ctrl', 'shift', 's')  # Salvar como JSON
                        print("💾", end="", flush=True)
                        fase = "SALVAR_COMO"
                        time.sleep(0.4)
                    except Exception as e:
                        print(f"❌ Erro ao ativar janela principal: {e}")
            
            # Fase 2: Diálogo Salvar Como
            if fase == "SALVAR_COMO":
                janela_save = esperar_janela(["Save As", "Salvar como", "Salvar"], 5)
                if janela_save:
                    try:
                        janela_save.activate()
                        time.sleep(0.4)
                        
                        # Colar caminho do arquivo JSON
                        pyperclip.copy(json_final_path)
                        pyautogui.hotkey('ctrl', 'a')  # Selecionar tudo
                        pyautogui.hotkey('ctrl', 'v')  # Colar
                        time.sleep(0.4)
                        pyautogui.press('enter')  # Confirmar
                        
                        # Aguardar possível confirmação de sobrescrita
                        time.sleep(0.4)
                        janela_confirm = esperar_janela(["Confirm", "Confirmação"], 3)
                        if janela_confirm:
                            pyautogui.press('enter')  # Confirmar sobrescrita
                        
                        fase = "AGUARDAR_CONVERSAO"
                        print("🔄", end="", flush=True)
                    except Exception as e:
                        print(f"❌ Erro no diálogo de salvamento: {e}")
            
            # Fase 3: Verificar se arquivo foi criado
            if fase == "AGUARDAR_CONVERSAO":
                if os.path.exists(json_final_path) and os.path.getsize(json_final_path) > 100:
                    sucesso = True
                    print("✅", flush=True)
                    break
            
            time.sleep(0.5)
        
        # Finalizar processo
        if proc.poll() is None:
            proc.terminate()
            time.sleep(0.4)
            if proc.poll() is None:
                proc.kill()
        
        # Forçar kill se necessário (Windows)
        if sys.platform == "win32":
            os.system("taskkill /f /im UAssetGUI.exe >nul 2>&1")
        
    except Exception as e:
        print(f"❌ Erro durante conversão: {e}")
        proc.terminate()
        return False
    
    return sucesso

def passo_2_conversao():
    """Converte arquivos UAsset filtrados para JSON"""
    print(f"\n{'='*60}")
    print("🔧 PASSO 2: CONVERTENDO UASSET PARA JSON")
    print(f"{'='*60}")
    
    if not os.path.exists(PASTA_FILTRADO):
        print(f"❌ Pasta filtrada não encontrada: {PASTA_FILTRADO}")
        return False
    
    # Buscar arquivos UAsset filtrados
    arquivos_uasset = []
    for root, _, files in os.walk(PASTA_FILTRADO):
        for file in files:
            if file.endswith(".uasset"):
                arquivos_uasset.append(os.path.join(root, file))
    
    if not arquivos_uasset:
        print("❌ Nenhum arquivo UAsset encontrado para conversão")
        return False
    
    total = len(arquivos_uasset)
    sucessos = 0
    falhas = 0
    
    print(f"📊 Encontrados {total} arquivos para conversão")
    
    for i, uasset_path in enumerate(arquivos_uasset, 1):
        # Calcular caminho do JSON de destino
        rel_path = os.path.relpath(uasset_path, PASTA_FILTRADO)
        json_final_path = os.path.abspath(
            os.path.join(PASTA_JSON_ORIGINAL, rel_path.replace(".uasset", ".json"))
        )
        
        # Garantir que diretório destino existe
        os.makedirs(os.path.dirname(json_final_path), exist_ok=True)
        
        # Converter arquivo
        if converter_uasset_para_json(uasset_path, json_final_path, i, total):
            sucessos += 1
        else:
            falhas += 1
        
        # Pequena pausa entre conversões
        if i < total:
            time.sleep(0.5)
    
    print(f"\n📊 RESUMO DA CONVERSÃO:")
    print(f"   ✅ Sucessos: {sucessos}")
    print(f"   ❌ Falhas: {falhas}")
    print(f"   📊 Total: {total}")
    
    return falhas == 0

def main():
    """Função principal"""
    try:
        print("🚀 INICIANDO WORKFLOW UASSET PARA JSON")
        print("⚠️  Não toque no computador durante a automação!")
        print(f"{'='*60}")
        
        # Validar pré-requisitos
        problemas = validar_pre_requisitos()
        if problemas:
            print("❌ PROBLEMAS ENCONTRADOS:")
            for problema in problemas:
                print(f"   {problema}")
            return False
        
        # Executar passos
        if not passo_1_filtrar():
            print("❌ Falha no passo 1 (filtro)")
            return False
        
        if not passo_2_conversao():
            print("❌ Falha no passo 2 (conversão)")
            return False
        
        print(f"\n{'='*60}")
        print("🎉 WORKFLOW CONCLUÍDO COM SUCESSO!")
        print(f"📁 JSONs disponíveis em: {PASTA_JSON_ORIGINAL}")
        print(f"{'='*60}")
        return True
        
    except Exception as e:
        print(f"💥 Erro crítico no workflow: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = main()
    
    if not sucesso:
        print("\n🚫 Workflow falhou. Verifique os logs acima.")
        sys.exit(1)
    else:
        print("\n✨ Pronto para iniciar a tradução!")