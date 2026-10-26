"""08장 프로젝트 시작 템플릿 - 메모리 저장 구조와 API 과제만 먼저 제공합니다."""
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(title='Final Project - Student Starter')


class MemberCreate(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr


class MemberOut(MemberCreate):
    id: int


# TODO 1: TaskCreate, TaskPatch, TaskOut 모델을 작성하세요.
# TODO 2: Pydantic Field 및 Validator로 입력을 검증하세요.
# TODO 3: dict 저장소에 ID를 부여하고 등록/조회 API를 구현하세요.
# TODO 4: PATCH에서는 exclude_unset=True를 사용하세요.
# TODO 5: 존재하지 않는 회원/작업에 404를 반환하세요.

members: dict[int, dict] = {}


@app.post('/members', response_model=MemberOut, status_code=status.HTTP_201_CREATED)
def create_member(payload: MemberCreate):
    raise HTTPException(status_code=501, detail='TODO: 회원 등록을 구현하세요')


@app.get('/members', response_model=list[MemberOut])
def list_members():
    return list(members.values())