import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega arquivo .env se existir
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Configurações do Telegram e Banco de Dados
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "data", "bot.db"))

# Garantir que o diretório de dados exista
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# Categorias Padrão
CATEGORIES = [
    "Eletrônicos",
    "Vestuário",
    "Games & Software",
    "Casa & Cozinha",
    "Cosméticos & Beleza",
    "Geral"
]

# Definição dos Checkpoints de Resfriamento (em horas a partir da criação)
CHECKPOINT_INTERVALS_HOURS = {
    1: 24,       # Checkpoint 1: 24 Horas
    2: 168,      # Checkpoint 2: 7 Dias (7 * 24 = 168h)
    3: 360,      # Checkpoint 3: 15 Dias (15 * 24 = 360h)
    4: 720       # Checkpoint 4: 30 Dias (30 * 24 = 720h) - Checkpoint Final
}

# Tolerância para Auto-Expiração após a notificação do último checkpoint (em horas)
AUTO_EXPIRATION_HOURS = 48  # 2 Dias após o 4º checkpoint

# Adiantamento por Snooze (em horas)
SNOOZE_HOURS = 168  # +7 Dias
