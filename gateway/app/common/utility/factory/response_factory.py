from fastapi.responses import JSONResponse
from httpx import Response
from typing import Any, Dict

class ResponseFactory:
    @staticmethod
    def create_response(response: Response) -> JSONResponse:
        """HTTP 응답을 FastAPI JSONResponse로 변환"""
        try:
            content = response.json()
        except:
            content = response.text
        
        return JSONResponse(
            content=content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
