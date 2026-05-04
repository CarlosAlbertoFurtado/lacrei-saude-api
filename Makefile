# ==============================================================================
# Makefile - Lacrei Saúde API
# Comandos de operação para desenvolvimento, staging e produção
# ==============================================================================

.PHONY: help install run test lint coverage docker-up docker-down docker-test \
        migrate superuser deploy-staging deploy-production logs health

# Cores para output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
NC     := \033[0m

help: ## Exibe esta ajuda
	@echo "$(GREEN)Lacrei Saúde API - Comandos Disponíveis$(NC)"
	@echo "========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

# ==============================================================================
# Desenvolvimento Local
# ==============================================================================

install: ## Instala dependências com Poetry
	pip install poetry==1.8.4
	poetry install --no-interaction

run: ## Inicia servidor de desenvolvimento
	python manage.py runserver 0.0.0.0:8000

migrate: ## Executa migrações do banco de dados
	python manage.py migrate --noinput

makemigrations: ## Cria novas migrações
	python manage.py makemigrations

superuser: ## Cria superusuário (admin/admin123)
	DJANGO_SUPERUSER_PASSWORD=admin123 python manage.py createsuperuser \
		--username admin --email admin@lacrei.com --noinput 2>/dev/null || true

shell: ## Abre shell Django interativo
	python manage.py shell

# ==============================================================================
# Qualidade de Código
# ==============================================================================

lint: ## Verifica formatação e estilo (Black + isort + Flake8)
	black --check --diff .
	isort --check-only --diff .
	flake8 .

format: ## Formata o código automaticamente (Black + isort)
	black .
	isort .

test: ## Executa todos os testes com verbosidade
	python manage.py test apps/ --verbosity=2

coverage: ## Executa testes com relatório de cobertura
	coverage run manage.py test apps/ --verbosity=2
	coverage report -m
	coverage html
	@echo "$(GREEN)Relatório HTML disponível em htmlcov/index.html$(NC)"

# ==============================================================================
# Docker
# ==============================================================================

docker-up: ## Sobe containers (PostgreSQL + API) em modo produção
	docker compose up --build -d
	@echo "$(GREEN)API disponível em http://localhost:8000$(NC)"
	@echo "$(GREEN)Swagger UI: http://localhost:8000/api/docs/$(NC)"

docker-dev: ## Sobe containers em modo desenvolvimento (hot reload)
	docker compose --profile dev up --build web-dev

docker-down: ## Para todos os containers (mantém dados)
	docker compose down

docker-clean: ## Para containers e remove volumes (limpa tudo)
	docker compose down -v

docker-test: ## Executa testes em container Docker
	docker compose --profile test run --rm test

docker-logs: ## Exibe logs dos containers
	docker compose logs -f web

# ==============================================================================
# Deploy
# ==============================================================================

deploy-staging: ## Deploy para ambiente de staging (AWS ECS)
	@echo "$(YELLOW)Executando deploy para STAGING...$(NC)"
	@echo "1. Build da imagem Docker..."
	docker build -t lacrei-saude-api:staging .
	@echo "2. Tag para ECR..."
	docker tag lacrei-saude-api:staging \
		$${AWS_ACCOUNT_ID}.dkr.ecr.$${AWS_REGION}.amazonaws.com/lacrei-saude-api:staging
	@echo "3. Push para ECR..."
	aws ecr get-login-password --region $${AWS_REGION} | \
		docker login --username AWS --password-stdin \
		$${AWS_ACCOUNT_ID}.dkr.ecr.$${AWS_REGION}.amazonaws.com
	docker push $${AWS_ACCOUNT_ID}.dkr.ecr.$${AWS_REGION}.amazonaws.com/lacrei-saude-api:staging
	@echo "4. Atualizando serviço ECS..."
	aws ecs update-service --cluster lacrei-cluster-staging \
		--service lacrei-api-staging --force-new-deployment
	@echo "$(GREEN)Deploy staging concluído! Aguardando health check...$(NC)"

deploy-production: ## Deploy para produção (AWS ECS Blue/Green)
	@echo "$(YELLOW)Executando deploy para PRODUÇÃO...$(NC)"
	@echo "⚠️  Este deploy utiliza estratégia Blue/Green."
	@echo "1. Build da imagem Docker..."
	docker build -t lacrei-saude-api:latest .
	@echo "2. Tag para ECR..."
	docker tag lacrei-saude-api:latest \
		$${AWS_ACCOUNT_ID}.dkr.ecr.$${AWS_REGION}.amazonaws.com/lacrei-saude-api:latest
	@echo "3. Push para ECR..."
	aws ecr get-login-password --region $${AWS_REGION} | \
		docker login --username AWS --password-stdin \
		$${AWS_ACCOUNT_ID}.dkr.ecr.$${AWS_REGION}.amazonaws.com
	docker push $${AWS_ACCOUNT_ID}.dkr.ecr.$${AWS_REGION}.amazonaws.com/lacrei-saude-api:latest
	@echo "4. Atualizando serviço ECS (Blue/Green)..."
	aws ecs update-service --cluster lacrei-cluster \
		--service lacrei-api --force-new-deployment
	@echo "$(GREEN)Deploy produção iniciado! O ALB fará o switch após health check.$(NC)"

# ==============================================================================
# Operações
# ==============================================================================

health: ## Verifica saúde da aplicação
	@curl -s http://localhost:8000/api/health/ | python -m json.tool

metrics: ## Exibe métricas da aplicação
	@curl -s http://localhost:8000/api/metrics/ | python -m json.tool

logs: ## Exibe logs da aplicação (últimas 100 linhas)
	@tail -n 100 logs/access.log 2>/dev/null || echo "Sem logs disponíveis"

logs-error: ## Exibe logs de erro (últimas 50 linhas)
	@tail -n 50 logs/error.log 2>/dev/null || echo "Sem erros registrados"

# ==============================================================================
# Verificação de Ambiente
# ==============================================================================

check-env: ## Verifica variáveis de ambiente necessárias
	@echo "Verificando variáveis de ambiente..."
	@test -f .env && echo "$(GREEN)✅ .env encontrado$(NC)" || echo "$(YELLOW)⚠️ .env não encontrado - copie .env.example$(NC)"
	@python -c "import django; print('$(GREEN)✅ Django', django.VERSION, '$(NC)')" 2>/dev/null || echo "$(YELLOW)⚠️ Django não instalado$(NC)"
	@python -c "import rest_framework; print('$(GREEN)✅ DRF instalado$(NC)')" 2>/dev/null || echo "$(YELLOW)⚠️ DRF não instalado$(NC)"
	@docker --version > /dev/null 2>&1 && echo "$(GREEN)✅ Docker disponível$(NC)" || echo "$(YELLOW)⚠️ Docker não encontrado$(NC)"
