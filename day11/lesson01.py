import os
from dotenv import load_dotenv
from pathlib import Path
import psycopg
import uvicorn
from fastapi import APIRouter, FastAPI, Request
from psycopg.rows import dict_row
from pydantic import BaseModel, ConfigDict, Field

# 이 파일과 같은 폴더의 .env를 읽는다. 기존 환경 변수는 덮어쓰지 않는다.
load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(title="사용자 등록·조회 실습")
router = APIRouter(tags=["users"])


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=1, max_length=50)
    email: str = Field(min_length=1, max_length=100)


def initialize_database(db_config):
    with psycopg.connect(**db_config) as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS kdt_api01;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kdt_api01.users (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL
            );
        """)


def get_connection(request: Request):
    return psycopg.connect(
        **request.app.state.db_config,
        row_factory=dict_row,
    )


@router.post("/users", status_code=201)
def create_user(user: UserCreate, request: Request):
    with get_connection(request) as conn:
        row = conn.execute(
            """
            INSERT INTO kdt_api01.users (name, email)
            VALUES (%s, %s)
            RETURNING id, name, email;
            """,
            (user.name, user.email),
        ).fetchone()
    return row


@router.get("/users")
def list_users(request: Request):
    with get_connection(request) as conn:
        rows = conn.execute("""
            SELECT id, name, email
            FROM kdt_api01.users
            ORDER BY id;
        """).fetchall()
    return rows


app.include_router(router)


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
    if not all(db_config[key] for key in ("host", "user", "password")):
        raise RuntimeError("Day12/.env에 SUPABASE_DB_HOST, SUPABASE_DB_USER, SUPABASE_DB_PASSWORD를 설정하세요.")
    initialize_database(db_config)
    app.state.db_config = db_config
    print("DB 준비 완료. http://127.0.0.1:8000/docs 에 접속하세요.")
    uvicorn.run(app, host="127.0.0.1", port=8000)
