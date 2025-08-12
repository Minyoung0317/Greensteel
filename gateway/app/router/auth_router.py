from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
import httpx
import logging
import os
from typing import Dict, Any
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Auth Service URL 설정
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8081")

def get_allowed_origins():
    """환경변수 FRONTEND_ORIGIN에서 허용할 Origin 목록을 가져옴"""
    origins_str = os.getenv("FRONTEND_ORIGIN", "")
    if origins_str:
        origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
        return origins
    else:
        # 기본값 (프로덕션 환경용) - 환경변수가 없을 때도 작동하도록
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://frontend:3000",
            "https://www.minyoung.cloud",
            "https://minyoung.cloud",
            "https://greensteel.vercel.app",
            "https://greensteel-gateway-production.up.railway.app",
            "https://greensteel-gateway-production-eeb5.up.railway.app",
            "https://greensteel-frontend.vercel.app",
            "https://greensteel-gateway.railway.app",
        ]

async def forward_request_to_auth_service(
    request: Request,
    path: str,
    method: str = "POST"
) -> Response:
    """
    Auth Service로 요청을 전달하고 쿠키를 포함한 응답을 반환
    """
    try:
        # 요청 바디 읽기
        body = await request.body()
        
        # 요청 헤더 준비 (쿠키 포함)
        headers = dict(request.headers)
        
        # Host 헤더 제거 (auth-service로 전달할 때 문제가 될 수 있음)
        if "host" in headers:
            del headers["host"]
        
        # 쿠키 헤더 명시적 설정
        if "cookie" in headers:
            logger.info(f"🍪 쿠키 전달: {headers['cookie']}")
        else:
            logger.info("🍪 전달할 쿠키 없음")
        
        # Auth Service로 요청 전달
        async with httpx.AsyncClient() as client:
            auth_url = f"{AUTH_SERVICE_URL}/auth/{path}"
            
            logger.info(f"🔄 Auth Service로 요청 전달: {method} {auth_url}")
            logger.info(f"📤 Origin: {request.headers.get('origin', 'N/A')}")
            logger.info(f"📤 전달할 헤더: {dict(headers)}")
            
            response = await client.request(
                method=method,
                url=auth_url,
                headers=headers,
                content=body,
                timeout=30.0
            )
            
            logger.info(f"📥 Auth Service 응답: {response.status_code}")
            
            # 응답 헤더 준비 (Set-Cookie 포함)
            response_headers = dict(response.headers)
            
            # Set-Cookie 헤더 로깅
            if "set-cookie" in response_headers:
                logger.info(f"🍪 Set-Cookie 응답: {response_headers['set-cookie']}")
            else:
                logger.info("🍪 Set-Cookie 응답 없음")
            
            # CORS 헤더 강화 - 환경변수 기반 Origin 설정
            origin = request.headers.get("origin")
            allowed_origins = get_allowed_origins()
            logger.info(f"[Auth Router] Origin: {origin}, Allowed: {allowed_origins}")
            
            if origin and origin in allowed_origins:
                response_headers["Access-Control-Allow-Origin"] = origin
                logger.info(f"[Auth Router] Setting CORS origin: {origin}")
            else:
                response_headers["Access-Control-Allow-Origin"] = "https://www.minyoung.cloud"
                logger.warning(f"[Auth Router] Origin {origin} not in allowed list, using default")
            
            response_headers["Access-Control-Allow-Credentials"] = "true"
            response_headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response_headers["Access-Control-Allow-Headers"] = "*"
            response_headers["Access-Control-Expose-Headers"] = "*"
            response_headers["Access-Control-Max-Age"] = "86400"
            
            # 응답 생성
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=response_headers,
                media_type=response.headers.get("content-type", "application/json")
            )
            
    except httpx.TimeoutException:
        logger.error("⏰ Auth Service 요청 타임아웃")
        raise HTTPException(status_code=504, detail="Auth Service 응답 시간 초과")
    except httpx.ConnectError:
        logger.error("🔌 Auth Service 연결 실패")
        raise HTTPException(status_code=503, detail="Auth Service 연결 실패")
    except Exception as e:
        logger.error(f"❌ Auth Service 요청 전달 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Auth Service 요청 처리 실패: {str(e)}")

@router.post("/signup")
async def auth_signup(request: Request):
    """회원가입 요청을 Auth Service로 프록시"""
    return await forward_request_to_auth_service(request, "signup", "POST")

@router.post("/login")
async def auth_login(request: Request):
    """로그인 요청을 Auth Service로 프록시"""
    return await forward_request_to_auth_service(request, "login", "POST")

@router.post("/logout")
async def auth_logout(request: Request):
    """로그아웃 요청을 Auth Service로 프록시"""
    return await forward_request_to_auth_service(request, "logout", "POST")

@router.get("/verify")
async def auth_verify(request: Request):
    """세션 검증 요청을 Auth Service로 프록시"""
    return await forward_request_to_auth_service(request, "verify", "GET")

@router.get("/{path:path}")
async def auth_proxy_get(request: Request, path: str):
    """
    GET 요청도 Auth Service로 프록시
    """
    return await forward_request_to_auth_service(request, path, "GET")

@router.put("/{path:path}")
async def auth_proxy_put(request: Request, path: str):
    """
    PUT 요청도 Auth Service로 프록시
    """
    return await forward_request_to_auth_service(request, path, "PUT")

@router.delete("/{path:path}")
async def auth_proxy_delete(request: Request, path: str):
    """
    DELETE 요청도 Auth Service로 프록시
    """
    return await forward_request_to_auth_service(request, path, "DELETE")

@router.options("/signup")
@router.options("/login")
@router.options("/logout")
@router.options("/verify")
async def auth_proxy_options(request: Request):
    """
    OPTIONS 요청 처리 (CORS preflight)
    """
    # 환경변수 기반 Origin 설정
    origin = request.headers.get("origin")
    allowed_origins = get_allowed_origins()
    if origin and origin in allowed_origins:
        allow_origin = origin
    else:
        allow_origin = "https://www.minyoung.cloud"
    
    path = request.url.path.split("/")[-1]  # 마지막 경로 부분 추출
    logger.info(f"🔄 OPTIONS 요청 처리: {path} from {origin}")
    
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": allow_origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Expose-Headers": "*",
            "Access-Control-Max-Age": "86400",
        }
    )
