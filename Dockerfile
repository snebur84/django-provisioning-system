# Dockerfile

# ==============================================================================
# 1. FASE DE BUILD (Instalação de Dependências)
# ==============================================================================
# FromAsCasing: Corrigido para 'AS' em maiúsculo
FROM python:3.11-slim AS builder

WORKDIR /usr/src/app

# Copia e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# 2. FASE FINAL (Runtime de Produção)
# ==============================================================================
FROM python:3.11-slim

WORKDIR /usr/src/app

RUN adduser --system --group django
USER django

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

COPY --chown=django:django . .

# Comandos de Preparação do Django
RUN STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage" \ 
    python manage.py collectstatic --noinput

RUN mkdir -p media

# Configuração do Cloud Run
ENV PORT=8080 
EXPOSE 8080

# Comando de Inicialização (Entrypoint)
CMD ["gunicorn", "provision.wsgi:application", "--bind", "0.0.0.0:${PORT}", "--workers", "2", "--timeout", "90"]