from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime

class UserModel(BaseModel):
    def __init__(self):
        pass