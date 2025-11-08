# 🚀 Provisionamento CRCTTEC

Este repositório contém o código-fonte da aplicação de Provisionamento, um projeto desenvolvido em **Django** focado na gestão de **Dispositivos, Perfis e Templates**. A aplicação utiliza o Google Cloud Platform (GCP) para hospedagem (Cloud Run, Cloud SQL) e serviços de autenticação robustos via `django-allauth` com login social Google.

## ✨ Funcionalidades Principais

* **Gestão de Entidades:** CRUD completo para Dispositivos, Perfis e Templates (via app `core`).
* **Autenticação Robusta:** Implementação completa de login/registro usando `django-allauth`.
* **Login Social:** Integração finalizada com **Google OAuth2** para acesso rápido.
* **Estilização Moderna:** Formulários customizados e estilizados com **Bootstrap 5** via `django-crispy-forms`.
* **API RESTful:** API implementada usando Django REST Framework, documentada com **Drf-Spectacular** (OpenAPI/Swagger).
* **Ambiente de Produção:** Configuração otimizada para **Google Cloud Run** e **Cloud SQL (MySQL)**.

---

## ☁️ Deploy e CI/CD (GitHub Actions + GCP)

O processo de *deploy* em produção utiliza **GitHub Actions** para automação do CI/CD, visando o **Google Cloud Run** como ambiente *serverless*. O fluxo é disparado automaticamente em *push* para o *branch* principal (`main`/`master`).

### 1. Pré-requisitos no Google Cloud Platform (GCP)

Para que o *workflow* funcione, os seguintes recursos devem estar provisionados e as respectivas APIs habilitadas no GCP:

| Serviço GCP | Configuração Necessária | Informação a Obter |
| :--- | :--- | :--- |
| **Cloud Run & Artifact Registry** | Criar um repositório Docker (ex: `provision-app`). | N/A (Configurado pelo Workflow) |
| **Cloud SQL (MySQL)** | Instância e Banco de Dados criados. | `CLOUD_SQL_CONNECTION_NAME` |
| **Cloud Storage (GCS)** | Criar um *bucket* para Estáticos/Mídia. | `GS_BUCKET_NAME` |

### 2. Secrets e Variáveis de Ambiente (GitHub Actions)

O *workflow* depende de Secrets configurados no repositório (**Settings > Secrets and variables > Actions**) para autenticação e injeção de variáveis de ambiente no Cloud Run.

| Nome do GitHub Secret | Finalidade |
| :--- | :--- |
| **`GCP_SA_KEY`** | **Chave JSON da Service Account** com permissões de `Cloud Run Developer` e `Storage Admin`. Essencial para autenticação. |
| **`GCP_PROJECT_ID`** | ID do projeto GCP de destino. |
| **`REGION`** | Região do Cloud Run (Ex: `southamerica-east1`). |
| **`SECRET_KEY`** | Chave secreta de produção (Para o `settings.py`). |
| **`CLOUD_SQL_CONNECTION_NAME`** | String de conexão do Cloud SQL (Ex: `project:region:instance`). |
| **`DB_PASSWORD`** | Senha do usuário MySQL do Cloud SQL. |
| **`GS_BUCKET_NAME`** | Nome do *bucket* GCS para `collectstatic`. |
| **`DJANGO_ALLOWED_HOSTS`** | Domínios de produção permitidos (Ex: `*.crcttec.com.br, *.run.app`). |
| **`EMAIL_HOST_USER`**, etc. | Credenciais de **SMTP** para o envio de e-mails do Allauth. |

### 3. Resumo do Workflow (`deploy-cloud-run.yml`)

O arquivo `.github/workflows/deploy-cloud-run.yml` executa as seguintes etapas:

1.  **`Auth GCP`:** Autentica o fluxo usando o Secret `GCP_SA_KEY`.
2.  **`Build & Push`:** Constrói a imagem Docker da aplicação e envia para o **Artifact Registry**.
3.  **`Deploy Cloud Run`:** Implanta a imagem no serviço Cloud Run, injetando todas as variáveis de ambiente necessárias (`SECRET_KEY`, `CLOUD_SQL_CONNECTION_NAME`, etc.).
4.  **`Run Migrations & Collectstatic`:** **Crucial:** Executa *jobs* temporários do Cloud Run para rodar **`python manage.py migrate`** e **`python manage.py collectstatic --noinput`**, garantindo que o banco de dados e os estáticos sejam atualizados no ambiente de produção.

---

## 🛠️ Configuração de Desenvolvimento Local

Siga estas etapas para configurar e rodar o projeto localmente.

### 1. Pré-requisitos

Certifique-se de ter instalado:
* Python (3.11 ou superior recomendado)
* Git
* Docker e Docker Compose (Opcional, mas recomendado para o ambiente local)

### 2. Configuração do Ambiente

1.  **Clone o Repositório:**
    ```bash
    git clone https://github.com/snebur84/django-provisioning-system.git
    cd [pasta-do-projeto]
    ```

2.  **Crie e Ative o Ambiente Virtual:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate.bat   # Windows
    ```

3.  **Instale as Dependências:**
    ```bash
    pip install -r requirements-dev.txt
    ```

4.  **Crie o arquivo `.env`:**
    Crie um arquivo `.env` na raiz do projeto para armazenar variáveis de ambiente locais.
    **(Obrigatório para o fluxo de autenticação e banco de dados local)**

    ```env
    # --- Variáveis de Segurança ---
    SECRET_KEY="SUA_CHAVE_SECRETA_DEV_AQUI"
    DJANGO_DEBUG="1" # Modo debug ativado

    # --- Configuração de Banco de Dados Local (MySQL/SQLite) ---
    # Se usar MySQL local, preencha as credenciais. Caso contrário, use SQLite.
    # Exemplo SQLite (padrão)
    # DATABASE_URL=sqlite:///db.sqlite3

    # --- Configurações de Allauth/Email (DEV) ---
    ACCOUNT_EMAIL_VERIFICATION="none" # Para evitar envio de emails em DEV
    EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend"

    # --- Credenciais Google OAuth (DEV) ---
    # *AVISO*: As credenciais finais são inseridas no painel Admin (DB) em PRODUÇÃO.
    # Use estas apenas para o setup inicial no Admin.
    # SOCIALACCOUNT_GOOGLE_CLIENT_ID="SEU_CLIENT_ID_LOCAL"
    # SOCIALACCOUNT_GOOGLE_SECRET="SEU_SECRET_LOCAL"
    ```

### 3. Inicialização do Banco de Dados

1.  **Execute as Migrações:**
    ```bash
    python manage.py migrate
    ```

2.  **Crie um Superusuário:**
    ```bash
    python manage.py createsuperuser
    ```

3.  **Coleta de Estáticos (Obrigatório devido ao GCS em Prod):**
    ```bash
    python manage.py collectstatic
    ```

### 4. Rodar o Servidor

```bash
python manage.py runserver