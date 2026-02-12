# 🏥 Lacrei Saúde API

> **API RESTful de Gerenciamento de Consultas Médicas**
>
> Desenvolvida para a Lacrei Saúde, com foco em saúde inclusiva e de qualidade para a comunidade LGBTQIAPN+.

[![CI/CD Pipeline](https://github.com/seu-usuario/lacrei-saude-api/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/seu-usuario/lacrei-saude-api/actions)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/django-5.1-green.svg)](https://djangoproject.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Tecnologias](#-tecnologias)
- [Arquitetura](#-arquitetura)
- [Setup Local](#-setup-local)
- [Setup com Docker](#-setup-com-docker)
- [Executando os Testes](#-executando-os-testes)
- [Documentação da API](#-documentação-da-api)
- [Endpoints](#-endpoints)
- [Segurança](#-segurança)
- [Deploy (CI/CD)](#-deploy-cicd)
- [Proposta de Rollback](#-proposta-de-rollback)
- [Integração com Assas](#-integração-com-assas)
- [Justificativas Técnicas](#-justificativas-técnicas)
- [Erros Encontrados e Melhorias](#-erros-encontrados-e-melhorias)

---

## 🎯 Sobre o Projeto

API RESTful para gerenciamento de consultas médicas, incluindo:

- **CRUD completo** de profissionais da saúde
- **CRUD completo** de consultas médicas
- **Busca de consultas** pelo ID do profissional
- **Autenticação JWT** para proteção dos endpoints
- **Documentação interativa** via Swagger/Redoc
- **Proposta de integração** com Assas (gateway de pagamentos)

---

## 🛠 Tecnologias

| Tecnologia | Versão | Uso |
|---|---|---|
| **Python** | 3.12 | Linguagem principal |
| **Django** | 5.1 | Framework web |
| **Django REST Framework** | 3.15 | API RESTful |
| **PostgreSQL** | 16 | Banco de dados |
| **Poetry** | 1.8 | Gerenciamento de dependências |
| **Docker** + **Docker Compose** | Latest | Containerização |
| **GitHub Actions** | - | CI/CD Pipeline |
| **SimpleJWT** | 5.3 | Autenticação JWT |
| **drf-spectacular** | 0.28 | Documentação OpenAPI (Swagger/Redoc) |
| **Bleach** | 6.2 | Sanitização de inputs |
| **WhiteNoise** | 6.8 | Servir arquivos estáticos |
| **Gunicorn** | 23.0 | WSGI Server (produção) |

---

## 🏗 Arquitetura

```
lacrei-saude-api/
├── .github/
│   └── workflows/
│       └── ci-cd.yml              # Pipeline CI/CD
├── apps/
│   ├── profissionais/             # App de Profissionais
│   │   ├── models.py              # Modelo Profissional
│   │   ├── serializers.py         # Serializers + validação + sanitização
│   │   ├── views.py               # ViewSet CRUD
│   │   ├── urls.py                # Rotas
│   │   ├── tests.py               # Testes APITestCase
│   │   └── admin.py               # Admin Django
│   └── consultas/                 # App de Consultas
│       ├── models.py              # Modelo Consulta (FK → Profissional)
│       ├── serializers.py         # Serializers + validação
│       ├── views.py               # ViewSet CRUD + busca por profissional
│       ├── urls.py                # Rotas
│       ├── tests.py               # Testes APITestCase
│       ├── admin.py               # Admin Django
│       └── services/
│           └── assas_integration.py  # Proposta de integração Assas
├── core/
│   ├── settings/
│   │   ├── base.py                # Settings base (compartilhado)
│   │   ├── staging.py             # Settings staging
│   │   └── production.py          # Settings produção
│   ├── middleware/
│   │   └── logging_middleware.py   # Middleware de logging
│   ├── utils/
│   │   └── sanitization.py        # Utilitários de sanitização
│   ├── exceptions.py              # Handler de exceções customizado
│   ├── views.py                   # Health check
│   ├── urls.py                    # URLs root
│   ├── wsgi.py                    # WSGI
│   └── asgi.py                    # ASGI
├── logs/                          # Logs de acesso e erro
├── Dockerfile                     # Imagem Docker
├── docker-compose.yml             # Orquestração de containers
├── pyproject.toml                 # Dependências (Poetry)
├── manage.py                      # Django CLI
├── .env.example                   # Template de variáveis de ambiente
├── .flake8                        # Config do linter
├── .coveragerc                    # Config de cobertura de testes
└── README.md                      # Este arquivo
```

---

## 🚀 Setup Local

### Pré-requisitos

- Python 3.12+
- Poetry 1.8+
- PostgreSQL 16+

### Passo a passo

```bash
# 1. Clonar o repositório
git clone https://github.com/seu-usuario/lacrei-saude-api.git
cd lacrei-saude-api

# 2. Instalar dependências com Poetry
poetry install

# 3. Configurar variáveis de ambiente
cp .env.example .env
# Edite o .env com as credenciais do seu PostgreSQL local

# 4. Criar banco de dados (PostgreSQL deve estar rodando)
# No psql:
# CREATE DATABASE lacrei_saude;
# CREATE USER lacrei_user WITH PASSWORD 'sua_senha';
# GRANT ALL PRIVILEGES ON DATABASE lacrei_saude TO lacrei_user;

# 5. Executar migrações
poetry run python manage.py migrate

# 6. Criar superusuário (para acessar o admin e gerar tokens)
poetry run python manage.py createsuperuser

# 7. Rodar o servidor de desenvolvimento
poetry run python manage.py runserver

# A API estará disponível em http://localhost:8000
```

---

## 🐳 Setup com Docker

### Pré-requisitos

- Docker 24+
- Docker Compose v2+

### Início rápido

```bash
# 1. Clonar o repositório
git clone https://github.com/seu-usuario/lacrei-saude-api.git
cd lacrei-saude-api

# 2. Configurar variáveis de ambiente
cp .env.example .env

# 3. Subir containers (PostgreSQL + API)
docker compose up --build -d

# 4. Criar superusuário
docker compose exec web python manage.py createsuperuser

# A API estará disponível em http://localhost:8000
```

### Modo desenvolvimento (com hot reload)

```bash
docker compose --profile dev up web-dev db -d
```

### Parar containers

```bash
docker compose down

# Para remover volumes (limpar banco)
docker compose down -v
```

---

## 🧪 Executando os Testes

### Local (com Poetry)

```bash
# Rodar todos os testes
poetry run python manage.py test apps/ --verbosity=2

# Com cobertura de código
poetry run coverage run manage.py test apps/ --verbosity=2
poetry run coverage report --show-missing

# Gerar HTML da cobertura
poetry run coverage html
# Abrir htmlcov/index.html no navegador
```

### Com Docker

```bash
docker compose exec web python manage.py test apps/ --verbosity=2
```

### Cobertura dos testes

Os testes cobrem:

| Área | Testes |
|---|---|
| CRUD Profissionais | Criar, listar, detalhar, atualizar (PUT/PATCH), excluir |
| CRUD Consultas | Criar, listar, detalhar, atualizar (PUT/PATCH), excluir |
| Busca por profissional | Consultas filtradas pelo ID do profissional |
| Erros de validação | Campos ausentes, dados inválidos, data no passado |
| Sanitização | Remoção de HTML/XSS de inputs |
| Autenticação | Acesso negado sem token, token inválido |
| Regras de negócio | Exclusão de profissional com consultas vinculadas |

---

## 📖 Documentação da API

Após iniciar o servidor, acesse:

| URL | Descrição |
|---|---|
| `http://localhost:8000/api/docs/` | **Swagger UI** - Documentação interativa |
| `http://localhost:8000/api/redoc/` | **ReDoc** - Documentação alternativa |
| `http://localhost:8000/api/schema/` | **OpenAPI Schema** - JSON/YAML |

---

## 📡 Endpoints

### Autenticação (JWT)

```
POST /api/auth/token/          → Obter token (login)
POST /api/auth/token/refresh/  → Renovar token
POST /api/auth/token/verify/   → Verificar token
```

**Exemplo de login:**
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "sua_senha"}'
```

**Resposta:**
```json
{
  "access": "eyJ0eXAi...",
  "refresh": "eyJ0eXAi..."
}
```

**Usando o token:**
```bash
curl -X GET http://localhost:8000/api/profissionais/ \
  -H "Authorization: Bearer eyJ0eXAi..."
```

### Profissionais da Saúde

```
GET    /api/profissionais/          → Listar todos (paginado)
POST   /api/profissionais/          → Cadastrar novo
GET    /api/profissionais/{id}/     → Detalhar
PUT    /api/profissionais/{id}/     → Atualizar completo
PATCH  /api/profissionais/{id}/     → Atualizar parcial
DELETE /api/profissionais/{id}/     → Excluir
```

**Exemplo: Criar profissional**
```bash
curl -X POST http://localhost:8000/api/profissionais/ \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome_social": "Dra. Maria Silva",
    "profissao": "Medicina - Clínica Geral",
    "endereco": "Rua das Flores, 123 - São Paulo, SP",
    "contato": "maria.silva@email.com"
  }'
```

### Consultas Médicas

```
GET    /api/consultas/                                    → Listar todas (paginado)
POST   /api/consultas/                                    → Agendar nova
GET    /api/consultas/{id}/                               → Detalhar
PUT    /api/consultas/{id}/                               → Atualizar completa
PATCH  /api/consultas/{id}/                               → Atualizar parcial
DELETE /api/consultas/{id}/                               → Cancelar
GET    /api/consultas/por-profissional/{profissional_id}/ → Buscar por profissional
```

**Exemplo: Buscar consultas por profissional**
```bash
curl -X GET http://localhost:8000/api/consultas/por-profissional/1/ \
  -H "Authorization: Bearer SEU_TOKEN"
```

### Health Check

```
GET /api/health/ → Verificar status da aplicação (sem autenticação)
```

---

## 🔒 Segurança

### Implementações

| Proteção | Implementação |
|---|---|
| **SQL Injection** | Django ORM com queries parametrizadas (proteção nativa) |
| **XSS** | Sanitização de inputs com Bleach em todos os serializers |
| **CORS** | Configurado via `django-cors-headers` com origens permitidas |
| **Autenticação** | JWT (SimpleJWT) com rotation de refresh tokens |
| **Rate Limiting** | Throttling configurado (50 req/h anônimo, 200 req/h autenticado) |
| **HTTPS** | Forçado em staging/produção via HSTS |
| **Headers de Segurança** | X-Frame-Options: DENY, X-Content-Type-Options: nosniff |
| **Logging** | Middleware de logging para todas as requisições |
| **Validação de dados** | Validação em múltiplas camadas (serializer + model) |

### Proteção contra SQL Injection

O Django ORM **nativamente** utiliza queries parametrizadas, prevenindo SQL Injection:

```python
# ✅ Seguro - Django ORM usa queries parametrizadas
Profissional.objects.filter(nome_social=user_input)

# ❌ Nunca usado - Raw queries com interpolação de strings
Profissional.objects.raw(f"SELECT * FROM ... WHERE name = '{user_input}'")
```

---

## 🚀 Deploy (CI/CD)

### Pipeline GitHub Actions

O pipeline CI/CD (``.github/workflows/ci-cd.yml``) segue os steps obrigatórios:

```
1. 🔍 Lint      → Black + isort + Flake8
2. 🧪 Testes    → APITestCase com cobertura ≥ 80%
3. 🏗️ Build     → Docker image build
4. 🚀 Deploy    → Staging (branch staging) ou Produção (branch main)
```

### Ambientes

| Ambiente | Branch | URL | Settings |
|---|---|---|---|
| **Desenvolvimento** | `develop` | `localhost:8000` | `core.settings.base` |
| **Staging** | `staging` | `staging.lacrei-saude.com.br` | `core.settings.staging` |
| **Produção** | `main` | `api.lacrei-saude.com.br` | `core.settings.production` |

### Infraestrutura AWS

```
┌─────────────────────────────────────────────┐
│                  AWS Cloud                    │
│                                               │
│  ┌─────────┐    ┌─────────────┐    ┌──────┐  │
│  │   ECR   │───▶│   ECS       │───▶│ RDS  │  │
│  │ (Images)│    │ (Fargate)   │    │(PgSQL)│  │
│  └─────────┘    └──────┬──────┘    └──────┘  │
│                        │                      │
│                 ┌──────┴──────┐               │
│                 │     ALB     │               │
│                 │ (Load Bal.) │               │
│                 └─────────────┘               │
└─────────────────────────────────────────────┘
```

- **ECR**: Armazena imagens Docker
- **ECS Fargate**: Executa containers serverless
- **RDS PostgreSQL**: Banco de dados gerenciado
- **ALB**: Balanceamento de carga com health checks
- **CloudWatch**: Monitoramento e logs

### Secrets necessários (GitHub)

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
DJANGO_SECRET_KEY
DB_PASSWORD
```

---

## 🔄 Proposta de Rollback

### Estratégia: Blue/Green Deploy

Utilizamos **Blue/Green Deploy** com AWS ECS para minimizar downtime e permitir rollback instantâneo:

```
                    ┌──────── ALB ────────┐
                    │                      │
              ┌─────▼─────┐        ┌──────▼──────┐
              │   BLUE     │        │   GREEN      │
              │ (Atual)    │        │ (Nova versão)│
              │ v1.0.0     │        │ v1.1.0       │
              └────────────┘        └──────────────┘
                    │                      │
         100% tráfego              0% tráfego
         (até validação)           (em teste)
```

### Fluxo de Rollback

1. **Deploy automático**: GitHub Actions faz deploy da nova versão no ambiente **Green**
2. **Health checks**: ALB verifica saúde dos novos containers
3. **Troca de tráfego**: Se saudável, tráfego migra de Blue → Green
4. **Rollback**: Se falhar, tráfego volta para Blue instantaneamente

### Comandos de Rollback Manual

```bash
# Opção 1: Revert no GitHub Actions
# Reverter o último commit na branch main
git revert HEAD
git push origin main
# O pipeline será executado com o código anterior

# Opção 2: Deploy de versão anterior via AWS CLI
aws ecs update-service \
  --cluster lacrei-production-cluster \
  --service lacrei-api-production \
  --task-definition lacrei-api:VERSAO_ANTERIOR \
  --force-new-deployment

# Opção 3: Rollback de migração do banco
docker compose exec web python manage.py migrate app_name MIGRATION_NUMBER
```

### Checklist de Rollback

- [ ] Identificar a versão estável anterior
- [ ] Executar rollback via CLI ou GitHub Actions revert
- [ ] Verificar health checks pós-rollback
- [ ] Verificar logs de erro
- [ ] Comunicar time sobre o rollback
- [ ] Documentar o motivo e criar issue para fix

---

## 💳 Integração com Assas

### Proposta Arquitetural

A integração com a **Assas** (gateway de pagamentos) permite o split de pagamento entre a Lacrei Saúde e os profissionais. Arquivo: `apps/consultas/services/assas_integration.py`

### Fluxo Proposto

```
Paciente                     API Lacrei              Assas
   │                            │                      │
   │  1. Agendar consulta       │                      │
   ├───────────────────────────▶│                      │
   │                            │  2. Criar cobrança   │
   │                            ├─────────────────────▶│
   │                            │                      │
   │                            │  3. Configurar split  │
   │                            ├─────────────────────▶│
   │                            │                      │
   │  4. Link de pagamento      │                      │
   │◀───────────────────────────┤                      │
   │                            │                      │
   │  5. Pagar (PIX/Boleto)     │                      │
   ├──────────────────────────────────────────────────▶│
   │                            │                      │
   │                            │  6. Webhook pagamento │
   │                            │◀─────────────────────┤
   │                            │                      │
   │  7. Confirmação            │                      │
   │◀───────────────────────────┤                      │
```

### Split de Pagamento

- **80%** → Profissional da saúde
- **20%** → Taxa Lacrei Saúde

A implementação atual é um **mock** que demonstra toda a arquitetura. Para ativação em produção, basta substituir os métodos mock por chamadas HTTP reais à API da Assas.

---

## 💡 Justificativas Técnicas

### 1. Django + DRF
Escolhido por ser o framework web Python mais maduro, com excelente suporte a APIs REST, ORM robusto com proteção nativa contra SQL Injection, e ecossistema extenso de pacotes.

### 2. JWT (SimpleJWT)
Autenticação stateless ideal para APIs RESTful. Permite escalabilidade horizontal (múltiplas instâncias) sem necessidade de sessões no servidor. Rotation de refresh tokens aumenta a segurança.

### 3. PostgreSQL
Banco de dados relacional robusto, com excelente suporte a JSON, índices parciais e full-text search. Ideal para dados estruturados como profissionais e consultas.

### 4. Poetry
Gerenciador de dependências moderno que substitui pip + requirements.txt. Oferece lock file determinístico, resolução de dependências mais confiável e melhor gestão de ambientes virtuais.

### 5. Docker + Docker Compose
Containerização garante que o ambiente é replicável em qualquer máquina. Docker Compose simplifica a orquestração local de API + PostgreSQL. Em produção, ECS Fargate gerencia os containers.

### 6. Separação de Settings (base/staging/production)
Permite configurações específicas por ambiente sem duplicação de código. Base contém configurações compartilhadas, staging e production herdam e sobrescrevem apenas o necessário.

### 7. Bleach para Sanitização
Biblioteca especializada em sanitização HTML/XSS, complementando a proteção nativa do Django ORM contra SQL Injection. Aplicada diretamente nos serializers para proteção em múltiplas camadas.

### 8. drf-spectacular para Documentação
Gera documentação OpenAPI 3.0 automaticamente a partir do código, com Swagger UI e ReDoc. Reduz o risco de documentação desatualizada.

### 9. Blue/Green Deploy
Estratégia de deploy que permite rollback instantâneo em caso de falha, sem downtime. O ALB gerencia a troca de tráfego entre as versões.

### 10. Middleware de Logging
Logging centralizado captura todas as requisições com método, path, IP, status code e duração. Essencial para monitoramento, debugging e auditoria de acessos.

---

## 📝 Erros Encontrados e Melhorias

### Erros/Desafios Encontrados

1. **Encoding UTF-8 no Windows**: Necessário configurar `PYTHONIOENCODING=utf-8` para caracteres especiais em logs e testes.
2. **CORS em desenvolvimento**: Headers de CORS precisam incluir `Authorization` para JWT funcionar via Swagger UI.
3. **Timezone**: Configuração de `America/Sao_Paulo` com `USE_TZ=True` para consistência de datas.

### Melhorias Propostas

1. **Cache com Redis**: Implementar cache de consultas frequentes para reduzir carga no banco.
2. **WebSockets**: Notificações em tempo real para atualizações de consultas.
3. **Rate Limiting por IP**: Proteção mais granular contra abusos.
4. **Soft Delete**: Manter histórico de registros excluídos para auditoria.
5. **Paginação cursor-based**: Para datasets maiores, mais eficiente que offset-based.
6. **Observabilidade**: Integração com Prometheus + Grafana para métricas.
7. **Feature Flags**: Controle de funcionalidades com LaunchDarkly ou similar.
8. **API Versioning**: Versionamento de endpoints (v1, v2) para evolução sem breaking changes.

---

## 📄 Licença

Este projeto foi desenvolvido como parte do desafio técnico da Lacrei Saúde.

---

**Desenvolvido com ❤️ para a [Lacrei Saúde](https://lacreisaude.com.br/)**
