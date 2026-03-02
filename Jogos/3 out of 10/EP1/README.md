# Tradução / Open-Source - 3 out of 10 EP1 (PT-BR)

**Status do Projeto:** ⚠️ Jogável / Revisão Manual Pendente 

**Traduzido por:** ツFinuraBR

---

## 📌 Estado Atual da Tradução

- **Progresso:**

| Episódio | Status | Obs. |
| :--- | :---: | :--- |
| **Episódio 1** | ✅ Concluído | Revisão Manual Pendente |
| **Episódio 2** | 🔄 Em Andamento ||
| **Episódio 3** | ❌ Pendente ||
| **Episódio 4** | ❌ Pendente ||
| **Episódio 5** | ❌ Pendente ||

---

## 🛠️ Como Instalar a Tradução (Para Jogadores)

A instalação foi feita para ser a mais simples possível.

1. Vá até a aba **[Releases](https://github.com/FinuraBR/traducao-jogos-e-guias/releases/tag/3-out-of-10-EP1)** deste repositório (lado direito da página) e baixe a versão `.zip` mais recente.
2. Abra a pasta onde o seu jogo está instalado (A **pasta raiz**, onde fica o arquivo `ThreeTen.exe`).
3. Extraia todo o conteúdo do `.zip` baixado para dentro dessa pasta.
4. Abra o jogo e divirta-se! A tradução deve carregar automaticamente.

---

## 🤝 Workflow e Scripts (Para Desenvolvedores/Tradutores)

Se você tem interesse em como essa tradução foi feita ou quer ajudar a melhorar os scripts, aqui está o fluxo de trabalho que utilizei. O processo é automatizado em Python para lidar com arquivos da Unreal Engine (`.locres` e `.uasset` convertidos para `.json`).

### 🗂️ Estrutura do Processo
O fluxo de tradução segue estritamente esta ordem para garantir a integridade dos arquivos:

1.  **Divisão (`1_json_dividir`):** O arquivo original é fatiado em pequenos pedaços JSON/CSV para evitar que a IA se perca ou corte a resposta.
2.  **Tradução (`2_json_traduzir_tudo.py`):** A IA (via Ollama/DeepSeek) processa os arquivos, focando na criatividade e adaptação para PT-BR.
3.  **Verificação (`3_json_verificar.py`):** Uma segunda passada de IA (LQA) com temperatura baixa verifica erros de sintaxe JSON e garante que as tags (`<cf>`, `{0}`) não foram quebradas.
4.  **União (`4_json_juntar.py`):** Os pedaços traduzidos e verificados são remontados no arquivo original.
5.  **Resgate (`5_json_corrigir_corrupcao.py`):** O "Script Cirurgião" pega apenas os textos traduzidos do arquivo final e injeta cirurgicamente no arquivo original intacto, prevenindo corrupção de dados da Engine.

### Ferramentas Utilizadas
- **FModel:** Para extração dos arquivos `.pak`.
- **UAssetGUI:** Para converter arquivos `.uasset` (DataTables) em JSON e vice-versa.
- **UnrealPak:** Para empacotar o mod final.
- **Python + IA:** Para automação da tradução.

### 📜 Licença e Créditos
Este projeto é de código aberto para a comunidade. A única exigência caso você continue o projeto, publique atualizações ou crie um instalador automático no futuro é **manter o meu nome nos créditos como criador original da base da tradução**.

**Créditos Iniciais:** ツFinuraBR
