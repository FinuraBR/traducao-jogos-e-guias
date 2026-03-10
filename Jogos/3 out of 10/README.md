# Tradução / Open-Source - 3 out of 10 (PT-BR)

---

## 📌 Progresso e Status

O projeto visa entregar uma **base funcional** para todos os episódios. O conteúdo traduzido é compreensível para a progressão e entendimento da história, servindo como ponto de partida para possíveis refinamentos futuros pela comunidade (ou por mim kk).

| Episódio | Status | Observação |
| :--- | :---: | :--- |
| **Episódio 1** | ✅ Concluido ||
| **Episódio 2** | ⌛ Em Andamento ||
| **Episódio 3** | ❌ Pendente ||
| **Episódio 4** | ❌ Pendente ||
| **Episódio 5** | ❌ Pendente ||

---

## 🛠️ Instalação (Para Jogadores)

1. Acesse a aba **[Releases](https://github.com/FinuraBR/traducao-jogos-e-guias/releases/tag/3-out-of-10)** e baixe o arquivo `.zip` mais recente.
2. Dentro do arquivo baixado, as traduções estarão organizadas em pastas específicas (ex: `EP1`, `EP2`, etc.).
3. Localize a pasta raiz da instalação do jogo (onde se encontra o executável `ThreeTen.exe`).
4. Extraia o conteúdo da pasta do episódio desejado para dentro dessa pasta raiz.

---

## 🤝 Workflow e Estrutura Técnica (Para Desenvolvedores)

O fluxo de trabalho foi unificado para processar todos os episódios sob uma única estrutura de scripts. Embora o processo possua diversas etapas para garantir a estabilidade dos arquivos, abaixo segue uma visão geral do método utilizado:

### 1. Processamento de Localização (`.locres`)
Arquivos de localização direta são tratados de forma independente:
- Exportação dos dados para formato **CSV** através do **UE4 Localizations Tool**.
- Utilização dos utilitários na pasta `csv_scripts` para processamento e tradução.
- Finalização e fechamento dos dados no arquivo original.

### 2. Processamento de Assets e Dados (`.uasset`)
O restante do conteúdo (DataTables, Blueprints e outros assets) segue um fluxo automatizado:
- **Extração:** Utilização do **FModel** para exportar os arquivos para a pasta de trabalho `1_RAW`.
- **Preparação:** Execução do script `0_workflow_uasset.py` para organização e filtragem de arquivos seguros.
- **Automação Integral:** O ciclo completo de divisão, tradução via IA, verificação e reconstrução é centralizado no script `6_processar_tudo.py`.

*Nota: Esta é uma visão geral. O workflow envolve camadas de filtragem para evitar a tradução de strings técnicas que poderiam causar instabilidade na Unreal Engine 4.24.3.*

### Ferramentas Utilizadas
- **UE Localizations Tool:** Manipulação de arquivos `.locres`.
- **FModel:** Extração dos assets.
- **UAssetGUI / UAssetAPI:** Manipulação de dados `.uasset`.
- **Python 3.12+:** Automação e comunicação com modelos de IA.

### 📜 Licença e Créditos
Este projeto é de código aberto. Caso utilize estes scripts ou a base de tradução aqui disponibilizada para outros projetos, solicita-se a **manutenção dos créditos ao criador original**.

**Créditos:** ツFinuraBR
