import json
import os
import subprocess
import shutil
import time
import pyautogui
import pyperclip
import traceback
import sys
from config import *

# Configurações de segurança
pyautogui.PAUSE = 0.3  # Aumentado para mais confiabilidade

def esperar_janela(titulos, timeout=1):
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
        time.sleep(0.3)
    return None

def verificar_pre_requisitos(status):
    """Verifica se todos os pré-requisitos estão atendidos"""
    if not os.path.exists(ARQUIVO_STATUS):
        print("❌ Arquivo de status não encontrado. Execute o Passo 1 primeiro.")
        return False
    
    if not os.path.exists(ARQUIVO_JSON_TRADUZIDO):
        print("❌ Arquivo JSON traduzido não encontrado. Execute o Passo 4 primeiro.")
        return False
    
    if not os.path.exists(UASSET_GUI_PATH):
        print(f"❌ UAssetGUI não encontrado em: {UASSET_GUI_PATH}")
        return False
    
    # Verificar arquivo original
    orig_src = os.path.join(PASTA_JSON_ORIGINAL, status['subpath'], f'{status["nome"]}.json')
    if not os.path.exists(orig_src):
        print(f"❌ Arquivo original não encontrado: {orig_src}")
        return False
    
    return True

def executar_backup_seguro(status):
    """Executa backup do arquivo original"""
    try:
        nome = status['nome']
        subpath = status['subpath']
        
        # Caminhos importantes
        orig_src = os.path.join(PASTA_JSON_ORIGINAL, subpath, f'{nome}.json')
        uexp_orig = orig_src.replace(".json", ".uexp")
        
        print("💾 Executando backup...")
        
        # Criar backup do JSON original
        if os.path.exists(orig_src):
            backup_json = orig_src + ".bak"
            shutil.copy2(orig_src, backup_json)
            print(f"✅ Backup JSON criado: {backup_json}")

        else:
            print("⚠️ Arquivo JSON original não encontrado para backup")
        
        # Criar backup do UEXP se existir
        if os.path.exists(uexp_orig):
            backup_uexp = uexp_orig + ".bak"
            shutil.copy2(uexp_orig, backup_uexp)
            print(f"✅ Backup UEXP criado: {backup_uexp}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante backup: {e}")
        return False

def limpar_arquivos_temporarios(status):
    """Limpa arquivos temporários do processamento e os arquivos originais (após backup)"""
    try:
        nome = status['nome']
        subpath = status['subpath']
        
        # Caminhos dos arquivos originais que devem ser removidos (pois o .bak já existe)
        orig_src = os.path.join(PASTA_JSON_ORIGINAL, subpath, f'{nome}.json')
        uexp_orig = orig_src.replace(".json", ".uexp")
        
        print("🧹 Limpando arquivos temporários e arquivos originais substituídos...")
        
        # Lista expandida de arquivos para remover
        arquivos_para_remover = [
            ARQUIVO_JSON_TRADUZIDO,
            ARQUIVO_STATUS,
            os.path.join(BASE_DIR, f"{nome}_SEGURO.json"),
            orig_src,  # Remove o .json original
            uexp_orig  # Remove o .uexp original
        ]
        
        # Limpar pastas de partes (se houver)
        pastas_para_limpar = [PASTA_PARTES_1, PASTA_PARTES_2, PASTA_PARTES_3]
        
        for pasta in pastas_para_limpar:
            if os.path.exists(pasta):
                for arquivo in os.listdir(pasta):
                    caminho_arquivo = os.path.join(pasta, arquivo)
                    try:
                        if os.path.isfile(caminho_arquivo):
                            os.remove(caminho_arquivo)
                    except Exception as e:
                        print(f"⚠️ Não foi possível remover {caminho_arquivo}: {e}")
        
        # Remover arquivos individuais da lista
        for arquivo in arquivos_para_remover:
            if os.path.exists(arquivo):
                try:
                    os.remove(arquivo)
                    print(f"✅ Removido: {os.path.basename(arquivo)}")
                except Exception as e:
                    # Silenciamos o erro caso o .uexp não exista (nem todo json tem uexp)
                    if not arquivo.endswith(".uexp"):
                        print(f"⚠️ Não foi possível remover {arquivo}: {e}")
        
        print("✅ Limpeza completa concluída!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante limpeza: {e}")
        return False

def executar_conversao_uasset(status):
    """Executa a conversão para UAsset usando UAssetGUI"""
    nome = status['nome']
    subpath = status['subpath']
    
    # Caminhos importantes
    orig_src = os.path.join(PASTA_JSON_ORIGINAL, subpath, f'{nome}.json')
    dest_folder = os.path.join(PASTA_MOD_FINAL, subpath)
    uasset_final = os.path.abspath(os.path.join(dest_folder, f'{nome}.uasset'))
    
    # Criar arquivo seguro
    seguro_json = os.path.join(BASE_DIR, f"{nome}_SEGURO.json")
    try:
        shutil.copy2(ARQUIVO_JSON_TRADUZIDO, seguro_json)
        print(f"📄 Arquivo seguro criado: {seguro_json}")
    except Exception as e:
        print(f"❌ Erro ao criar arquivo seguro: {e}")
        return False
    
    # Garantir que pasta destino existe
    os.makedirs(dest_folder, exist_ok=True)
    
    print(f"🤖 Iniciando UAssetGUI para: {nome}")
    print(f"📍 Destino: {uasset_final}")
    
    # Iniciar UAssetGUI
    try:
        proc = subprocess.Popen([UASSET_GUI_PATH, os.path.abspath(seguro_json), UE_VERSION])
    except Exception as e:
        print(f"❌ Erro ao iniciar UAssetGUI: {e}")
        return False
    
    start_time = time.time()
    fase = "ABERTURA"
    sucesso = False
    
    try:
        while proc.poll() is None and time.time() - start_time < 120:  # Timeout de 2 minutos
            # Verificar e fechar janelas de erro
            win_erro = esperar_janela(["Notice", "Uh oh!", "Error", "Warning", "Erro"], 1)
            if win_erro:
                try:
                    win_erro.activate()
                    time.sleep(0.3)
                    pyautogui.press('enter')  # Fechar com Enter
                    print("⚠️ Janela de erro fechada")
                    time.sleep(0.3)
                except Exception as e:
                    print(f"⚠️ Erro ao lidar com janela de erro: {e}")
            
            # Fase 1: Aguardar abertura e salvar
            if fase == "ABERTURA" and time.time() - start_time > 1:
                win_main = esperar_janela(["UAssetGUI"], 5)
                if win_main:
                    try:
                        win_main.activate()
                        time.sleep(0.3)
                        pyautogui.hotkey('ctrl', 'shift', 's')  # Salvar como
                        fase = "SALVAR_COMO"
                        print("📤 Iniciando salvamento...")
                        time.sleep(0.3)
                    except Exception as e:
                        print(f"❌ Erro ao ativar janela principal: {e}")
            
            # Fase 2: Diálogo Salvar Como
            if fase == "SALVAR_COMO":
                win_save = esperar_janela(["Save As", "Salvar como", "Salvar"], 5)
                if win_save:
                    try:
                        win_save.activate()
                        time.sleep(0.3)
                        
                        # Colocar caminho no clipboard e colar
                        pyperclip.copy(uasset_final)
                        pyautogui.hotkey('ctrl', 'a')  # Selecionar tudo
                        pyautogui.hotkey('ctrl', 'v')  # Colar
                        time.sleep(0.3)
                        pyautogui.press('enter')  # Confirmar
                        
                        # Aguardar possível confirmação de sobrescrita
                        time.sleep(0.3)
                        win_confirm = esperar_janela(["Confirm", "Confirmação"], 3)
                        if win_confirm:
                            pyautogui.press('enter')  # Confirmar sobrescrita
                        
                        fase = "AGUARDAR_CONVERSAO"
                        print("🔄 Aguardando conversão...")
                    except Exception as e:
                        print(f"❌ Erro no diálogo de salvamento: {e}")
            
            # Fase 3: Aguardar conclusão
            if fase == "AGUARDAR_CONVERSAO":
                # Verificar se arquivo foi criado
                if os.path.exists(uasset_final) and os.path.getsize(uasset_final) > 100:
                    sucesso = True
                    print("✅ Arquivo UAsset criado com sucesso!")
                    break
            
            time.sleep(0.3)
        
        # Finalizar processo
        if proc.poll() is None:
            proc.terminate()
            time.sleep(0.3)
            if proc.poll() is None:
                proc.kill()
        
        # Forçar kill se necessário (Windows)
        if sys.platform == "win32":
            os.system("taskkill /f /im UAssetGUI.exe >nul 2>&1")
        
    except Exception as e:
        print(f"❌ Erro durante automação do UAssetGUI: {e}")
        traceback.print_exc()
        proc.terminate()
        return False
    
    return sucesso

def main():
    """Função principal"""
    try:
        print(f"\n{'='*60}")
        print(f"🛠️ INICIANDO CONVERSÃO E CORREÇÃO FINAL")
        print(f"{'='*60}")
        
        # Verificar pré-requisitos
        if not os.path.exists(ARQUIVO_STATUS):
            print("❌ Arquivo de status não encontrado.")
            return False
        
        with open(ARQUIVO_STATUS, 'r', encoding='utf-8') as f:
            status = json.load(f)
        
        print(f"📦 Processando: {status['nome']}")
        print(f"📂 Subpasta: {status['subpath']}")
        
        if not verificar_pre_requisitos(status):
            return False
        
        # Executar conversão
        sucesso_conversao = executar_conversao_uasset(status)
        
        if sucesso_conversao:
            # Executar backup
            executar_backup_seguro(status)
            
            # Limpar arquivos temporários
            limpar_arquivos_temporarios(status)
            
            print(f"\n🎉 PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
            print(f"📁 Arquivo final salvo em: {PASTA_MOD_FINAL}")
            time.sleep(0.3)
            return True
        else:
            print(f"\n❌ Falha na conversão do arquivo {status['nome']}")
            time.sleep(0.3)
            return False
            
    except Exception as e:
        print(f"💥 Erro crítico no script de correção: {e}")
        traceback.print_exc()
        time.sleep(0.3)
        return False

if __name__ == '__main__':
    resultado = main()
    
    if resultado:
        print("\n🏁 Processo final concluído com sucesso!")
        time.sleep(0.3)
    else:
        print("\n🚫 Processo final falhou. Verifique os logs acima.")
        time.sleep(0.3)
        sys.exit(1)