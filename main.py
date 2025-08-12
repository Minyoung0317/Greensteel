from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import uvicorn
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from gateway.app.domain.discovery.model.service_registry import ServiceRegistry
from gateway.app.domain.discovery.controller.discovery_controller import DiscoveryController
from gateway.app.router.proxy_router import ProxyRouter


# 환경 변수 설정
PORT = 8080
HOST = os.getenv("GATEWAY_HOST", "0.0.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# 전역 서비스 레지스트리
service_registry = ServiceRegistry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시
    logger.info(f"Starting Gateway Service in {ENVIRONMENT} environment...")
    yield
    # 종료 시
    logger.info("Shutting down Gateway Service...")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title="MSA Gateway API",
    description="""
    ## MSA Gateway API Documentation
    
    이 API는 마이크로서비스 아키텍처에서 서비스 디스커버리와 프록시 기능을 제공합니다.
    
    ### 주요 기능:
    * **서비스 디스커버리**: 마이크로서비스의 등록, 해제, 조회
    * **로드 밸런싱**: 라운드 로빈 방식의 로드 밸런싱
    * **헬스 체크**: 서비스 인스턴스의 상태 모니터링
    * **프록시**: 요청을 적절한 서비스로 전달
    
    ### 사용 방법:
    1. 서비스를 `/discovery/register`로 등록
    2. `/proxy/{service_name}/{path}`로 서비스에 요청 전달
    3. `/discovery/services`로 등록된 서비스 조회
    """,
    version="1.0.0",
    contact={
        "name": "MSA Gateway Team",
        "email": "gateway@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS 설정
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host 설정
allowed_hosts = os.getenv("ALLOWED_HOSTS", "*").split(",")
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts
)


# 라우터 등록
discovery_controller = DiscoveryController()
proxy_router = ProxyRouter(service_registry)

app.include_router(discovery_controller.get_router())
app.include_router(proxy_router.get_router())


# 루트 엔드포인트
@app.get("/", tags=["Gateway"])
async def root():
    """
    게이트웨이 상태 확인
    
    게이트웨이의 기본 상태와 사용 가능한 서비스 정보를 반환합니다.
    """
    return {
        "message": "MSA Gateway is running",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "timestamp": datetime.now().isoformat(),
        "services": {
            "discovery": "/discovery",
            "proxy": "/proxy"
        },
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
    }





# 서비스 정보 엔드포인트
@app.get("/info", tags=["Gateway"])
async def service_info():
    """
    서비스 정보 조회
    
    게이트웨이의 상세 정보와 사용 가능한 엔드포인트 목록을 반환합니다.
    """
    return {
        "name": "MSA Gateway",
        "description": "Microservice Architecture Gateway",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "features": [
            "Service Discovery",
            "Load Balancing", 
            "Request Proxy"
        ],
        "endpoints": {
            "discovery": {
                "register": "POST /discovery/register",
                "unregister": "DELETE /discovery/unregister/{service_name}/{instance_id}",
                "services": "GET /discovery/services",
                "service_instances": "GET /discovery/services/{service_name}"
            },
            "proxy": {
                "forward": "ALL /proxy/{service_name}/{path}"
            }
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


# 커스텀 OpenAPI 스키마 설정
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # 서버 정보 추가
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    # 태그 정보 추가
    openapi_schema["tags"] = [
        {
            "name": "Gateway",
            "description": "게이트웨이 기본 정보 및 상태 확인"
        },
        {
            "name": "discovery", 
            "description": "서비스 디스커버리 관련 API"
        },
        {
            "name": "proxy",
            "description": "프록시 및 요청 전달 관련 API"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=ENVIRONMENT == "development",
        log_level=LOG_LEVEL.lower()
    )
