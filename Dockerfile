FROM python:3.11-slim

# Evita geração de arquivos .pyc e força unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar pacotes de sistema necessários (ex: fontes para Matplotlib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código-fonte
COPY . /app/

# Criar o diretório de dados para o SQLite
RUN mkdir -p /app/data

CMD ["python", "bot.py"]
