"""08장: 사용자·작업 관리 API의 요청/응답 모델 정의."""
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class MemberCreate(StrictModel):
    name: str = Field(min_length=2, max_length=40)
    email: EmailStr
    role: Literal['student', 'instructor'] = 'student'


class MemberOut(MemberCreate):
    id: int


class TaskCreate(StrictModel):
    owner_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=80)
    done: bool = Field(default=False, strict=True)
    priority: Literal['low', 'normal', 'high'] = 'normal'
    due_date: date | None = None
    internal_note: str | None = Field(default=None, max_length=200)

    @field_validator('title')
    @classmethod
    def normalize_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError('제목은 공백만으로 구성할 수 없습니다')
        return cleaned


class TaskPatch(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=80)
    done: bool | None = Field(default=None, strict=True)
    priority: Literal['low', 'normal', 'high'] | None = None
    due_date: date | None = None
    internal_note: str | None = Field(default=None, max_length=200)

    @field_validator('title')
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError('제목을 공백으로 변경할 수 없습니다')
        return value.strip() if value is not None else None


class TaskOut(StrictModel):
    # response_model이 내부 메모를 안전하게 제외하도록 여분 필드는 무시한다.
    model_config = ConfigDict(extra='ignore', str_strip_whitespace=True)
    id: int
    owner_id: int
    title: str
    done: bool
    priority: Literal['low', 'normal', 'high']
    due_date: date | None = None
    # internal_note는 응답에서 노출하지 않는다.