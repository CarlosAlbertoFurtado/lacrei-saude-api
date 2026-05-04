# 🏥 Lacrei Saúde API

> **API RESTful de Gerenciamento de Consultas Médicas**
>
> Desenvolvida para a Lacrei Saúde, com foco em saúde inclusiva e de qualidade para a comunidade LGBTQIAPN+.

[![CI/CD Pipeline](https://github.com/CarlosAlbertoFurtado/lacrei-saude-api/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/CarlosAlbertoFurtado/lacrei-saude-api/actions)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/django-5.1-green.svg)](https://djangoproject.com)

---

## 📋 Índice

1. [Sobre o Projeto](#-sobre-o-projeto)
2. [Tecnologias](#-tecnologias)
3. [Arquitetura](#-arquitetura)
4. [Setup Local](#-setup-local)
5. [Setup com Docker](#-setup-com-docker)
6. [Executando os Testes](#-executando-os-testes)
7. [Documentação da API](#-documentação-da-api)
8. [Endpoints](#-endpoints)
9. [Autenticação JWT](#-autenticação-jwt)
10. [Segurança](#-segurança)
11. [Logging & Monitoramento](#-logging--monitoramento)
12. [CI/CD Pipeline](#-cicd-pipeline)
13. [Deploy & Rollback](#-deploy--rollback)
14. [Integração Assas](#-integração-assas)
15. [Justificativas Técnicas](#-justificativas-técnicas)

---

## 🎯 Sobre o Projeto

API REST para gerenciamento de profissionais da saúde e consultas médicas, desenvolvida como parte do desafio técnico Lacrei Saúde.

### Funcionalidades
- ✅ **CRUD Profissionais** – Cadastro, listagem, atualização e exclusão de profissionais
- ✅ **CRUD Consultas** – Cadastro, listagem, atualização e exclusão de consultas
- ✅ **Busca por Profissional** – Endpoint customizado para consultas de um profissional específico
- ✅ **Autenticação JWT** – Tokens de acesso e refresh com SimpleJWT
- ✅ **Permissões** – Controle de acesso em todos os endpoints
- ✅ **CORS** – Configurado com django-cors-headers
- ✅ **Proteção XSS** – Sanitização de inputs com Bleach
- ✅ **SQL Injection** – Protegido nativamente pelo Django ORM
- ✅ **Logs** – Acesso e erro com middleware customizado + arquivo rotativo
- ✅ **Testes** – 42 testes automatizados com APITestCase
- ✅ **Docker** – Containerização completa com PostgreSQL
- ✅ **CI/CD** – Pipeline GitHub Actions (lint, test, build, deploy)
- ✅ **Documentação** – Swagger UI e ReDoc automáticos

---

## 🛠 Tecnologias

| Tecnologia | Versão | Uso |
|---|---|---|
| **Python** | 3.12 | Linguagem principal |
| **Django** | 5.1 | Framework web |
| **Django REST Framework** | 3.15 | API REST |
| **SimpleJWT** | 5.5 | Autenticação JWT |
| **PostgreSQL** | 16 | Banco de dados |
| **Docker** | - | Containerização |
| **Poetry** | 1.8 | Gerenciamento de dependências |
| **Gunicorn** | 22 | Servidor WSGI (produção) |
| **GitHub Actions** | - | CI/CD Pipeline |
| **drf-spectacular** | 0.29 | Documentação OpenAPI |
| **Bleach** | 6.3 | Sanitização de inputs |
| **WhiteNoise** | 6.11 | Arquivos estáticos |

---

## 🏗 Arquitetura

```
lacrei-saude-api/
├── .github/
│   └── workflows/
│       └── ci-cd.yml            # Pipeline CI/CD (lint, test, build, deploy)
├── apps/
│   ├── profissionais/           # App: Profissionais da Saúde
│   │   ├── models.py            #   Modelo com campos obrigatórios + índices
│   │   ├── services.py          #   NOVO: Camada de Domínio/Business Logic (Desacoplamento)
│   │   ├── serializers.py       #   Validação + sanitização de inputs
│   │   ├── views.py             #   ViewSet chamando Camada de Serviço
│   │   ├── tests.py             #   Testes automatizados + Edge Cases
│   │   ├── urls.py              #   Rotas REST
│   │   └── admin.py             #   Admin Django
│   └── consultas/               # App: Consultas Médicas
│       ├── models.py            #   Modelo com FK para Profissional (PROTECT)
│       ├── services.py          #   NOVO: Regras de negócio (ex: data retroativa)
│       ├── serializers.py       #   Validação de data + sanitização
│       ├── views.py             #   ViewSet com busca por profissional
│       ├── tests.py             #   Testes de erro e casos de borda
│       ├── urls.py              #   Rotas REST
│       ├── admin.py             #   Admin Django
│       └── services/
│           └── assas_integration.py  # Proposta integração Assas
├── core/
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── logging_middleware.py # Observabilidade: Logs de acesso/erro
│   ├── settings/
│   │   ├── base.py              # Settings base (JWT, CORS, logging, DRF)
│   │   ├── staging.py           # SSL + segurança para staging
│   │   └── production.py        # Segurança máxima + HSTS
│   ├── utils/
│   │   ├── __init__.py
│   │   └── sanitization.py      # Utilitário de limpeza anti-XSS
│   ├── views.py                 # Health Check detalhado (Métricas + Saúde)
│   └── urls.py                  # Rotas globais + Docs
├── scripts/
│   └── make_migrations.py       # Helper para migrações em Docker
├── Dockerfile                   # Build para produção
├── docker-compose.yml           # Orquestração local (API + DB)
├── pyproject.toml               # Poetry (dependências)
└── README.md                    # Documentação técnica completa
│   │   └── production.py        # HSTS + segurança máxima
│   ├── middleware/
│   │   └── logging_middleware.py # Logs de acesso (method, path, user, IP, duration)
│   ├── utils/
│   │   └── sanitization.py      # Utilitário de sanitização anti-XSS
│   ├── exceptions.py            # Handler de erros centralizado
│   ├── views.py                 # Health check endpoint
│   └── urls.py                  # Rotas principais (JWT, Swagger, apps)
├── Dockerfile                   # Build da imagem Docker
├── docker-compose.yml           # PostgreSQL + API + dev + testes
├── entrypoint.sh                # Script de inicialização Docker
├── pyproject.toml               # Dependências (Poetry)
├── .env.example                 # Template de variáveis de ambiente
└── manage.py
```

---

## 🚀 Setup Local

### Pré-requisitos
- Python 3.12+
- PostgreSQL 16+ (ou usar SQLite para testes rápidos)
- Poetry

### Passo a passo

```bash
# 1. Clonar o repositório
git clone https://github.com/CarlosAlbertoFurtado/lacrei-saude-api.git
cd lacrei-saude-api

# 2. Instalar dependências com Poetry
pip install poetry
poetry install

# 3. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas credenciais de banco de dados

# 4. Executar migrações
python manage.py migrate

# 5. Criar superusuário (para obter token JWT)
python manage.py createsuperuser

# 6. Iniciar o servidor
python manage.py runserver
```

A API estará disponível em `http://localhost:8000`

---

## 🐳 Setup com Docker

### Pré-requisitos
- Docker e Docker Compose

### Início rápido

```bash
# 1. Clonar o repositório
git clone https://github.com/CarlosAlbertoFurtado/lacrei-saude-api.git
cd lacrei-saude-api

# 2. Configurar variáveis de ambiente
cp .env.example .env

# 3. Subir os containers (PostgreSQL + API)
docker compose up --build -d

# A API estará em http://localhost:8000
# Swagger UI: http://localhost:8000/api/docs/
# Superusuário automático: admin / admin123
```

### Modo desenvolvimento (com hot reload)

```bash
docker compose --profile dev up --build web-dev
```

### Parar containers

```bash
docker compose down          # Manter dados
docker compose down -v       # Limpar tudo
```

---

## 🧪 Executando os Testes

### Local (com Poetry)

```bash
# Executar todos os testes
python manage.py test apps/ --verbosity=2

# Com cobertura de código
coverage run manage.py test apps/ --verbosity=2
coverage report -m
```

### Com Docker

```bash
docker compose --profile test run --rm test
```

### Cobertura dos testes

| App | Cenários testados | Total |
|---|---|---|
| **Profissionais** | CRUD, validação, sanitização, filtros, auth, conflito | 21 testes |
| **Consultas** | CRUD, validação, data passada, busca por profissional, auth | 21 testes |
| **Total** | **Cobertura completa dos requisitos** | **42 testes** |

#### Detalhamento dos testes

**Profissionais (`apps/profissionais/tests.py`)**:
- `test_criar_profissional_com_dados_validos` – Criação com sucesso
- `test_criar_profissional_sem_nome` – Validação campo obrigatório
- `test_criar_profissional_sem_profissao` – Validação campo obrigatório
- `test_criar_profissional_sem_endereco` – Validação campo obrigatório
- `test_criar_profissional_sem_contato` – Validação campo obrigatório
- `test_criar_profissional_com_nome_curto` – Validação comprimento mínimo
- `test_criar_profissional_com_xss` – Sanitização anti-XSS (Bleach)
- `test_criar_profissional_com_campos_html` – Sanitização HTML
- `test_listar_profissionais` – Listagem paginada
- `test_detalhar_profissional` – Busca por ID
- `test_detalhar_profissional_inexistente` – Retorna 404
- `test_filtrar_por_profissao` – Filtro por profissão
- `test_buscar_por_nome` – Busca textual
- `test_atualizar_profissional_completo` – PUT completo
- `test_atualizar_profissional_parcial` – PATCH parcial
- `test_atualizar_profissional_inexistente` – Retorna 404
- `test_excluir_profissional` – DELETE com sucesso
- `test_excluir_profissional_com_consultas` – Proteção de integridade (409)
- `test_acessar_sem_token` – Retorna 401 (autenticação obrigatória)
- `test_acessar_com_token_invalido` – Retorna 401
- `test_acessar_com_token_valido` – Retorna 200

**Consultas (`apps/consultas/tests.py`)**:
- `test_criar_consulta_com_dados_validos` – Criação com sucesso
- `test_criar_consulta_sem_profissional` – Validação campo obrigatório
- `test_criar_consulta_sem_data` – Validação campo obrigatório
- `test_criar_consulta_sem_observacoes` – Campo opcional funciona
- `test_criar_consulta_com_data_no_passado` – Validação de data futura
- `test_criar_consulta_com_profissional_inexistente` – Validação FK
- `test_criar_consulta_com_xss` – Sanitização anti-XSS (Bleach)
- `test_criar_consulta_com_html` – Sanitização HTML
- `test_listar_consultas` – Listagem paginada com detalhes profissional
- `test_detalhar_consulta` – Busca por ID
- `test_detalhar_consulta_inexistente` – Retorna 404
- `test_filtrar_consultas_por_profissional_id` – Filtro por FK
- `test_buscar_consultas_por_profissional` – Action customizada
- `test_buscar_consultas_por_profissional_inexistente` – Retorna 404
- `test_atualizar_consulta_completa` – PUT completo
- `test_atualizar_consulta_parcial` – PATCH parcial
- `test_atualizar_consulta_inexistente` – Retorna 404
- `test_excluir_consulta` – DELETE com sucesso
- `test_excluir_consulta_inexistente` – Retorna 404
- `test_acessar_sem_token` – Retorna 401 (autenticação obrigatória)
- `test_acessar_com_token_valido` – Retorna 200

---

## 📖 Documentação da API

| Interface | URL | Descrição |
|---|---|---|
| **Swagger UI** | `http://localhost:8000/api/docs/` | Documentação interativa |
| **ReDoc** | `http://localhost:8000/api/redoc/` | Documentação alternativa |
| **OpenAPI JSON** | `http://localhost:8000/api/schema/` | Schema OpenAPI 3.0 |

A documentação é gerada automaticamente pelo **drf-spectacular** com base nos serializers e viewsets.

---

## 📡 Endpoints

### Autenticação (JWT)

| Método | Endpoint | Descrição |
|---|---|---|
| `POST` | `/api/auth/token/` | Obter par de tokens (access + refresh) |
| `POST` | `/api/auth/token/refresh/` | Renovar token de acesso |
| `POST` | `/api/auth/token/verify/` | Verificar validade do token |

### Profissionais da Saúde

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/api/profissionais/` | Listar todos (paginado) |
| `POST` | `/api/profissionais/` | Cadastrar novo |
| `GET` | `/api/profissionais/{id}/` | Detalhar |
| `PUT` | `/api/profissionais/{id}/` | Atualizar completo |
| `PATCH` | `/api/profissionais/{id}/` | Atualizar parcial |
| `DELETE` | `/api/profissionais/{id}/` | Excluir |

### Consultas Médicas

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/api/consultas/` | Listar todas (paginado) |
| `POST` | `/api/consultas/` | Cadastrar nova |
| `GET` | `/api/consultas/{id}/` | Detalhar |
| `PUT` | `/api/consultas/{id}/` | Atualizar completa |
| `PATCH` | `/api/consultas/{id}/` | Atualizar parcial |
| `DELETE` | `/api/consultas/{id}/` | Excluir |
| `GET` | `/api/consultas/por-profissional/{prof_id}/` | Buscar por profissional |

### Health Check

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/api/health/` | Verifica saúde da API e banco de dados |

---

## 🔑 Autenticação JWT

Todos os endpoints (exceto `/api/auth/` e `/api/health/`) exigem autenticação JWT.

### Como obter um token

```bash
# 1. Obter o token (troque admin/admin123 pelas suas credenciais)
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Resposta:
# {
#   "access": "eyJhbGciOiJIUzI1NiIs...",
#   "refresh": "eyJhbGciOiJIUzI1NiIs..."
# }
```

### Usando o token nas requisições

```bash
# 2. Usar o token de acesso
curl -X GET http://localhost:8000/api/profissionais/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Renovar token expirado

```bash
# 3. Renovar com o refresh token
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "eyJhbGciOiJIUzI1NiIs..."}'
```

### Configuração JWT

| Parâmetro | Valor | Configurável via |
|---|---|---|
| Token de acesso expira em | 30 minutos | `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` |
| Token de refresh expira em | 7 dias | `JWT_REFRESH_TOKEN_LIFETIME_DAYS` |
| Rotação de refresh | Ativada | `ROTATE_REFRESH_TOKENS` |
| Tipo do header | `Bearer` | `AUTH_HEADER_TYPES` |

### Implementação no código

```python
# apps/profissionais/views.py  (e apps/consultas/views.py)
class ProfissionalViewSet(viewsets.ModelViewSet):
    # Autenticação e Permissões explícitas
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    ...

# core/settings/base.py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    ...
}
```

---

## 🔒 Segurança

### Implementações

| Proteção | Implementação | Arquivo |
|---|---|---|
| **Autenticação JWT** | `JWTAuthentication` explícito em cada ViewSet | `views.py` |
| **Permissões** | `IsAuthenticated` em todos os endpoints protegidos | `views.py` |
| **CORS** | `django-cors-headers` com origens configuráveis | `settings/base.py` |
| **Sanitização XSS** | `bleach.clean()` em todos os campos de texto | `serializers.py` |
| **SQL Injection** | Django ORM (queries parametrizadas nativas) | `models.py` |
| **Rate Limiting** | 50/h anônimo, 200/h autenticado | `settings/base.py` |
| **Security Headers** | `X-Frame-Options: DENY`, `X-Content-Type-Options` | `settings/base.py` |
| **HTTPS** | `SECURE_SSL_REDIRECT` em staging/production | `settings/staging.py` |
| **HSTS** | 1 ano com subdomínios em produção | `settings/production.py` |

### Configuração CORS

```python
# core/settings/base.py
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
CORS_ALLOW_HEADERS = [
    "accept", "authorization", "content-type", "origin", ...
]
```

### Proteção contra SQL Injection

O Django ORM é utilizado em **todas** as queries, garantindo parametrização automática:

```python
# Seguro - Django ORM gera query parametrizada
Profissional.objects.filter(nome_social__icontains=search_term)

# Nunca usamos SQL raw sem parametrização
```

---

## 📊 Observabilidade & Monitoramento

### 1. Health Check Detalhado (`/api/health/`)
O endpoint de saúde foi expandido para fornecer uma visão 360º da aplicação, não apenas do banco de dados.

**Campos da Resposta:**
- `status`: "healthy" ou "unhealthy"
- `timestamp`: Unix timestamp para verificação de latência
- `metrics`: Contagem em tempo real de Profissionais e Consultas
- `checks`: Status detalhado do banco de dados e informações do sistema (OS, Python Version)

### 2. Middleware de Logging (`core/middleware/logging_middleware.py`)
Todas as requisições são logadas automaticamente com nível de severidade dinâmico.
- **INFO**: Respostas 2xx e 3xx
- **WARNING**: Respostas 4xx (Erros de cliente/validação)
- **ERROR**: Respostas 5xx (Erros de servidor/exceções não tratadas)

### 3. Camada de Serviço (Service Layer)
A lógica de negócio foi movida das Views para arquivos `services.py`. Isso permite:
- **Testabilidade**: Testar regras de negócio sem simular requisições HTTP
- **Reuso**: Mesma lógica pode ser usada em comandos CLI, tasks Celery ou Views
- **Clean Architecture**: Views cuidam apenas do protocolo HTTP, Services cuidam do domínio.

---

## 🚀 CI/CD Pipeline

### Pipeline GitHub Actions (`.github/workflows/ci-cd.yml`)

O pipeline roda automaticamente a cada push nas branches `main`, `staging` e `develop`.

```
Push/PR → [1. Lint] → [2. Testes] → [3. Build Docker] → [4. Deploy]
```

### Etapas

| Etapa | O que faz | Quando roda |
|---|---|---|
| **🔍 Lint** | Black + isort + Flake8 | Sempre |
| **🧪 Testes** | `python manage.py test` com PostgreSQL real | Após lint passar |
| **🐳 Build** | Build da imagem Docker | Após testes passarem |
| **🚀 Deploy Staging** | Push ECR + deploy ECS | Branch `staging` |
| **🏭 Deploy Production** | Push ECR + Blue/Green ECS | Branch `main` |

### Serviço PostgreSQL no CI

Os testes rodam com **PostgreSQL real** no GitHub Actions (não SQLite):

```yaml
services:
  postgres:
    image: postgres:16-alpine
    env:
      POSTGRES_DB: lacrei_saude_test
      POSTGRES_USER: lacrei_user
      POSTGRES_PASSWORD: lacrei_password_test
    ports:
      - 5432:5432
```

---

## 🔄 Deploy & Rollback (AWS Cloud)

### Infraestrutura como Código e Estratégia
O deploy é automatizado via **GitHub Actions** para a **AWS**, utilizando serviços serverless para escalabilidade e baixo custo.

### Componentes AWS Utilizados:
1. **AWS ECS (Fargate)**: Executa os containers Docker sem necessidade de gerenciar servidores (EC2).
2. **AWS ECR**: Registry privado para armazenar as imagens Docker da Lacrei Saúde.
3. **AWS RDS (PostgreSQL 16)**: Banco de dados gerenciado com backup automático e Multi-AZ.
4. **AWS ALB (Load Balancer)**: Distribui o tráfego e gerencia o SSL (HTTPS).
5. **AWS Secrets Manager**: Armazena chaves sensíveis (DJANGO_SECRET_KEY, DB_PASSWORD).

### Estratégia: Blue/Green Deploy
Garante que a nova versão (Green) esteja 100% saudável antes de substituir a versão atual (Blue).

**Fluxo de Deploy:**
1. **Build**: GitHub Actions gera a imagem e envia para o ECR.
2. **Provision**: O ECS sobe novas instâncias da aplicação.
3. **Health Check**: O Load Balancer verifica se o endpoint `/api/health/` da nova versão retorna 200 OK.
4. **Switch**: Se aprovado, o tráfego é migrado. Se falhar, a versão antiga permanece ativa (Rollback Automático).

### Comandos para Operações Manuais
```bash
# Verificar status dos serviços na AWS
aws ecs describe-services --cluster lacrei-cluster --services lacrei-api

# Forçar redeploy (útil para atualizar segredos ou configurações)
aws ecs update-service --cluster lacrei-cluster --service lacrei-api --force-new-deployment
```

---

## 💳 Integração Assas

### Proposta Arquitetural

O arquivo `apps/consultas/services/assas_integration.py` contém a proposta completa de integração com o gateway de pagamento Assas.

### Fluxo Proposto

```
1. Paciente agenda consulta
2. API cria cobrança no Assas
3. Paciente efetua pagamento
4. Assas envia webhook de confirmação
5. API atualiza status da consulta para "confirmada"
6. Split automático: 80% profissional / 20% Lacrei
```

### Split de Pagamento

```python
# Distribuição do valor da consulta
SPLIT_CONFIG = {
    "profissional": 80,  # 80% para o profissional
    "lacrei": 20,         # 20% para Lacrei Saúde (taxa da plataforma)
}
```

---

## 💡 Justificativas Técnicas

### 1. Django + DRF
Framework Python mais maduro para APIs, com ORM robusto, admin integrado, e ecossistema vasto. O DRF adiciona serialização, autenticação, paginação e throttling prontos para produção.

### 2. JWT (SimpleJWT)
Autenticação stateless ideal para APIs REST. Tokens de acesso curtos (30min) com refresh tokens longos (7 dias) garantem segurança sem sacrificar UX. A rotação automática de refresh tokens previne token theft.

### 3. PostgreSQL
Banco de dados relacional robusto, ideal para dados estruturados como profissionais e consultas. Suporte nativo a JSON, full-text search, e melhor performance com índices compostos.

### 4. Poetry
Gerenciamento de dependências determinístico com lockfile, garantindo builds reprodutíveis. Superior ao pip/requirements.txt para projetos profissionais.

### 5. Docker + Docker Compose
Containerização garante consistência entre ambientes (dev, staging, prod). O docker-compose.yml inclui:
- **db**: PostgreSQL 16 com healthcheck
- **web**: API com Gunicorn (produção)
- **web-dev**: Django runserver (desenvolvimento)
- **test**: Runner de testes automatizados

### 6. Separação de Settings
Settings divididos em `base.py` (configurações compartilhadas), `staging.py` (SSL + logs verbose), e `production.py` (HSTS + rate limiting conservador). Permite controle granular por ambiente.

### 7. Bleach para Sanitização
Biblioteca especializada em sanitização HTML/XSS. Todos os campos de texto passam por `bleach.clean()` nos serializers antes de serem salvos, prevenindo ataques de Cross-Site Scripting.

### 8. drf-spectacular para Documentação
Gera documentação OpenAPI 3.0 automaticamente a partir dos serializers e viewsets. Interface Swagger UI interativa permite testar endpoints diretamente do navegador.

### 9. Blue/Green Deploy
Estratégia de deploy que mantém duas versões rodando simultaneamente, eliminando downtime e permitindo rollback instantâneo em caso de falha.

### 10. Middleware de Logging
Logging centralizado que captura todas as requisições com método, path, usuário, IP, status code e duração. Logs vão para console (stdout) e arquivos rotativos, facilitando integração com serviços de monitoramento.

---

## 📝 Variáveis de Ambiente

Copie `.env.example` para `.env` e configure:

```env
# Django
DJANGO_SECRET_KEY=sua-chave-secreta-aqui
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de Dados (PostgreSQL)
DB_NAME=lacrei_saude
DB_USER=lacrei_user
DB_PASSWORD=lacrei_password_secure
DB_HOST=db
DB_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=30
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
```

---

## 📄 Licença

Este projeto foi desenvolvido como parte do desafio técnico da Lacrei Saúde.

---

**Desenvolvido com ❤️ para a comunidade LGBTQIAPN+**
