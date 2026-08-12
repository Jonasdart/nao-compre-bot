# Product Requirement Document (PRD)
## Bot Telegram Antimpulso de Compras (`AntiImpulseBot`)

---

### 1. Visão Geral do Produto
O **Bot Antimpulso de Compras** é uma ferramenta interativa desenvolvida para o Telegram, cujo propósito central é criar um **"atrito positivo"** na jornada de consumo online do usuário. Ao desacelerar o ciclo de gratificação imediata (pico de dopamina do checkout), a aplicação intercepta a intenção de compra e obriga o usuário a reavaliar a real necessidade do item em quatro intervalos estratégicos de tempo (*cooldown*: 1h, 12h, 7d e 15d).

Além do diferimento da compra, o bot rastreia os itens desistidos, calcula a economia acumulada e gera **relatórios visuais mensais** (gráficos consolidadores) categorizando os ganhos financeiros decorrentes do controle de impulso.

---

### 2. Objetivos e Métricas de Sucesso (KPIs)
* **Redução de Compras Impulsivas:** Atingir uma taxa de descarte (*cancellation rate*) de pelo menos 60% dos itens cadastrados na fila de resfriamento.
* **Friction-less Data Entry:** Permitir que o cadastro de um produto leve menos de 5 segundos via mensagens de texto simples ou compartilhamento de links.
* **Engajamento com Lembretes:** Garantir 100% de precisão nos agendamentos de notificação sem falhas de execução no servidor.
* **Visibilidade Financeira:** Entregar relatórios gráficos mensais que evidenciem o valor economizado acumulado em reais (R$).

---

### 3. Público-Alvo e Personas
* **Usuários com perfil de consumo digital frequente:** Pessoas que navegam constantemente em e-commerces, e-mail marketing, redes sociais e marketplaces (Amazon, Mercado Livre, Shopee, AliExpress).
* **Consumidores em busca de gestão de finanças pessoais:** Indivíduos que desejam otimizar seu orçamento e economizar dinheiro eliminando pequenos gastos supérfluos do cotidiano.

---

### 4. Escopo das Funcionalidades

#### 4.1. Entrada de Dados e Captura de Itens
* **Parsing de Texto Livre:** Suporte a mensagens no formato `Nome do Produto - Valor` (ex: `Fone Bluetooth 250.00` ou `Camiseta Nike R$ 120,00`).
* **Parsing de Links (URLs):** Extração de URLs contidas na mensagem e identificação de títulos/preços preliminares.
* **Categorização Automática (*Smart Matching*):** Heurística baseada em regex e dicionário de palavras-chave para atribuir automaticamente uma das categorias padrão:
  * Eletrônicos
  * Vestuário
  * Games & Software
  * Casa & Cozinha
  * Cosméticos & Beleza
  * Geral (Default)

#### 4.2. Régua de Resfriamento (*Cooldown Intervals*)
* **Checkpoint 0 (Imediato):** Confirmação de cadastro do item e botões inline ("❌ Desisti da compra", "🛒 Comprei agora").
* **Checkpoint 1 (1 Hora):** Lembrete rápido enviando notificação push no Telegram para quebrar o impulso inicial.
* **Checkpoint 2 (12 Horas):** Lembrete ao mudar de turno (manhã/noite).
* **Checkpoint 3 (7 Dias):** Pergunta de reflexão sobre a utilidade no médio prazo.
* **Checkpoint 4 (15 Dias):** Decisão final. Se o item não for comprado até aqui, o usuário é encorajado a marcar como cancelado, consolidando a economia.

#### 4.3. Módulo de Relatórios Mensais e Visuais
* **Comando `/relatorio`:** Gera sob demanda (ou no 1º dia de cada mês) um relatório estatístico e gráfico.
* **Renderização de Dashboard em Imagem (PNG):**
  * **Gráfico de Rosca (Donut Chart):** Distribuição percentual do valor economizado por categoria.
  * **Gráfico de Barras:** Comparativo entre número de itens cancelados (economizados), comprados e ainda em resfriamento.
* **KPIs no Texto:** Exibição do valor total salvo em reais (`R$ X.XXX,XX`).

---

### 5. Arquitetura Técnica e Tecnologias

* **Linguagem:** Python 3.10+
* **Framework Telegram:** `python-telegram-bot` v20+ (API oficial de Bot API via Long Polling ou Webhook; sem uso de Userbot/Telethon).
* **Banco de Dados:** SQLite3 (Banco relacional leve e sem dependências externas de serviço).
* **Agendador de Tarefas:** `APScheduler` (AsyncIOScheduler) para gerenciamento persistente dos lembretes nos intervalos de tempo.
* **Visualização de Dados:** `Matplotlib` para renderização de gráficos estáticos em modo escuro (*Dark Mode*) exportados diretamente em PNG.

---

### 6. Modelagem de Dados (SQLite Schema)

```sql
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wishlist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    price REAL NOT NULL,
    url TEXT,
    category TEXT DEFAULT 'Geral',
    status TEXT DEFAULT 'PENDING', -- PENDING, PURCHASED, CANCELLED
    checkpoint_stage INTEGER DEFAULT 0, -- 0 (0h), 1 (1h), 2 (12h), 3 (7d), 4 (15d)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);
```

---

### 7. Requisitos Não-Funcionais
* **Privacidade:** O bot coleta apenas dados estritamente necessários (ID do Telegram, nome do produto e valor fornecido). Nenhuma credencial bancária ou de e-commerce é solicitada.
* **Desempenho:** O processamento de mensagens e resposta inicial deve ser concluído em < 1.5 segundo.
* **Disponibilidade:** O script Python deve rodar em um processo contínuo (ex: daemon systemd ou container Docker).

---

### 8. Próximos Passos e Roadmap Futuro (Post-MVP)
* Integrar web scraping avançado via Playwright/Selenium para extração automática de título, preço e imagem direto de links do Mercado Livre e Amazon.
* Adicionar comando para ajuste manual da lista de palavras-chave/categorias por usuário.
* Exportação de dados em relatórios CSV e XLSX para controle financeiro pessoal avançado.
