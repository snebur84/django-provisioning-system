# ==============================================================================
# 1. 🏗️ FASE DE BUILD (Instalação de Dependências)
# ==============================================================================
FROM python:3.11-slim AS builder

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# 2. 🚀 FASE FINAL (Runtime de Produção)
# ==============================================================================
FROM python:3.11-slim

# Define o diretório de trabalho
WORKDIR /usr/src/app

# COPIA OS PACOTES: Garante que os pacotes estejam no PATH padrão do Python
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# COPIA O CÓDIGO DA APLICAÇÃO (Rodando como ROOT)
COPY . .

# ⚙️ Comandos de Preparação do Django - RODANDO COMO ROOT
# A variável STATICFILES_STORAGE impede o GCS, e o RUN como root evita permissões.
# Se o erro "storages" persistir aqui, o pacote não foi instalado corretamente.
RUN STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage" \ 
    python manage.py collectstatic --noinput

# 🔑 Configuração de Segurança (SÓ AQUI MUDAMOS PARA O USUÁRIO SEM PRIVILÉGIO)
# Cria o usuário para o runtime (sem privilégios)
RUN adduser --system --group django

# APLICA PERMISSÃO AO USUÁRIO DJANGO PARA ACESSO AOS ARQUIVOS
# Dá ao usuário 'django' permissão para ler o código e os estáticos.
RUN chown -R django:django /usr/src/app

# Define o usuário que será usado no runtime
USER django

# Cria o diretório de mídia (necessário mesmo que use GCS, para uploads temporários)
# Este comando deve ser executado pelo usuário 'django' (ou ter permissão)
RUN mkdir -p media

# 🌐 Configuração do Cloud Run
ENV PORT=8080 
EXPOSE 8080

# 🏃 Comando de Inicialização (Entrypoint)
CMD ["gunicorn", "provision.wsgi:application", "--bind", "0.0.0.0:${PORT}", "--workers", "4", "--timeout", "180"]