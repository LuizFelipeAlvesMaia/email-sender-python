# Use uma imagem base do Python
FROM python:3.12-slim

# Defina o diretório de trabalho dentro do container
WORKDIR /app

# Copie os arquivos requirements.txt e o script Python para o diretório de trabalho
COPY requirements.txt requirements.txt
COPY . .

# Instale as dependências do sistema necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    build-essential \
    cron

# Instale as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando para inicializar o cron
CMD ["cron", "-f"]