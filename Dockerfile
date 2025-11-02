# Dockerfile

# ==============================================================================
# 1. FASE DE BUILD (Instalação de Dependências)
# ==============================================================================
FROM python:3.11-slim as builder

WORKDIR /usr/src/app

# Copia e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# 2. FASE FINAL (Runtime de Produção)
# ==============================================================================
FROM python:3.11-slim

WORKDIR /usr/src/app

# Configuração de Segurança (Boa Prática)
# Cria um usuário não-root por segurança
RUN adduser --system --group django
USER django

# Copia os pacotes Python instalados da fase de build para a imagem final
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# COPIAR CÓDIGO FONTE AGORA (Garante que settings.py esteja presente)
# Copia o código da aplicação (com permissões para o usuário django)
COPY --chown=django:django . .

# Comandos de Preparação do Django
# Este comando usará o Google Cloud Storage (GCS) como backend
# se o seu settings.py estiver configurado para detectar o GCS no build.
RUN python manage.py collectstatic --noinput

# Cria o diretório de mídia (necessário mesmo que use GCS, para uploads temporários)
# Embora o usuário seja 'django', o diretório já existe; isso é mais um ajuste.
RUN mkdir -p media

# Configuração do Cloud Run
ENV PORT 8080 
EXPOSE 8080

# Comando de Inicialização (Entrypoint)
# Inicia o Gunicorn, apontando para o módulo WSGI correto.
CMD exec gunicorn provision.wsgi:application --bind 0.0.0.0:${PORT} --workers 2 --timeout 90