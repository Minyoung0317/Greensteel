from fastapi import APIRouter, Cookie, HTTPException, Query, Request
from fastapi.responses import JSONResponse
import logging
import json
from datetime import datetime

# from app.domain.auth.controller.google_controller import GoogleController

auth_router = APIRouter(prefix="/auth", tags=["auth"])
# google_controller = GoogleController()

# 로깅 설정
logger = logging.getLogger("auth_service")

@auth_router.get("/google/login", summary="Google 로그인 시작")
async def google_login(
    redirect_uri: str = Query(
        default="http://localhost:3000/dashboard",
        description="로그인 후 리다이렉트할 URI (기본값: /dashboard)"
    )
):
    """
    Google OAuth 로그인을 시작합니다.
    리다이렉트 URI는 state 파라미터로 전달되어 콜백 시 다시 받게 됩니다.
    """
    return {"message": "Google 로그인 기능 준비 중"}

@auth_router.get("/google/callback", summary="Google OAuth 콜백 처리")
async def google_callback(
    code: str = Query(..., description="Google OAuth 인증 코드"),
    state: str = Query(..., description="로그인 시작 시 전달한 state 값")
):
    """
    Google OAuth 콜백을 처리합니다.
    인증 코드를 받아 처리하고 세션 토큰을 쿠키에 설정한 후 리다이렉트합니다.
    """
    return {"message": "Google 콜백 기능 준비 중"}

@auth_router.post("/logout", summary="로그아웃")
async def logout(session_token: str | None = Cookie(None)):
    """
    사용자를 로그아웃하고 인증 쿠키를 삭제합니다.
    """
    print(f"로그아웃 요청 - 받은 세션 토큰: {session_token}")
    
    # 로그아웃 응답 생성
    response = JSONResponse({
        "success": True,
        "message": "로그아웃되었습니다."
    })
    
    # 인증 쿠키 삭제
    response.delete_cookie(
        key="session_token",
        path="/",
        # domain 설정 제거 (로컬 환경)
    )
    
    print("✅ 로그아웃 완료 - 인증 쿠키 삭제됨")
    return response

@auth_router.get("/profile", summary="사용자 프로필 조회")
async def get_profile(session_token: str | None = Cookie(None)):
    """
    세션 토큰으로 사용자 프로필을 조회합니다.
    세션 토큰이 없거나 유효하지 않으면 401 에러를 반환합니다.
    """
    print(f"프로필 요청 - 받은 세션 토큰: {session_token}")
    
    if not session_token:
        raise HTTPException(status_code=401, detail="인증 쿠키가 없습니다.")
    try:
        return {"message": "프로필 조회 기능 준비 중"}
    except Exception as e:
        print(f"프로필 조회 오류: {e}")
        raise HTTPException(status_code=401, detail=str(e))

@auth_router.post("/logs/data", summary="데이터 로그 수신")
async def receive_data_log(request: Request):
    """
    Gateway에서 전달받은 데이터 로그를 처리합니다.
    """
    try:
        body = await request.body()
        if body:
            log_data = json.loads(body.decode('utf-8'))
            logger.info(f"📊 데이터 로그 수신: {log_data}")
            
            # 로그 데이터 처리 (필요시 데이터베이스에 저장)
            # 여기서는 로깅만 수행
            logger.info(f"서비스: {log_data.get('service')}")
            logger.info(f"경로: {log_data.get('path')}")
            logger.info(f"데이터 크기: {log_data.get('data_size')} bytes")
            logger.info(f"타임스탬프: {log_data.get('timestamp')}")
            logger.info(f"소스: {log_data.get('source')}")
            
            return {"status": "success", "message": "로그 수신 완료"}
        else:
            logger.warning("빈 로그 데이터 수신")
            return {"status": "warning", "message": "빈 로그 데이터"}
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {str(e)}")
        raise HTTPException(status_code=400, detail="잘못된 JSON 형식")
    except Exception as e:
        logger.error(f"로그 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="로그 처리 중 오류 발생")

@auth_router.get("/logs", summary="로그 조회")
async def get_logs():
    """
    저장된 로그를 조회합니다. (현재는 간단한 상태만 반환)
    """
    return {
        "status": "success",
        "message": "로그 조회 기능 준비됨",
        "timestamp": datetime.now().isoformat()
    }