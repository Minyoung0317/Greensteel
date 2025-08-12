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
from app.domain.discovery.model.service_discovery import ServiceDiscovery
from app.domain.discovery.model.service_type import ServiceType
from app.common.utility.constant.settings import Settings
from app.common.utility.factory.response_factory import ResponseFactory

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

# Railway 환경변수 디버깅
logger = logging.getLogger("gateway_api")
logger.info(f"🔍 Railway 환경변수 디버깅:")
logger.info(f"   RAILWAY_ENVIRONMENT: {os.getenv('RAILWAY_ENVIRONMENT', 'NOT_SET')}")
logger.info(f"   PORT: {os.getenv('PORT', 'NOT_SET')}")
logger.info(f"   AUTH_SERVICE_URL: {os.getenv('AUTH_SERVICE_URL', 'NOT_SET')}")
logger.info(f"   RAILWAY_ENV (계산됨): {RAILWAY_ENV}")

# 환경변수 검증
if RAILWAY_ENV:
    auth_url = os.getenv('AUTH_SERVICE_URL')
    if not auth_url:
        logger.error("❌ Railway 환경에서 AUTH_SERVICE_URL이 설정되지 않음")
    else:
        logger.info(f"✅ AUTH_SERVICE_URL 설정됨: {auth_url}")

# 로깅
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("gateway_api")

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
# CORS: 프로덕션 도메인은 정확히, 프리뷰는 정규식으로 허용
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://frontend:3000",   # Docker 내부 네트워크
    "https://www.minyoung.cloud",  # + 끝 슬래시(/) 금지
    "https://minyoung.cloud",      # + 끝 슬래시(/) 금지
    "https://greensteel.vercel.app",  # + 끝 슬래시(/) 금지
]

ALLOW_ORIGIN_REGEX = r"^https:\/\/[a-z0-9-]+\.vercel\.app$"  # 모든 Vercel 프리뷰 허용

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=ALLOW_ORIGIN_REGEX,
    allow_credentials=True,  # 쿠키/세션 사용 시 True
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

# CORS 디버깅 미들웨어
@app.middleware("http")
async def cors_debug_middleware(request: Request, call_next):
    """CORS 요청 디버깅을 위한 미들웨어"""
    origin = request.headers.get("origin")
    method = request.method
    
    logger.info(f"🌐 CORS 디버깅: {method} {request.url.path}")
    logger.info(f"   Origin: {origin}")
    logger.info(f"   Allowed Origins: {ALLOWED_ORIGINS}")
    
    if origin:
        is_allowed = origin in ALLOWED_ORIGINS or re.match(ALLOW_ORIGIN_REGEX, origin)
        logger.info(f"   Origin Allowed: {is_allowed}")
    
    response = await call_next(request)
    
    # CORS 헤더 확인
    cors_headers = {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
    if cors_headers:
        logger.info(f"   CORS Headers: {cors_headers}")
    
    return response

def _forward_headers(request: Request) -> Dict[str, str]:
    skip = {"host", "content-length"}
    return {k: v for k, v in request.headers.items() if k.lower() not in skip}

# ---------------------------------------------------------------------
# 기본 루트 (헬스)
@app.get("/")
async def root():
    return {"message": "GreenSteel Gateway API", "docs": "/docs", "version": "0.1.0"}

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
            "AUTH_SERVICE_URL": os.getenv("AUTH_SERVICE_URL", "NOT_SET")
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
    logger.info(f"[PROXY >>] Method: OPTIONS, Service: {service.value}, Path: /{path}")
    logger.info(f"🌐 OPTIONS 요청 CORS 디버깅:")
    logger.info(f"   Origin: {request.headers.get('Origin', 'NOT_SET')}")
    logger.info(f"   Access-Control-Request-Method: {request.headers.get('Access-Control-Request-Method', 'NOT_SET')}")
    logger.info(f"   Access-Control-Request-Headers: {request.headers.get('Access-Control-Request-Headers', 'NOT_SET')}")
    
    origin = request.headers.get('Origin', 'https://www.minyoung.cloud')
    
    # Origin 검증
    is_allowed = origin in ALLOWED_ORIGINS or re.match(ALLOW_ORIGIN_REGEX, origin)
    logger.info(f"   Origin Allowed: {is_allowed}")
    
    if not is_allowed:
        logger.warning(f"⚠️ CORS Origin 차단: {origin}")
        return Response(
            status_code=403,
            content="CORS Origin not allowed"
        )
    
    logger.info(f"✅ CORS Origin 허용: {origin}")
    
    return Response(
        status_code=200,
        headers={
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With'
        }
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
    # auth 서비스는 프록시로 처리
    if service == ServiceType.AUTH:
        logger.info(f"🔐 AUTH 프록시 요청 시작: /auth/{path}")
        logger.info(f"📥 요청 헤더: {dict(request.headers)}")
        
        # 요청 바디 읽기
        body: bytes = await request.body()
        logger.info(f"📦 요청 바디 크기: {len(body)} bytes")
        
        # auth-service로 요청 전달
        # 환경변수에서 AUTH_SERVICE_URL 가져오기
        AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8081")
        # 끝 슬래시 제거
        AUTH_SERVICE_URL = AUTH_SERVICE_URL.rstrip('/')
        auth_url = f"{AUTH_SERVICE_URL}/auth/{path}"
        logger.info(f"🌐 Auth Service URL: {auth_url}")
        
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"🔄 Auth Service로 요청 전송 중...")
                response = await client.request(
                    method="POST",
                    url=auth_url,
                    headers=_forward_headers(request),
                    content=body,
                    timeout=30.0
                )
                
                logger.info(f"✅ Auth Service 응답: {response.status_code}")
                logger.info(f"📤 응답 헤더: {dict(response.headers)}")
                
                # 응답 헤더 준비 (Set-Cookie 포함)
                response_headers = dict(response.headers)
                
                # CORS 헤더 추가 (Gateway에서 처리)
                origin = request.headers.get("origin")
                if origin:
                    # 정확한 origin 매칭
                    if origin in ALLOWED_ORIGINS or re.match(ALLOW_ORIGIN_REGEX, origin):
                        response_headers["Access-Control-Allow-Origin"] = origin
                    else:
                        response_headers["Access-Control-Allow-Origin"] = "https://www.minyoung.cloud"
                else:
                    response_headers["Access-Control-Allow-Origin"] = "https://www.minyoung.cloud"
                
                response_headers["Access-Control-Allow-Credentials"] = "true"
                response_headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                response_headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
                response_headers["Access-Control-Expose-Headers"] = "Set-Cookie"
                response_headers["Access-Control-Max-Age"] = "86400"
                
                logger.info(f"🔐 AUTH 프록시 요청 완료: {response.status_code}")
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=response_headers,
                    media_type=response.headers.get("content-type", "application/json")
                )
        except httpx.ConnectError as e:
            logger.error(f"❌ Auth Service 연결 실패: {auth_url} - {str(e)}")
            return JSONResponse(
                content={"detail": f"Auth Service 연결 실패: {str(e)}"}, 
                status_code=503
            )
        except httpx.TimeoutException as e:
            logger.error(f"⏰ Auth Service 요청 타임아웃: {auth_url} - {str(e)}")
            return JSONResponse(
                content={"detail": f"Auth Service 요청 타임아웃: {str(e)}"}, 
                status_code=504
            )
        except Exception as e:
            logger.error(f"❌ Auth Service 요청 실패: {auth_url} - {str(e)}")
            return JSONResponse(
                content={"detail": f"Auth Service 요청 실패: {str(e)}"}, 
                status_code=500
            )
    
    try:
        logger.info(f"🌈 POST 프록시 시작: 서비스={service}, 경로={path}")
        body: bytes = await request.body()
        logger.info(f"📦 요청 바디 크기: {len(body)} bytes")

        factory = ServiceDiscovery(service_type=service)

        files = None
        params = None
        data = None
        headers = _forward_headers(request)

        if service in FILE_REQUIRED_SERVICES:
            if "upload" in path and not file:
                logger.error(f"❌ 파일 업로드 필요: 서비스 {service}")
                raise HTTPException(
                    status_code=400, detail=f"서비스 {service}에는 파일 업로드가 필요합니다."
                )
            if file:
                file_content = await file.read()
                files = {"file": (file.filename, file_content, file.content_type)}
                await file.seek(0)
                logger.info(f"📁 파일 업로드: {file.filename}")
            if sheet_names:
                params = {"sheet_name": sheet_names}
                logger.info(f"📋 시트 이름: {sheet_names}")

        logger.info(f"🔄 서비스로 요청 전송 중...")
        resp = await factory.request(
            method="POST",
            path=path,
            headers=headers,
            body=body if files is None else None,
            files=files,
            params=params,
            data=data,
            cookies=request.cookies,  # ✅ 세션 쿠키 전달
        )

        logger.info(f"✅ 서비스 응답: {resp.status_code}")
        out = ResponseFactory.create_response(resp)
        # ✅ Set-Cookie 패스스루
        if "set-cookie" in resp.headers:
            out.headers["set-cookie"] = resp.headers["set-cookie"]
            logger.info(f"🍪 Set-Cookie 패스스루: {resp.headers['set-cookie']}")
        
        logger.info(f"🌈 POST 프록시 완료: {resp.status_code}")
        return out

    except HTTPException as he:
        logger.error(f"❌ HTTP 예외: {he.status_code} - {he.detail}")
        return JSONResponse(content={"detail": he.detail}, status_code=he.status_code)
    except Exception as e:
        logger.exception(f"❌ POST 프록시 처리 중 오류: {str(e)}")
        return JSONResponse(content={"detail": f"Gateway error: {str(e)}"}, status_code=500)



# ---------------------------------------------------------------------
# 라우터 등록
app.include_router(gateway_router)

# ---------------------------------------------------------------------
# 로컬 실행용
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
