# Use uma imagem base Python com suporte Debian (Slim é comum)
FROM python:3.11-slim

# 1. Instalar dependências de sistema (Reduzido, pois PyMySQL é puro Python)
# Removemos default-libmysqlclient-dev. Mantemos build-essential/gcc para quaisquer outras
# bibliotecas que possam ser dependências do seu requirements.txt.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    gcc \
    # Limpar o cache do apt para reduzir o tamanho da imagem
    && rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho
WORKDIR /usr/src/app

# Copiar requirements.txt e instalar dependências Python
# Instalar PyMySQL aqui, se já não estiver no requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante da aplicação
COPY . .

# Variável de Ambiente para a porta do Cloud Run
ENV PORT 8080

# =========================================================================
# COMANDO DE INÍCIO DE PRODUÇÃO (CRÍTICO: Gunicorn com Timeout de 5m)
# =========================================================================
# O timeout de 300s é crucial para o Cloud SQL Proxy inicializar.
# Usamos o módulo wsgi para iniciar o Gunicorn.
CMD gunicorn provision.wsgi:application --bind 0.0.0.0:${PORT} --workers 4 --timeout 300