#!/usr/bin/env python3.11
"""
Gateway API - Python 3.11
"""

from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import os
import sys
import logging
import re
from datetime import datetime
import pytz

from fastapi import (
    FastAPI, APIRouter, Request, UploadFile, Query, HTTPException
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from dotenv import load_dotenv
import httpx

# --- 프로젝트 내부 모듈 ---
from app.router.user_router import router as user_router
from app.router.chatbot_router import router as chatbot_router
# JWT 미들웨어 제거됨 - 웹 회원가입만 사용
from app.domain.discovery.model.service_discovery import ServiceDiscovery, ServiceType
from app.common.utility.constant.settings import Settings
from app.common.utility.factory.response_factory import ResponseFactory

# 한국 시간대 설정
os.environ['TZ'] = 'Asia/Seoul'

# ---------------------------------------------------------------------
# ENV
# Railway 환경에서는 dotenv 로드하지 않음
if os.getenv("RAILWAY_ENVIRONMENT") != "true":
    load_dotenv()

# Railway 환경 감지 개선
RAILWAY_ENV = (
    os.getenv("RAILWAY_ENVIRONMENT", "false").lower() == "true" or
    os.getenv("RAILWAY_ENVIRONMENT", "").lower() == "production"
)

# 로깅 설정 (한국 시간대 적용)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("gateway_api")

# Uvicorn 액세스 로그 형식 통일
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.handlers.clear()
uvicorn_access_handler = logging.StreamHandler(sys.stdout)
uvicorn_access_handler.setFormatter(logging.Formatter(
    "%(asctime)s - uvicorn.access - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))
uvicorn_access_logger.addHandler(uvicorn_access_handler)
uvicorn_access_logger.setLevel(logging.INFO)

# httpx 로그 형식 통일
httpx_logger = logging.getLogger("httpx")
httpx_logger.handlers.clear()
httpx_handler = logging.StreamHandler(sys.stdout)
httpx_handler.setFormatter(logging.Formatter(
    "%(asctime)s - httpx - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))
httpx_logger.addHandler(httpx_handler)
httpx_logger.setLevel(logging.INFO)

# Railway 환경변수 디버깅
logger.info("🔍 Gateway Railway 환경변수 디버깅:")
logger.info(f"   RAILWAY_ENVIRONMENT: {os.getenv('RAILWAY_ENVIRONMENT', 'NOT_SET')}")
logger.info(f"   PORT: {os.getenv('PORT', 'NOT_SET')}")
logger.info(f"   AUTH_SERVICE_URL: {os.getenv('AUTH_SERVICE_URL', 'NOT_SET')}")
logger.info(f"   RAILWAY_ENV (계산됨): {RAILWAY_ENV}")

# 모든 환경변수 디버깅 (Railway 문제 해결용)
logger.info("🔍 전체 환경변수 디버깅:")
for key, value in os.environ.items():
    if 'RAILWAY' in key or 'AUTH' in key or 'PORT' in key or 'DATABASE' in key:
        logger.info(f"   {key}: {value}")

# 환경변수 검증
if RAILWAY_ENV:
    auth_url = os.getenv('AUTH_SERVICE_URL')
    if not auth_url:
        logger.error("❌ Railway 환경에서 AUTH_SERVICE_URL이 설정되지 않음")
        logger.error("❌ Railway에서 AUTH_SERVICE_URL 환경변수를 설정해주세요")
    else:
        logger.info(f"✅ AUTH_SERVICE_URL 설정됨: {auth_url}")
else:
    logger.info("🐳 Docker 환경에서 AUTH_SERVICE_URL 확인 중...")
    auth_url = os.getenv('AUTH_SERVICE_URL')
    if auth_url:
        logger.info(f"✅ AUTH_SERVICE_URL 설정됨: {auth_url}")
    else:
        logger.warning("⚠️ AUTH_SERVICE_URL이 설정되지 않음 (기본값 사용)")

# Docker/Railway 환경에서 로그 레벨 강제 설정
if os.getenv("RAILWAY_ENVIRONMENT", "false").lower() == "true" or os.getenv("RAILWAY_ENVIRONMENT", "").lower() == "production":
    logging.getLogger().setLevel(logging.INFO)
    logger.setLevel(logging.INFO)
    logger.info("🚂 Railway 환경에서 로깅 레벨을 INFO로 설정")
    
    # Railway에서 로그 지속성을 위한 추가 설정
    import sys
    sys.stdout.flush()
    sys.stderr.flush()
    
    # 모든 로거에 대해 강제 출력 설정
    for handler in logging.getLogger().handlers:
        handler.flush()
    
    logger.info("🔄 Railway 로그 출력 강제 플러시 완료")
else:
    # Docker 환경에서도 동일한 로깅 설정
    logging.getLogger().setLevel(logging.INFO)
    logger.setLevel(logging.INFO)
    logger.info("🐳 Docker 환경에서 로깅 레벨을 INFO로 설정")
    
    # Docker에서도 로그 지속성을 위한 설정
    import sys
    sys.stdout.flush()
    sys.stderr.flush()
    
    # 모든 로거에 대해 강제 출력 설정
    for handler in logging.getLogger().handlers:
        handler.flush()
    
    logger.info("🔄 Docker 로그 출력 강제 플러시 완료")

# 파일이 필요한 서비스 (필요 시 채워서 사용)
FILE_REQUIRED_SERVICES: set[ServiceType] = set()

# ---------------------------------------------------------------------
# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Gateway API 서비스 시작")
    logger.info(
        f"환경: {'Railway' if RAILWAY_ENV else 'Local/Docker'}"
    )
    logger.info(f"포트: {os.getenv('PORT', '8080')}")
    app.state.settings = Settings()
    yield
    logger.info("🛑 Gateway API 서비스 종료")

# ---------------------------------------------------------------------
# 앱
app = FastAPI(
    title="Gateway API",
    description="Gateway API for GreenSteel",
    version="0.1.0",
    docs_url="/docs",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------
# CORS: 환경변수 기반 설정으로 개선
FRONTEND_ORIGIN_ENV = os.getenv("FRONTEND_ORIGIN", "https://www.minyoung.cloud")

# 환경변수에서 콤마로 구분된 도메인들을 파싱
FRONTEND_ORIGINS = [origin.strip() for origin in FRONTEND_ORIGIN_ENV.split(",") if origin.strip()]

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000", 
    "http://frontend:3000",   # Docker 내부 네트워크
    "https://www.minyoung.cloud",
    "https://minyoung.cloud",
    "http://www.minyoung.cloud",  # HTTP 버전도 추가
    "http://minyoung.cloud",      # HTTP 버전도 추가
    "https://greensteel.vercel.app",
] + FRONTEND_ORIGINS  # 환경변수에서 가져온 값들을 추가

# 디버깅을 위한 로그 추가
logger.info("🔧 CORS 설정 정보:")
logger.info(f"   FRONTEND_ORIGIN_ENV: {FRONTEND_ORIGIN_ENV}")
logger.info(f"   FRONTEND_ORIGINS (파싱됨): {FRONTEND_ORIGINS}")
logger.info(f"   ALLOWED_ORIGINS: {ALLOWED_ORIGINS}")

ALLOW_ORIGIN_REGEX = r"^https:\/\/[a-z0-9-]+\.vercel\.app$"  # 모든 Vercel 프리뷰 허용

# CORS 디버깅 미들웨어 (CORS 미들웨어보다 먼저 실행되도록)
@app.middleware("http")
async def cors_debug_middleware(request: Request, call_next):
    """CORS 요청 디버깅을 위한 미들웨어"""
    origin = request.headers.get("origin")
    method = request.method
    path = request.url.path
    
    logger.info(f"🌐 CORS 디버깅: {method} {path}")
    logger.info(f"   Origin: {origin}")
    logger.info(f"   User-Agent: {request.headers.get('user-agent', 'NOT_SET')}")
    logger.info(f"   Allowed Origins: {ALLOWED_ORIGINS}")
    logger.info(f"   FRONTEND_ORIGIN_ENV: {FRONTEND_ORIGIN_ENV}")
    
    if origin:
        is_allowed = origin in ALLOWED_ORIGINS or re.match(ALLOW_ORIGIN_REGEX, origin)
        logger.info(f"   Origin Allowed: {is_allowed}")
    
    try:
        response = await call_next(request)
        
        # CORS 헤더 확인
        cors_headers = {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
        if cors_headers:
            logger.info(f"   CORS Headers: {cors_headers}")
        
        logger.info(f"✅ 요청 처리 완료: {method} {path} -> {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"❌ 요청 처리 중 오류: {method} {path} - {str(e)}")
        raise

# CORS 미들웨어 (디버깅 미들웨어 이후에 추가)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=ALLOW_ORIGIN_REGEX,
    allow_credentials=True,  # 쿠키/세션 사용 시 True
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # 명시적으로 허용
    allow_headers=["*"],  # 모든 헤더 허용
    expose_headers=["Set-Cookie", "Content-Length", "Content-Type"],  # 명시적으로 노출
    max_age=86400,
)

logger.info("✅ CORS 미들웨어 설정 완료")

def _forward_headers(request: Request) -> Dict[str, str]:
    skip = {"host", "content-length"}
    return {k: v for k, v in request.headers.items() if k.lower() not in skip}

def _add_cors_headers(response_headers: dict, origin: str) -> dict:
    """CORS 헤더를 응답 헤더에 추가"""
    if origin and (origin in ALLOWED_ORIGINS or re.match(ALLOW_ORIGIN_REGEX, origin)):
        response_headers["Access-Control-Allow-Origin"] = origin
    else:
        response_headers["Access-Control-Allow-Origin"] = "https://www.minyoung.cloud"
    
    response_headers["Access-Control-Allow-Credentials"] = "true"
    response_headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response_headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    response_headers["Access-Control-Expose-Headers"] = "Set-Cookie"
    response_headers["Access-Control-Max-Age"] = "86400"
    return response_headers

async def _handle_auth_service_request(path: str, request: Request) -> Response:
    """Auth Service 요청 처리"""
    logger.info(f"🚀 🔐 AUTH 프록시 요청 시작: /auth/{path}")
    
    body: bytes = await request.body()
    AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8081").rstrip('/')
    auth_url = f"{AUTH_SERVICE_URL}/auth/{path}"
    
    if not auth_url.startswith(('http://', 'https://')):
        logger.error(f"❌ 잘못된 Auth Service URL 형식: {auth_url}")
        return JSONResponse(content={"detail": f"잘못된 Auth Service URL: {auth_url}"}, status_code=500)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method="POST", url=auth_url, headers=_forward_headers(request),
                content=body, timeout=30.0
            )
            
            response_headers = dict(response.headers)
            origin = request.headers.get("origin")
            response_headers = _add_cors_headers(response_headers, origin)
            
            return Response(
                content=response.content, status_code=response.status_code,
                headers=response_headers, media_type=response.headers.get("content-type", "application/json")
            )
    except httpx.ConnectError as e:
        logger.error(f"❌ Auth Service 연결 실패: {auth_url} - {str(e)}")
        return JSONResponse(content={"detail": f"Auth Service 연결 실패: {str(e)}"}, status_code=503)
    except httpx.TimeoutException as e:
        logger.error(f"⏰ Auth Service 요청 타임아웃: {auth_url} - {str(e)}")
        return JSONResponse(content={"detail": f"Auth Service 요청 타임아웃: {str(e)}"}, status_code=504)
    except Exception as e:
        logger.error(f"❌ Auth Service 요청 실패: {auth_url} - {str(e)}")
        return JSONResponse(content={"detail": f"Auth Service 요청 실패: {str(e)}"}, status_code=500)

async def _handle_general_service_request(service: ServiceType, path: str, request: Request, 
                                        file: Optional[UploadFile], sheet_names: Optional[List[str]]) -> Response:
    """일반 서비스 요청 처리"""
    logger.info(f"🌈 POST 프록시 시작: 서비스={service}, 경로={path}")
    
    body: bytes = await request.body()
    factory = ServiceDiscovery(service_type=service)
    headers = _forward_headers(request)
    
    files = None
    params = None
    
    if service in FILE_REQUIRED_SERVICES:
        if "upload" in path and not file:
            raise HTTPException(status_code=400, detail=f"서비스 {service}에는 파일 업로드가 필요합니다.")
        if file:
            file_content = await file.read()
            files = {"file": (file.filename, file_content, file.content_type)}
            await file.seek(0)
        if sheet_names:
            params = {"sheet_name": sheet_names}
    
    resp = await factory.request(
        method="POST", path=path, headers=headers,
        body=body if files is None else None, files=files, params=params,
        cookies=request.cookies
    )
    
    out = ResponseFactory.create_response(resp)
    if "set-cookie" in resp.headers:
        out.headers["set-cookie"] = resp.headers["set-cookie"]
    
    return out

# ---------------------------------------------------------------------
# 기본 루트 (헬스)
@app.get("/")
async def root():
    return {"message": "GreenSteel Gateway API", "docs": "/docs", "version": "0.1.0"}

@app.options("/")
async def root_options(request: Request):
    """루트 레벨 OPTIONS 요청 처리"""
    logger.info(f"🌐 루트 OPTIONS 요청: {request.headers.get('Origin', 'NOT_SET')}")
    origin = request.headers.get('Origin', FRONTEND_ORIGINS[0] if FRONTEND_ORIGINS else "https://www.minyoung.cloud")
    
    return Response(
        status_code=200,
        headers={
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS, PATCH',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Cache-Control',
            'Access-Control-Expose-Headers': 'Set-Cookie, Content-Length, Content-Type',
            'Access-Control-Max-Age': '86400'
        }
    )

@app.get("/healthz")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "service": "gateway",
        "timestamp": datetime.now().isoformat(),
        "environment": "Railway" if RAILWAY_ENV else "Local/Docker",
        "environment_vars": {
            "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "NOT_SET"),
            "PORT": os.getenv("PORT", "NOT_SET"),
            "AUTH_SERVICE_URL": os.getenv("AUTH_SERVICE_URL", "NOT_SET"),
            "FRONTEND_ORIGIN": FRONTEND_ORIGINS
        }
    }

# Auth 라우터 제거 - auth-service에서 직접 처리

# 게이트웨이 라우터 (다른 서비스용)
gateway_router = APIRouter(prefix="/api/v1", tags=["Gateway API"])


# ---------------------------------------------------------------------
# OPTIONS 요청 핸들러 (CORS preflight)
@gateway_router.options("/{service}/{path:path}", summary="OPTIONS 프록시")
async def proxy_options(service: ServiceType, path: str, request: Request):
    """OPTIONS 요청을 처리합니다 (CORS preflight)."""
    logger.info(f"🚀 [PROXY >>] Method: OPTIONS, Service: {service.value}, Path: /{path}")
    logger.info("🌐 OPTIONS 요청 CORS 디버깅:")
    logger.info(f"   Origin: {request.headers.get('Origin', 'NOT_SET')}")
    logger.info(f"   Access-Control-Request-Method: {request.headers.get('Access-Control-Request-Method', 'NOT_SET')}")
    logger.info(f"   Access-Control-Request-Headers: {request.headers.get('Access-Control-Request-Headers', 'NOT_SET')}")
    logger.info(f"   User-Agent: {request.headers.get('User-Agent', 'NOT_SET')}")
    
    origin = request.headers.get('Origin', FRONTEND_ORIGINS)
    
    # Origin 검증
    is_allowed = origin in ALLOWED_ORIGINS or re.match(ALLOW_ORIGIN_REGEX, origin)
    logger.info(f"   Origin Allowed: {is_allowed}")
    logger.info(f"   Allowed Origins: {ALLOWED_ORIGINS}")
    
    if not is_allowed:
        logger.warning(f"⚠️ CORS Origin 차단: {origin}")
        return Response(
            status_code=403,
            content="CORS Origin not allowed"
        )
    
    logger.info(f"✅ CORS Origin 허용: {origin}")
    logger.info("✅ OPTIONS 응답 헤더 설정 완료")
    
    # 더 포괄적인 CORS 헤더 설정
    response_headers = {
        'Access-Control-Allow-Origin': origin,
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS, PATCH',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Cache-Control',
        'Access-Control-Expose-Headers': 'Set-Cookie, Content-Length, Content-Type',
        'Access-Control-Max-Age': '86400'
    }
    
    logger.info(f"📤 OPTIONS 응답 헤더: {response_headers}")
    
    return Response(
        status_code=200,
        headers=response_headers
    )

# ---------------------------------------------------------------------
# 동적 프록시 (POST) - 세션 쿠키 전달/Set-Cookie 패스스루
@gateway_router.post("/{service}/{path:path}", summary="POST 프록시")
async def proxy_post(
    service: ServiceType,
    path: str,
    request: Request,
    file: Optional[UploadFile] = None,
    sheet_names: Optional[List[str]] = Query(None, alias="sheet_name"),
):
    try:
        if service == ServiceType.AUTH:
            return await _handle_auth_service_request(path, request)
        else:
            return await _handle_general_service_request(service, path, request, file, sheet_names)
    except HTTPException as he:
        logger.error(f"❌ HTTP 예외: {he.status_code} - {he.detail}")
        return JSONResponse(content={"detail": he.detail}, status_code=he.status_code)
    except Exception as e:
        logger.exception(f"❌ POST 프록시 처리 중 오류: {str(e)}")
        return JSONResponse(content={"detail": f"Gateway error: {str(e)}"}, status_code=500)



# ---------------------------------------------------------------------
# 라우터 등록
app.include_router(gateway_router)
app.include_router(user_router)  # user_router 등록 추가

# ---------------------------------------------------------------------
# 로컬 실행용
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    logger.info(f"🚀 Gateway API 시작 - 포트: {port}")
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=port,
        reload=False,
        log_level="info",
        access_log=True,
        log_config=None  # 우리가 설정한 로깅 설정 사용
    )
