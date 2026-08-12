import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
from parser import parse_product_message
import scheduler

logger = logging.getLogger(__name__)


async def handle_product_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa mensagens enviadas pelo usuário contendo informações de produtos/links ou edições de preço."""
    user = update.effective_user
    message_text = update.message.text

    if not user or not message_text:
        return

    # Garante o cadastro do usuário
    db.upsert_user(user.id, user.first_name)

    # Verifica se o usuário está no modo de edição de preço de um item
    editing_item_id = context.user_data.get("editing_item_id")
    if editing_item_id:
        item = db.get_item_by_id(editing_item_id)
        if item:
            from parser import extract_price
            new_price, _ = extract_price(message_text)
            if new_price and new_price > 0:
                db.update_item_price(editing_item_id, new_price)
                context.user_data.pop("editing_item_id", None)
                await update.message.reply_text(
                    f"✅ *Preço Atualizado com Sucesso!*\n\n"
                    f"📦 *Item:* {item['title']}\n"
                    f"💰 *Novo Valor:* R$ {new_price:.2f}",
                    parse_mode="Markdown"
                )
                return
            else:
                await update.message.reply_text(
                    "❌ Não consegui identificar o novo valor. Por favor, envie um valor em reais (ex: `4090.00` ou `R$ 4.090,00`)."
                )
                return
        else:
            context.user_data.pop("editing_item_id", None)

    # Parsing da mensagem para novo produto
    parsed = await parse_product_message(message_text)
    title = parsed["title"]
    price = parsed["price"]
    url = parsed["url"]
    category = parsed["category"]

    # Criação do item no banco
    item_id = db.create_item(
        user_id=user.id,
        title=title,
        price=price,
        url=url,
        category=category
    )

    # Agendamento dos checkpoints de resfriamento e auto-expiração
    scheduler.schedule_item_checkpoints(item_id=item_id, user_id=user.id)

    # Mensagem de confirmação imediata (Checkpoint 0)
    text = (
        f"✅ *Item Adicionado à Fila de Resfriamento!*\n\n"
        f"📦 *Produto:* {title}\n"
        f"💰 *Preço:* R$ {price:.2f}\n"
        f"🏷️ *Categoria:* {category}\n"
    )
    if url:
        text += f"🔗 [Link do Produto]({url})\n"

    if price == 0.0:
        text += "\n⚠️ _Dica: O preço não foi detectado automaticamente. Clique em '✏️ Editar Preço' abaixo para definir o valor!_\n"

    text += (
        f"\n⏳ *O ciclo de impulso foi interrompido!*\n"
        f"Seu primeiro lembrete de resfriamento chegará em **24 Horas**.\n\n"
        f"Se quiser decidir agora:"
    )

    keyboard = [
        [
            InlineKeyboardButton("❌ Desisti da compra", callback_data=f"cancel_{item_id}"),
            InlineKeyboardButton("🛒 Comprei agora", callback_data=f"buy_{item_id}")
        ],
        [
            InlineKeyboardButton("✏️ Editar Preço", callback_data=f"editprice_{item_id}")
        ]
    ]

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
