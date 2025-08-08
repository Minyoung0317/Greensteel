# 모든 명령어 앞에 'make' 를 붙여서 실행해야 함

# 🔧 공통 명령어
up:
	docker-compose up -d --build

down:
	docker-compose down

logs:
	docker-compose logs -f

restart:
	docker-compose down && docker-compose up -d --build

ps:
	docker-compose ps

# 🚀 마이크로서비스별 명령어

## gateway
build-gateway:
	docker-compose build gateway

up-gateway:
	docker-compose up -d gateway

down-gateway:
	docker-compose stop gateway

logs-gateway:
	docker-compose logs -f gateway

restart-gateway:
	docker-compose stop gateway && docker-compose up -d gateway

## cbam-service
build-cbam:
	docker-compose build cbam-service

up-cbam:
	docker-compose up -d cbam-service

down-cbam:
	docker-compose stop cbam-service

logs-cbam:
	docker-compose logs -f cbam-service

restart-cbam:
	docker-compose stop cbam-service && docker-compose up -d cbam-service

## chatbot-service
build-chatbot:
	docker-compose build chatbot-service

up-chatbot:
	docker-compose up -d chatbot-service

down-chatbot:
	docker-compose stop chatbot-service

logs-chatbot:
	docker-compose logs -f chatbot-service

restart-chatbot:
	docker-compose stop chatbot-service && docker-compose up -d chatbot-service

## lca-service
build-lca:
	docker-compose build lca-service

up-lca:
	docker-compose up -d lca-service

down-lca:
	docker-compose stop lca-service

logs-lca:
	docker-compose logs -f lca-service

restart-lca:
	docker-compose stop lca-service && docker-compose up -d lca-service

## report-service
build-report:
	docker-compose build report-service

up-report:
	docker-compose up -d report-service

down-report:
	docker-compose stop report-service

logs-report:
	docker-compose logs -f report-service

restart-report:
	docker-compose stop report-service && docker-compose up -d report-service

## redis
build-redis:
	docker-compose build redis

up-redis:
	docker-compose up -d redis

down-redis:
	docker-compose stop redis

logs-redis:
	docker-compose logs -f redis

restart-redis:
	docker-compose stop redis && docker-compose up -d redis
