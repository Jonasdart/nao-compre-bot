# 🧠 AntiImpulseBot — Bot Telegram Antimpulso de Compras

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-v20%2B-26A5E4.svg?logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

O **AntiImpulseBot** é uma aplicação interativa para o Telegram projetada para combater compras impulsivas através do conceito de **"Atrito Positivo"**. Ao desacelerar o ciclo de gratificação imediata do *checkout*, o bot intercepta a intenção de compra e ajuda o usuário a reavaliar a real necessidade dos itens em quatro intervalos estratégicos de tempo (**24h, 7d, 15d e 30d**).

Além do diferimento da compra, o bot monitora a taxa de descarte, calcula a economia acumulada e gera **relatórios visuais em modo escuro (Dark Mode)** com gráficos consolidados.

---

## ✨ Funcionalidades Principais

* ⚡ **Cadastro Instantâneo & Parsing Inteligente:**
  * Suporta mensagens em texto livre no formato `Nome do Produto 250.00` ou `Camiseta Nike R$ 120,00`.
  * Suporta o envio direto de links (URLs) de e-commerce (*Amazon, Mercado Livre, Shopee, Magalu, AliExpress*), com extração automática de título, preço e link público.
* 🏷️ **Categorização Automática (*Smart Matching*):**
  * Classificação automática entre: *Eletrônicos*, *Vestuário*, *Games & Software*, *Casa & Cozinha*, *Cosméticos & Beleza* e *Geral*.
* ✏️ **Edição Flexível de Preço:**
  * Botão inline instantâneo (`✏️ Editar Preço`) em todas as interações para definir ou ajustar o valor numérico em reais caso o site não o forneça publicamente.
* ⏳ **Régua de Resfriamento (*Cooldown Intervals*):**
  * **Checkpoint 0 (Imediato):** Registro inicial com botões inline (`Desisti da compra` / `Comprei agora`).
  * **Checkpoint 1 (24 Horas):** Notificação push após o impulso inicial passar.
  * **Checkpoint 2 (7 Dias):** Pergunta de reflexão sobre a utilidade no curto/médio prazo.
  * **Checkpoint 3 (15 Dias):** Pergunta de reflexão sobre a real falta que o item fez.
  * **Checkpoint 4 (30 Dias):** Decisão final com opção de **"⏰ Adiar por 7 dias"** para postergar a compra por mais uma semana.
* ⌛ **Auto-Expiração Inteligente:**
  * Se o último checkpoint (30 dias) não for respondido em até **2 dias (48 horas)**, o item sai automaticamente da lista e é contabilizado na **economia acumulada**.
* 📊 **Relatórios Visuais em Dark Mode (`/relatorio`):**
  * **Gráfico de Rosca (Donut Chart):** Distribuição da economia acumulada por categoria.
  * **Gráfico de Barras:** Comparativo entre compras evitadas, compras efetuadas e itens em resfriamento.
  * **KPIs em Texto:** Valor total salvo em reais (`R$ X.XXX,XX`) e taxa de sucesso no controle de impulso.
* 🐳 **Containerização Completa:**
  * Pronto para rodar via **Docker e Docker Compose** com banco de dados SQLite persistente em volume isolado.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.11+
* **Telegram Framework:** `python-telegram-bot` v20+ (Long Polling & Async/Await)
* **Agendador de Tarefas:** `APScheduler` (AsyncIOScheduler)
* **Banco de Dados:** SQLite3 (WAL Mode ativado para alta performance)
* **Visualização de Dados:** `Matplotlib` (Renderização de gráficos Dark Mode em buffer de memória `io.BytesIO`)
* **Requisições HTTP:** `httpx` (Parsing de metatags OpenGraph/JSON-LD em URLs)

---

## 🤖 Comandos do Bot

| Comando | Descrição |
| :--- | :--- |
| `/start` | Inicia o bot e exibe as instruções de boas-vindas. |
| `/help` | Exibe o manual detalhado de uso e formatos suportados. |
| `/minhalista` | Lista todas as compras ativas em resfriamento com botões de ação inline. |
| `/relatorio` | Gera e envia o relatório gráfico com estatísticas de economia. |

---

## 🚀 Como Executar o Projeto

### Pré-requisitos

1. Obter um `TELEGRAM_BOT_TOKEN` com o [@BotFather](https://t.me/BotFather) no Telegram.
2. [Docker](https://www.docker.com/) e [Docker Compose](https://docs.docker.com/compose/) instalados.

---

### Passo 1: Clonar o Repositório

```bash
git clone https://github.com/seu-usuario/antiimpulse-bot.git
cd antiimpulse-bot
```

### Passo 2: Configurar o Arquivo `.env`

Crie o arquivo `.env` a partir do exemplo fornecido:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com o seu token:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
DATABASE_PATH=data/bot.db
```

### Passo 3: Subir o Container com Docker Compose

```bash
docker compose up -d --build
```

Verifique se o bot está rodando e acompanhe os logs em tempo real:

```bash
docker compose logs -f antiimpulse_bot
```

---

## 📂 Estrutura do Projeto

```
.
├── .env.example              # Modelo de variáveis de ambiente
├── .gitignore                # Arquivos ignorados pelo Git
├── Dockerfile                # Imagem Docker otimizada em Python 3.11-slim
├── docker-compose.yml        # Orquestração do container e volumes
├── requirements.txt          # Dependências Python
├── config.py                 # Configurações globais e prazos dos checkpoints
├── database.py               # Operações CRUD e schema SQLite
├── parser.py                 # Módulo de parsing de texto, preços e URLs
├── scheduler.py              # Agendador de notificações e expiração
├── reports.py                # Geração de gráficos visuais Matplotlib (Dark Mode)
├── bot.py                    # Ponto de entrada da aplicação Telegram
└── handlers/
    ├── __init__.py
    ├── commands.py           # Handlers dos comandos (/start, /help, /minhalista, /relatorio)
    ├── messages.py           # Interceptação de produtos e edição de preço
    └── callbacks.py          # Ações dos botões inline (Desisti, Comprei, Adiar, Editar Preço)
```

---

## 📄 Licença

Este projeto está licenciado sob a licença [MIT](LICENSE) — consulte o arquivo para mais detalhes.
