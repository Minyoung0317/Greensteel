# gateway/app/main.py
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

# --- 프로젝트 내부 모듈 ---
from app.router.auth_router import router as auth_router
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
# CORS 설정 (환경변수 + 정규식 지원)
# FRONTEND_ORIGIN="https://www.minyoung.cloud,https://minyoung.cloud,https://greensteel.vercel.app"
# FRONTEND_ORIGIN_REGEX="^https://[a-z0-9-]+\\.vercel\\.app$"  # 모든 Vercel 프리뷰 허용(선택)
def _get_cors_config() -> tuple[list[str], str | None]:
    raw = os.getenv("FRONTEND_ORIGIN", "")
    allow_list = [o.strip() for o in raw.split(",") if o.strip()]
    
    # 기본값 추가 (환경변수가 없을 때도 작동하도록)
    if not allow_list:
        allow_list = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://www.minyoung.cloud",
            "https://minyoung.cloud",
            "https://greensteel.vercel.app",
            "https://greensteel-gateway-production.up.railway.app",
            "https://greensteel-gateway-production-eeb5.up.railway.app",
        ]
    
    regex_str = os.getenv("FRONTEND_ORIGIN_REGEX", "") or None
    logger.info(f"[CORS] allow_origins={allow_list}, allow_origin_regex={regex_str}")
    return allow_list, regex_str

def _forward_headers(request: Request) -> Dict[str, str]:
    skip = {"host", "content-length"}
    return {k: v for k, v in request.headers.items() if k.lower() not in skip}

# ⭐ 미들웨어 순서 주의:
# Starlette/FastAPI는 '마지막에 추가한' 미들웨어가 가장 바깥(먼저 실행)입니다.
# → CORS 헤더가 프리플라이트/에러에도 항상 붙도록 '마지막'에 CORS를 추가합니다.
# JWT 미들웨어 제거됨 - 웹 회원가입만 사용

_allow_list, _allow_regex = _get_cors_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_list,
    allow_origin_regex=_allow_regex,
    allow_credentials=True,  # 세션 쿠키 전달
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------------------------------------------------

# 기본 루트 (헬스)
@app.get("/")
async def root():
    return {"message": "GreenSteel Gateway API", "docs": "/docs", "version": "0.1.0"}

# 게이트웨이 라우터
gateway_router = APIRouter(prefix="/api/v1", tags=["Gateway API"])
gateway_router.include_router(auth_router)
gateway_router.include_router(user_router)
gateway_router.include_router(chatbot_router)

# ---------------------------------------------------------------------
# /api/v1/auth 전용 프록시 (세션 쿠키/Set-Cookie 패스스루)
@gateway_router.post("/auth/{path:path}", summary="Auth 전용 프록시 (POST)")
async def auth_proxy(path: str, request: Request):
    factory = ServiceDiscovery(service_type=ServiceType.AUTH)
    body = await request.body()

    logger.info(f"🔐 AUTH 프록시 요청: /auth/{path} (len={len(body) if body else 0})")

    resp = await factory.request(
        method="POST",
        path=path,
        headers=_forward_headers(request),
        body=body,
        cookies=request.cookies,  # ✅ 세션 쿠키 전달
    )

    out = ResponseFactory.create_response(resp)
    # ✅ auth-service가 내려준 Set-Cookie 헤더를 그대로 전달
    if "set-cookie" in resp.headers:
        out.headers["set-cookie"] = resp.headers["set-cookie"]
    
    # CORS 헤더 추가
    origin = request.headers.get("origin")
    if origin:
        out.headers["Access-Control-Allow-Origin"] = origin
        out.headers["Access-Control-Allow-Credentials"] = "true"
        out.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        out.headers["Access-Control-Allow-Headers"] = "*"
        out.headers["Access-Control-Expose-Headers"] = "*"
    
    return out

@gateway_router.options("/auth/{path:path}", summary="Auth 전용 프록시 (OPTIONS)")
async def auth_proxy_options(path: str, request: Request):
    """OPTIONS 요청 처리 (CORS preflight)"""
    origin = request.headers.get("origin")
    if origin:
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Expose-Headers": "*",
                "Access-Control-Max-Age": "86400",
            }
        )
    return Response(status_code=200)

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
