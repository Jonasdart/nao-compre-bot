import logging
import sys
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import TELEGRAM_BOT_TOKEN
import database as db
import scheduler
from handlers.commands import (
    start_command,
    help_command,
    minhalista_command,
    relatorio_command,
    share_command,
)
from handlers.messages import handle_product_message
from handlers.callbacks import handle_callback_query

# Configuração de Logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(application) -> None:
    """Callback assíncrono executado imediatamente após o boot da aplicação do Telegram."""
    db.init_db()
    scheduler.init_scheduler(application)
    scheduler.restore_pending_jobs()
    logger.info("✨ Não Compre - Bot inicializado com sucesso e escutando requisições!")


def main() -> None:
    """Ponto de entrada principal para inicializar e rodar o bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ ERRO CRÍTICO: A variável de ambiente TELEGRAM_BOT_TOKEN não foi encontrada no .env!")
        logger.error("Por favor, crie um arquivo .env baseado no .env.example e adicione seu token.")
        sys.exit(1)

    # Construção da Aplicação do Telegram
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Registrar Comandos
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("minhalista", minhalista_command))
    app.add_handler(CommandHandler("relatorio", relatorio_command))
    app.add_handler(CommandHandler(["compartilhar", "share"], share_command))

    # Registrar Handlers de Interatividade
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_message))

    # Iniciar Long Polling
    logger.info("Conectando ao Telegram (Long Polling)...")
    app.run_polling()


if __name__ == "__main__":
    main()
