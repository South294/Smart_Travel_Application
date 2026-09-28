from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import date

class UserSettings(BaseModel):
    email_notifications: bool = True
    sms_notifications: bool = False
    ai_personalization: bool = True
    language: str = "vi"

class UserProfile(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    role: str = "user"
    preferences: List[str] = []
    custom_preferences: List[str] = []
    saved_vouchers: List[str] = []
    settings: UserSettings = UserSettings()
    avatar_url: str = ""
    cccd: Optional[Dict[str, Any]] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    avatar_url: Optional[str] = None

class UserPreferencesUpdate(BaseModel):
    preferences: List[str]
    custom_preferences: List[str]

class UserSettingsUpdate(BaseModel):
    settings: UserSettings

class UserCCCDVerificationRequest(BaseModel):
    cccd_number: str = Field(min_length=12, max_length=12)
    full_name: str = Field(min_length=2, max_length=100)
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    id_front_url: str = Field(min_length=1)
    id_back_url: str = Field(min_length=1)
    portrait_url: str = Field(min_length=1)

class UserCCCDVerificationResponse(BaseModel):
    message: str
    cccd_status: str
    verified_at: str
