# ==============================================================================
# 1. FASE DE BUILD (Instalação de Dependências)
# ==============================================================================
FROM python:3.11-slim AS builder

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# 2. FASE FINAL (Runtime de Produção) - CORRIGIDO
# ==============================================================================
FROM python:3.11-slim

WORKDIR /usr/src/app

# COPIA OS PACOTES DEPOIS DE DEFINIR WORKDIR
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# COPIA O CÓDIGO
COPY . .

RUN STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage" \ 
    python manage.py collectstatic --noinput

RUN adduser --system --group django
USER django

RUN chown -R django:django /usr/src/app

RUN mkdir -p media

# Configuração do Cloud Run
ENV PORT=8080 
EXPOSE 8080

# Comando de Inicialização (Entrypoint)
CMD ["gunicorn", "provision.wsgi:application", "--bind", "0.0.0.0:${PORT}", "--workers", "2", "--timeout", "90"]