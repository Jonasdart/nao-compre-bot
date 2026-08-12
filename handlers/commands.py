import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
import reports

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /start."""
    user = update.effective_user
    if not user:
        return

    db.upsert_user(user.id, user.first_name)

    text = (
        f"Olá, *{user.first_name}*! 👋 Bem-vindo ao *Não Compre - Bot*!\n\n"
        f"Meu objetivo é te ajudar a **evitar compras impulsivas** criando um *atrito positivo* na sua jornada de consumo.\n\n"
        f"💡 *Como funciona?*\n"
        f"Sempre que quiser comprar algo, me envie o nome do item e o valor (ex: `Fone Bluetooth 250.00` ou um link do produto).\n\n"
        f"Eu coloco o produto em uma **Fila de Resfriamento** com 4 lembretes de reflexão:\n"
        f"• ⏱️ **24 Horas**\n"
        f"• ⏳ **7 Dias**\n"
        f"• 🤔 **15 Dias**\n"
        f"• 🎯 **30 Dias** (Checkpoint Final com opção de adiar por +7 dias)\n\n"
        f"📋 *Comandos Úteis:*\n"
        f"/minhalista - Ver itens em resfriamento\n"
        f"/relatorio - Ver relatório visual de economia\n"
        f"/help - Ajuda e instruções detalhadas"
    )

    await update.message.reply_text(text, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /help."""
    text = (
        "📖 *Manual de Uso do Não Compre - Bot*\n\n"
        "1️⃣ *Cadastrar um Produto:*\n"
        "Envie uma mensagem simples com o nome e o valor. Exemplos:\n"
        "• `Camiseta Nike R$ 120,00`\n"
        "• `Fone Bluetooth 250.00`\n"
        "• Colar o link do produto direto da loja!\n\n"
        "2️⃣ *Gerenciar a Lista de Desejos:*\n"
        "Use `/minhalista` para listar todos os itens pendentes. Você pode marcar como *Desisti da compra* ❌ ou *Comprei agora* 🛒 a qualquer momento.\n\n"
        "3️⃣ *Acompanhar a Economia:*\n"
        "Use `/relatorio` para gerar um gráfico interativo em Dark Mode com sua economia acumulada e taxa de sucesso!\n\n"
        "4️⃣ *Auto-Expiração:*\n"
        "Itens sem resposta após 48 horas do último checkpoint (30 dias) são expirados e contabilizados como economia automaticamente."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def minhalista_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /minhalista."""
    user = update.effective_user
    if not user:
        return

    items = db.get_active_items_by_user(user.id)

    if not items:
        await update.message.reply_text(
            "🎉 *Sua lista de desejos ativos está vazia!*\nVocê não possui compras em período de resfriamento no momento.",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(f"📋 *Sua Lista de Desejos ({len(items)} itens em resfriamento):*", parse_mode="Markdown")

    stage_names = {
        0: "0h (Recém-criado)",
        1: "24 Horas",
        2: "7 Dias",
        3: "15 Dias",
        4: "30 Dias (Final)"
    }

    for item in items:
        stage_desc = stage_names.get(item["checkpoint_stage"], "Em andamento")
        text = (
            f"📦 *{item['title']}*\n"
            f"💰 *Preço:* R$ {item['price']:.2f}\n"
            f"🏷️ *Categoria:* {item['category']}\n"
            f"⏳ *Estágio Atual:* {stage_desc}\n"
            f"📅 *Registrado em:* {item['created_at'][:10]}"
        )
        if item.get("url"):
            text += f"\n🔗 [Link do Produto]({item['url']})"

        keyboard = [
            [
                InlineKeyboardButton("❌ Desisti da compra", callback_data=f"cancel_{item['id']}"),
                InlineKeyboardButton("🛒 Comprei agora", callback_data=f"buy_{item['id']}")
            ],
            [
                InlineKeyboardButton("✏️ Editar Preço", callback_data=f"editprice_{item['id']}")
            ]
        ]
        
        if item["checkpoint_stage"] == 4:
            keyboard.append([
                InlineKeyboardButton("⏰ Adiar por 7 dias", callback_data=f"snooze_{item['id']}")
            ])

        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def relatorio_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /relatorio."""
    user = update.effective_user
    if not user:
        return

    await update.message.reply_chat_action("upload_photo")

    try:
        buf, text = reports.generate_monthly_report(user.id)
        await update.message.reply_photo(
            photo=buf,
            caption=text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Erro ao gerar relatório para o usuário {user.id}: {e}")
        await update.message.reply_text("❌ Ocorreu um erro ao gerar seu relatório visual. Tente novamente.")


import urllib.parse

async def share_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /compartilhar."""
    bot_info = await context.bot.get_me()
    bot_username = bot_info.username

    text = (
        f"📢 *Compartilhar o Não Compre - Bot*\n\n"
        f"Ajude amigos e grupos a evitarem compras impulsivas.\n\n"
        f"*Como funciona:*\n"
        f"• Cadastre o produto ou link\n"
        f"• Receba lembretes de resfriamento (24h, 7d, 15d e 30d)\n"
        f"• Decida com calma e acompanhe sua economia em relatórios\n\n"
        f"🔗 *Link direto:* https://t.me/{bot_username}\n"
        f"👥 *Adicionar a grupo:* https://t.me/{bot_username}?startgroup=true"
    )

    # Mensagem pragmática enviada para quem RECEBE o compartilhamento
    share_msg = (
        "Não Compre - Bot de Consumo Consciente\n\n"
        "Bot para evitar compras por impulso. Você envia o produto ou link e ele agenda lembretes em 24h, 7 dias, 15 dias e 30 dias para você decidir se realmente precisa do item.\n\n"
        "Inclui relatórios gráficos da sua economia acumulada.\n\n"
        "Acesse no Telegram:"
    )

    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}&text={urllib.parse.quote(share_msg)}"

    keyboard = [
        [
            InlineKeyboardButton("👥 Adicionar ao Grupo", url=f"https://t.me/{bot_username}?startgroup=true"),
            InlineKeyboardButton("📲 Compartilhar", url=share_url)
        ]
    ]

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
