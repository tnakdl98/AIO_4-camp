import os
from dotenv import load_dotenv
from pathlib import Path
import psycopg
import uvicorn
from fastapi import APIRouter, FastAPI, Request
from psycopg.rows import dict_row
from pydantic import BaseModel, ConfigDict, Field

# 이 파일과 같은 폴더의 .env를 읽는다. 기존 환경 변수는 덮어쓰지 않는다.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = FastAPI(title="사용자 등록·조회 실습")
router = APIRouter(tags=["users"])                      # 요청을 알맞은 함수로 안내하는 안내판


class UserCreate(BaseModel):
    # 문자열의 앞뒤 공백을 제거하고, 정의되지 않은 필드가 들어오면 검증 오류를 발생시킨다.
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    # 백엔드에선 통과하지만 데이터베이스에선 죽을 수 있음(범위를 통일해주는게 좋음)
    name: str = Field(min_length=1, max_length=50)
    email: str = Field(min_length=1, max_length=100) 


def initialize_database(db_config):
    with psycopg.connect(**db_config) as conn:                      # **은 데이터를 딕셔너리 형태로 받음
        conn.execute("CREATE SCHEMA IF NOT EXISTS kdt_api01;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kdt_api01.users (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL
            );
        """)

# Request는 클라이언트의 HTTP 요청 정보를 담으며, 여기서는 앱에 저장된 DB 설정에 접근한다.
def get_connection(request: Request):
    return psycopg.connect(
        **request.app.state.db_config,
        row_factory=dict_row,                       # 조회 결과를 딕셔너리로 반환
    )


@router.post("/users", status_code=201)             # @router : 특정 URL로 요청이 들어왔을 때 실행할 함수를 연결하기 위해 사용
def create_user(user: UserCreate, request: Request):  
    with get_connection(request) as conn:
        row = conn.execute(
            """
            INSERT INTO kdt_api01.users (name, email)
            VALUES (%s, %s)
            RETURNING id, name, email;              -- 저장된 사용자의 id, name, email을 반환
            """,
            (user.name, user.email),
        ).fetchone()
    return row                                      # row_factory=dict_row 때문에 row는 딕셔너리 형태로 값을 리턴


@router.get("/users")                               # APIRouter에 경로를 먼저 등록
def list_users(request: Request):
    with get_connection(request) as conn:
        rows = conn.execute("""
            SELECT id, name, email
            FROM kdt_api01.users
            ORDER BY id;
        """).fetchall()
    return rows


app.include_router(router)                          # include_router: 라우터에 정의된 API 경로를 앱에 등록


if __name__ == "__main__":
    db_config = {
        "host": os.getenv("host"),
        "port": os.getenv("port"),
        "dbname": os.getenv("dbname"),
        "user": os.getenv("user"),
        "password": os.getenv("password"),
        "sslmode": "require",
        "connect_timeout": 10,
    }
    initialize_database(db_config)                          # Supabase DB에 연결
    app.state.db_config = db_config
    print("DB 준비 완료. http://127.0.0.1:8000/docs 에 접속하세요.")
    uvicorn.run(app, host="127.0.0.1", port=8000)


"""
1.서버 시작: python main.py를 실행하면 83번 줄의 initialize_database(db_config)가 Supabase DB에 연결합니다. 
28번 줄은 kdt_api01 스키마를 만들고, 30번 줄은 그 안에 users 테이블이 없으면 만듭니다.

2.경로 등록: 45번 줄과 59번 줄에서 /users 요청을 처리할 함수를 router에 등록하고, 70번 줄에서 그 라우터를 app에 연결합니다.

3.요청 처리: 서버 실행 후 127.0.0.1:8000/users로 요청이 오면 요청 방식에 따라 다른 함수가 실행됩니다.
- GET → list_users()가 DB에 연결해 kdt_api01.users를 조회합니다.
- POST → create_user()가 DB에 연결해 kdt_api01.users에 사용자를 저장합니다.
"""