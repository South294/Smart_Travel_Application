from pydantic import BaseModel, EmailStr
from typing import Optional, List
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
