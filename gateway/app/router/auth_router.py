from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
import httpx
import logging
from typing import Dict, Any
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Auth Service URL 설정
AUTH_SERVICE_URL = "http://auth-service:8081"

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
        
        # Auth Service로 요청 전달
        async with httpx.AsyncClient() as client:
            auth_url = f"{AUTH_SERVICE_URL}/{path}"
            
            logger.info(f"🔄 Auth Service로 요청 전달: {method} {auth_url}")
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

@router.post("/{path:path}")
async def auth_proxy(request: Request, path: str):
    """
    /api/v1/auth/* 경로의 모든 요청을 Auth Service로 프록시
    """
    return await forward_request_to_auth_service(request, path, "POST")

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
