import logging
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application

from config import CHECKPOINT_INTERVALS_HOURS, AUTO_EXPIRATION_HOURS, SNOOZE_HOURS
import database as db

logger = logging.getLogger(__name__)

# Instância global do agendador
scheduler = AsyncIOScheduler()
_telegram_app: Optional[Application] = None


def init_scheduler(app: Application) -> None:
    """Inicializa o agendador e armazena referência da aplicação do Telegram."""
    global _telegram_app
    _telegram_app = app
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler inicializado com sucesso.")


def cancel_item_jobs(item_id: int) -> None:
    """Remove todos os agendamentos pendentes de um item."""
    for stage in [1, 2, 3, 4]:
        job_id = f"job_item_{item_id}_stage_{stage}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            
    expire_job_id = f"job_item_{item_id}_auto_expire"
    if scheduler.get_job(expire_job_id):
        scheduler.remove_job(expire_job_id)


def schedule_item_checkpoints(item_id: int, target_chat_id: int, base_time: Optional[datetime] = None) -> None:
    """Agenda os 4 checkpoints e o job de auto-expiração para um item."""
    if base_time is None:
        base_time = datetime.now()

    # Cancelar agendamentos anteriores por garantia
    cancel_item_jobs(item_id)

    # 1. Agendar Checkpoints 1, 2, 3 e 4
    for stage, hours in CHECKPOINT_INTERVALS_HOURS.items():
        run_date = base_time + timedelta(hours=hours)
        job_id = f"job_item_{item_id}_stage_{stage}"
        
        # Só agenda se a data for futura
        if run_date > datetime.now():
            scheduler.add_job(
                send_checkpoint_notification,
                'date',
                run_date=run_date,
                args=[item_id, target_chat_id, stage],
                id=job_id,
                replace_existing=True
            )

    # 2. Agendar Auto-Expiração (30 dias + 48 horas)
    total_hours_to_expire = CHECKPOINT_INTERVALS_HOURS[4] + AUTO_EXPIRATION_HOURS
    expire_run_date = base_time + timedelta(hours=total_hours_to_expire)
    expire_job_id = f"job_item_{item_id}_auto_expire"
    
    if expire_run_date > datetime.now():
        scheduler.add_job(
            handle_auto_expiration,
            'date',
            run_date=expire_run_date,
            args=[item_id, target_chat_id],
            id=expire_job_id,
            replace_existing=True
        )


def snooze_item_checkpoint(item_id: int, target_chat_id: int) -> datetime:
    """Reagenda o 4º checkpoint para +7 dias a partir de agora e ajusta a auto-expiração."""
    now = datetime.now()
    new_stage4_date = now + timedelta(hours=SNOOZE_HOURS)
    new_expire_date = new_stage4_date + timedelta(hours=AUTO_EXPIRATION_HOURS)

    # Remover jobs antigos de stage 4 e auto_expire
    stage4_job_id = f"job_item_{item_id}_stage_4"
    expire_job_id = f"job_item_{item_id}_auto_expire"

    if scheduler.get_job(stage4_job_id):
        scheduler.remove_job(stage4_job_id)
    if scheduler.get_job(expire_job_id):
        scheduler.remove_job(expire_job_id)

    # Adicionar novos jobs
    scheduler.add_job(
        send_checkpoint_notification,
        'date',
        run_date=new_stage4_date,
        args=[item_id, target_chat_id, 4],
        id=stage4_job_id,
        replace_existing=True
    )

    scheduler.add_job(
        handle_auto_expiration,
        'date',
        run_date=new_expire_date,
        args=[item_id, target_chat_id],
        id=expire_job_id,
        replace_existing=True
    )

    return new_stage4_date


async def send_checkpoint_notification(item_id: int, target_chat_id: int, stage: int) -> None:
    """Envio assíncrono da notificação de lembrete do checkpoint no Telegram."""
    if not _telegram_app:
        logger.error("Telegram App não inicializado no scheduler.")
        return

    item = db.get_item_by_id(item_id)
    if not item or item["status"] != "PENDING":
        return

    # Utiliza o chat_id armazenado no banco ou a chave de destino
    chat_to_send = item.get("chat_id") or target_chat_id

    # Atualiza o estágio no banco
    db.update_item_checkpoint(item_id, stage)

    title = item["title"]
    price = item["price"]

    # Mensagens adaptadas por estágio
    messages = {
        1: f"⏰ *Resfriamento 24 Horas*\nPassou um dia inteiro! O impulso inicial por *{title}* (R$ {price:.2f}) já diminuiu ou ainda faz sentido comprar?",
        2: f"⏳ *Resfriamento 7 Dias*\nFaz 1 semana que você registrou *{title}* (R$ {price:.2f}). Este item trará valor real na sua rotina?",
        3: f"🤔 *Resfriamento 15 Dias*\nPassou meio mês! Você realmente sentiu falta de *{title}* (R$ {price:.2f}) nestes últimos 15 dias?",
        4: f"🎯 *Decisão Final (30 Dias)*\nFaz 1 mês que você registrou *{title}* (R$ {price:.2f}). Se não comprou até agora, você realmente precisa dele?\n_\n⚠️ Se não responder em 48h, o item sairá da lista automaticamente!_"
    }

    text = messages.get(stage, f"⏰ Lembrete de Resfriamento para *{title}* (R$ {price:.2f}).")

    # Botões inline
    keyboard = [
        [
            InlineKeyboardButton("❌ Desisti da compra", callback_data=f"cancel_{item_id}"),
            InlineKeyboardButton("🛒 Comprei agora", callback_data=f"buy_{item_id}")
        ],
        [
            InlineKeyboardButton("✏️ Editar Preço", callback_data=f"editprice_{item_id}")
        ]
    ]

    # No 4º Checkpoint, adicionar o botão de adiar por 7 dias
    if stage == 4:
        keyboard.append([
            InlineKeyboardButton("⏰ Adiar por 7 dias", callback_data=f"snooze_{item_id}")
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await _telegram_app.bot.send_message(
            chat_id=chat_to_send,
            text=text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Erro ao enviar notificação de checkpoint para chat {chat_to_send}: {e}")


async def handle_auto_expiration(item_id: int, target_chat_id: int) -> None:
    """Trata a expiração automática de um item não respondido após 48h do último checkpoint."""
    if not _telegram_app:
        return

    item = db.get_item_by_id(item_id)
    if not item or item["status"] != "PENDING":
        return

    chat_to_send = item.get("chat_id") or target_chat_id

    # Atualiza para EXPIRED no banco
    db.update_item_status(item_id, "EXPIRED")

    title = item["title"]
    price = item["price"]

    text = (
        f"⌛ *Item Expirado Automático*\n"
        f"O item *{title}* (R$ {price:.2f}) não recebeu resposta após o período limite.\n\n"
        f"🎉 Ele foi removido da sua lista de desejos e contabilizado na sua *economia acumulada*! 💰"
    )

    try:
        await _telegram_app.bot.send_message(
            chat_id=chat_to_send,
            text=text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Erro ao enviar notificação de expiração para chat {chat_to_send}: {e}")


def restore_pending_jobs() -> None:
    """Restaura agendamentos de itens pendentes no banco após reinicialização do bot."""
    pending_items = db.get_all_pending_items()
    logger.info(f"Restaurando agendamentos para {len(pending_items)} itens pendentes.")
    
    for item in pending_items:
        try:
            created_at = datetime.strptime(item["created_at"], "%Y-%m-%d %H:%M:%S")
        except Exception:
            created_at = datetime.now()

        chat_id = item.get("chat_id") or item["user_id"]
        schedule_item_checkpoints(item["id"], chat_id, created_at)
