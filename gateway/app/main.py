from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import os
import sys
import json
import logging
import datetime as dt
import re

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

# 로깅
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("gateway_api")

# 파일이 필요한 서비스 (필요 시 채워서 사용)
FILE_REQUIRED_SERVICES: set[ServiceType] = set()

# ---------------------------------------------------------------------
# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Gateway API 서비스 시작")
    logger.info(
        f"환경: {'Railway' if os.getenv('RAILWAY_ENVIRONMENT') == 'true' else 'Local/Docker'}"
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

def _forward_headers(request: Request) -> Dict[str, str]:
    skip = {"host", "content-length"}
    return {k: v for k, v in request.headers.items() if k.lower() not in skip}

# ---------------------------------------------------------------------
# 기본 루트 (헬스)
@app.get("/")
async def root():
    return {"message": "GreenSteel Gateway API", "docs": "/docs", "version": "0.1.0"}

# Auth 라우터 제거 - auth-service에서 직접 처리

# 게이트웨이 라우터 (다른 서비스용)
gateway_router = APIRouter(prefix="/api/v1", tags=["Gateway API"])
gateway_router.include_router(user_router)
gateway_router.include_router(chatbot_router)

# ---------------------------------------------------------------------
# OPTIONS 요청 핸들러 (CORS preflight)
@gateway_router.options("/{service}/{path:path}", summary="OPTIONS 프록시")
async def proxy_options(
    service: ServiceType,
    path: str,
    request: Request,
):
    logger.info(f"🔄 OPTIONS 프록시: 서비스={service}, 경로={path}")
    
    # CORS 헤더 설정
    origin = request.headers.get("origin")
    headers = {}
    
    if origin:
        if origin in ALLOWED_ORIGINS or re.match(ALLOW_ORIGIN_REGEX, origin):
            headers["Access-Control-Allow-Origin"] = origin
        else:
            headers["Access-Control-Allow-Origin"] = "https://www.minyoung.cloud"
    else:
        headers["Access-Control-Allow-Origin"] = "https://www.minyoung.cloud"
    
    headers["Access-Control-Allow-Credentials"] = "true"
    headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    headers["Access-Control-Expose-Headers"] = "Set-Cookie"
    headers["Access-Control-Max-Age"] = "86400"
    
    return Response(status_code=200, headers=headers)

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
        logger.info(f"🔐 AUTH 프록시 요청: /{service}/{path}")
        # 요청 바디 읽기
        body: bytes = await request.body()
        # auth-service로 요청 전달
        auth_url = f"http://auth-service:8081/auth/{path}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method="POST",
                url=auth_url,
                headers=_forward_headers(request),
                content=body,
                timeout=30.0
            )
            
            # 응답 헤더 준비 (Set-Cookie 포함)
            response_headers = dict(response.headers)
            
            # CORS 헤더 추가
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
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=response_headers,
                media_type=response.headers.get("content-type", "application/json")
            )
    
    try:
        logger.info(f"🌈 POST 프록시: 서비스={service}, 경로={path}")
        body: bytes = await request.body()

        # (선택) auth-service로 데이터 사용 로그 전송
        if body:
            await log_to_auth_service(service, path, body)

        factory = ServiceDiscovery(service_type=service)

        files = None
        params = None
        data = None
        headers = _forward_headers(request)

        if service in FILE_REQUIRED_SERVICES:
            if "upload" in path and not file:
                raise HTTPException(
                    status_code=400, detail=f"서비스 {service}에는 파일 업로드가 필요합니다."
                )
            if file:
                file_content = await file.read()
                files = {"file": (file.filename, file_content, file.content_type)}
                await file.seek(0)
            if sheet_names:
                params = {"sheet_name": sheet_names}

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

        out = ResponseFactory.create_response(resp)
        # ✅ Set-Cookie 패스스루
        if "set-cookie" in resp.headers:
            out.headers["set-cookie"] = resp.headers["set-cookie"]
        return out

    except HTTPException as he:
        return JSONResponse(content={"detail": he.detail}, status_code=he.status_code)
    except Exception as e:
        logger.exception("POST 프록시 처리 중 오류")
        return JSONResponse(content={"detail": f"Gateway error: {str(e)}"}, status_code=500)

# ---------------------------------------------------------------------
# 유틸: auth-service로 데이터 로그 전달 (옵션)
async def log_to_auth_service(service: ServiceType, path: str, body: bytes):
    try:
        auth_factory = ServiceDiscovery(service_type=ServiceType.AUTH)
        log_data = {
            "service": service.value if hasattr(service, "value") else str(service),
            "path": path,
            "data_size": len(body),
            "timestamp": dt.datetime.utcnow().isoformat() + "Z",
            "source": "gateway",
        }
        await auth_factory.request(
            method="POST",
            path="logs/data",
            headers={"Content-Type": "application/json"},
            body=json.dumps(log_data).encode("utf-8"),
        )
        logger.info(f"📊 데이터 로그 전송 완료: {service}/{path}")
    except Exception as e:
        logger.warning(f"auth-service 로그 전송 실패: {e}")

# ---------------------------------------------------------------------
# 라우터 등록
app.include_router(gateway_router)

# ---------------------------------------------------------------------
# 로컬 실행용
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
