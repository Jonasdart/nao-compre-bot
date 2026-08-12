import logging
from telegram import Update
from telegram.ext import ContextTypes

import database as db
import scheduler

logger = logging.getLogger(__name__)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gerencia as ações disparadas pelos botões inline do bot."""
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()

    data = query.data
    user = update.effective_user

    if not user:
        return

    # Parser do callback data (ex: cancel_12, buy_12, snooze_12)
    try:
        action, item_id_str = data.split("_", 1)
        item_id = int(item_id_str)
    except ValueError:
        logger.error(f"Formato de callback inválido: {data}")
        return

    item = db.get_item_by_id(item_id)
    if not item:
        await query.edit_message_text("❌ Este item não existe mais ou já foi removido.")
        return

    title = item["title"]
    price = item["price"]

    if action == "cancel":
        # Marca como cancelado (economia acumulada)
        db.update_item_status(item_id, "CANCELLED")
        scheduler.cancel_item_jobs(item_id)
        
        text = (
            f"🎉 *Parabéns pela excelente decisão!*\n\n"
            f"Você desistiu da compra de *{title}* (R$ {price:.2f}).\n"
            f"💰 *R$ {price:.2f}* foram adicionados à sua **economia acumulada** no relatório mensal!"
        )
        await query.edit_message_text(text, parse_mode="Markdown")

    elif action == "buy":
        # Marca como comprado
        db.update_item_status(item_id, "PURCHASED")
        scheduler.cancel_item_jobs(item_id)

        text = (
            f"🛒 *Item Comprado*\n\n"
            f"O item *{title}* (R$ {price:.2f}) foi marcado como comprado.\n"
            f"Esperamos que seja uma escolha consciente e traga excelente utilidade!"
        )
        await query.edit_message_text(text, parse_mode="Markdown")

    elif action == "snooze":
        # Adiar por 7 dias
        target_chat_id = item.get("chat_id") or update.effective_chat.id
        new_date = scheduler.snooze_item_checkpoint(item_id, target_chat_id)
        date_str = new_date.strftime("%d/%m/%Y às %H:%M")

        text = (
            f"⏰ *Lembrete Adiado!*\n\n"
            f"O checkpoint final para *{title}* (R$ {price:.2f}) foi prorrogado por mais **7 Dias**.\n"
            f"📅 Novo lembrete agendado para: *{date_str}*."
        )
        await query.edit_message_text(text, parse_mode="Markdown")

    elif action == "editprice":
        # Ativa o modo de edição de preço para o próximo texto do usuário
        context.user_data["editing_item_id"] = item_id
        text = (
            f"✏️ *Editar Preço do Produto*\n\n"
            f"📦 *Item:* {title}\n"
            f"💰 *Preço Atual:* R$ {price:.2f}\n\n"
            f"Por favor, envie uma mensagem com o novo valor em reais.\n"
            f"*(Exemplo: `4090.00` ou `R$ 4.090,00`)*"
        )
        await query.message.reply_text(text, parse_mode="Markdown")
