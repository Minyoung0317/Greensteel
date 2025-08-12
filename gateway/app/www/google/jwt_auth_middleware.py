from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging
from typing import Optional
import jwt
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AuthMiddleware:
    def __init__(self, app):
        self.app = app
        self.secret_key = "your-secret-key"  # 실제로는 환경변수에서 가져와야 함
        self.algorithm = "HS256"

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # 헬스체크나 인증 관련 엔드포인트는 인증 제외
            if self._is_exempt_path(request.url.path):
                await self.app(scope, receive, send)
                return
            
            # JWT 토큰 검증
            user_id = await self._verify_token(request)
            if user_id:
                # 사용자 ID를 헤더에 추가
                scope["headers"] = [(b"x-user-id", str(user_id).encode())]
            
        await self.app(scope, receive, send)

    def _is_exempt_path(self, path: str) -> bool:
        """인증이 제외되는 경로들"""
        exempt_paths = [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/verify"
        ]
        return any(path.startswith(exempt_path) for exempt_path in exempt_paths)

    async def _verify_token(self, request: Request) -> Optional[str]:
        """JWT 토큰 검증"""
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                logger.warning("Authorization header missing or invalid")
                return None
            
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("user_id")
            
            if not user_id:
                logger.warning("User ID not found in token")
                return None
                
            logger.info(f"Token verified for user: {user_id}")
            return user_id
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return None 