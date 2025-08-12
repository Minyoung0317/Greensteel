from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

class ChatbotRequest(BaseModel):
    message: str

class ChatbotResponse(BaseModel):
    status: str
    message: str
    response: str
    timestamp: str

@router.post("/process", response_model=ChatbotResponse)
async def process_message(request: ChatbotRequest):
    """
    사용자 메시지를 처리하고 AI 응답을 반환
    """
    try:
        logger.info(f"=== 채팅봇 메시지 처리 ===")
        logger.info(f"받은 메시지: {request.message}")
        
        # 현재는 간단한 응답을 반환
        # 실제로는 chatbot-service로 전달해야 함
        ai_response = f"안녕하세요! '{request.message}'에 대한 응답입니다. 현재 개발 중인 기능입니다."
        
        response_data = ChatbotResponse(
            status="success",
            message="메시지가 성공적으로 처리되었습니다.",
            response=ai_response,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"AI 응답: {ai_response}")
        logger.info(f"응답 데이터: {json.dumps(response_data.dict(), indent=2, ensure_ascii=False)}")
        
        return response_data
        
    except Exception as e:
        logger.error(f"채팅봇 처리 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메시지 처리 중 오류가 발생했습니다: {str(e)}")


