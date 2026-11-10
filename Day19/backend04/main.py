"""3차시: 문의 컨텍스트와 성공한 상담을 서버의 Redis에서 관리한다."""

import hashlib
import time
from typing import Annotated
import httpx
from fastapi import Depends, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import SecretStr
from supabase import AuthApiError, AuthRetryableError, create_client
from supabase.client import ClientOptions

import json
import os
from typing import Literal
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import APIError, OpenAI
from pydantic import BaseModel, ConfigDict, Field
from redis import Redis, RedisError, WatchError


load_dotenv(".env", override=False, interpolate=False)
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()

REDIS_URL = os.getenv("REDIS_URL", "").strip()
for name, value in {"GROQ_API_KEY": os.getenv("GROQ_API_KEY", ""), "GROQ_MODEL": MODEL,
                    "REDIS_URL": REDIS_URL}.items():
    if not value.strip():
        raise RuntimeError(f".env의 {name} 값을 입력하세요.")
if not REDIS_URL.startswith(("redis://", "rediss://")):
    raise RuntimeError("REDIS_URL 주소를 확인하세요.")
TTL = 1800
app = FastAPI(title="IT 문의 컨텍스트 API")
INSTRUCTIONS = '당신은 사내 IT 헬프데스크의 상담 보조입니다. 한국어로 간결하게 답합니다.\n반드시 [증상 요약], [확인할 정보], [다음 조치] 세 제목을 사용합니다.\n이미 알려준 환경과 수행한 조치를 기억하고 같은 확인을 반복하지 않습니다.\n정보가 부족하면 확인 질문을 먼저 합니다. 원인을 확정하거나 VPN 주소를 지어내지 않습니다.\n비밀번호, 인증 코드, API 키를 요청하지 않습니다. 보안 기능 해제나 관리자 명령 실행을 권하지 않습니다.\n실습 운영 안내: VPN 담당 창구는 사내 IT 문의 채널이며 실제 접속 주소는 담당자가 안내합니다.\n제안한 작업을 실제로 실행했다고 주장하지 않습니다.'

def ask_groq(inputs, instructions=INSTRUCTIONS):
    # 전달한 대화 목록을 그대로 Responses API의 input에 넣는다.
    with OpenAI(api_key=os.environ["GROQ_API_KEY"],
                base_url="https://api.groq.com/openai/v1",
                timeout=60.0, max_retries=0) as client:
        response = client.responses.create(
            model=MODEL, instructions=instructions, input=inputs,
            reasoning={"effort": "low"}, max_output_tokens=1600,
        )
    if response.status != "completed" or not response.output_text.strip():
        raise ValueError("완료된 답변을 받지 못했습니다. 같은 질문을 다시 시도하세요.")
    return response


class TicketInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    subject: str = Field(min_length=1, max_length=100)
    service: Literal["VPN", "화상회의"]
    environment: str = Field(min_length=1, max_length=100)
    impact: Literal["본인만", "팀 전체"]


class TurnInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    request_id: UUID
    question: str = Field(min_length=1, max_length=1000)


@app.exception_handler(RedisError)
async def redis_error(_request, _exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=503, content={"detail": "Redis 연결을 확인하세요."})


def connect_redis():
    return Redis.from_url(REDIS_URL, decode_responses=True,
                          socket_connect_timeout=3, socket_timeout=3)


def ticket_key(ticket_id):
    return "kdt:groq:helpdesk:ticket:" + str(ticket_id)


def index_key(owner_id):
    return "kdt:groq:helpdesk:index:" + owner_id


def case_message(case):
    return {"role": "user", "content": (
        f"[문의 카드] 제목: {case['subject']} / 서비스: {case['service']} / "
        f"환경: {case['environment']} / 영향: {case['impact']}"
    )}


def build_input(ticket, question):
    history = []
    for turn in ticket["turns"]:
        history.extend([{"role": "user", "content": turn["question"]},
                        {"role": "assistant", "content": turn["answer"]}])
    return [case_message(ticket["case"])] + history + [{"role": "user", "content": question}]


def checked_ticket(raw, owner_id):
    if raw is None:
        raise HTTPException(404, "이 계정에서 찾을 수 없는 문의입니다.")
    ticket = json.loads(raw)
    if ticket["owner_id"] != owner_id:
        raise HTTPException(404, "이 계정에서 찾을 수 없는 문의입니다.")
    return ticket


def create_ticket(body, owner_id):
    ticket_id = str(uuid4())
    ticket = {"id": ticket_id, "owner_id": owner_id, "case": body.model_dump(), "turns": []}
    with connect_redis() as client, client.pipeline() as pipe:
        pipe.set(ticket_key(ticket_id), json.dumps(ticket, ensure_ascii=False), ex=TTL)
        pipe.sadd(index_key(owner_id), ticket_id)
        pipe.expire(index_key(owner_id), TTL)
        pipe.execute()
    return {"id": ticket_id, "case": ticket["case"], "turn_count": 0}


def get_ticket(ticket_id, owner_id):
    with connect_redis() as client:
        ticket = checked_ticket(client.get(ticket_key(ticket_id)), owner_id)
    return {"id": ticket["id"], "case": ticket["case"], "turns": ticket["turns"],
            "turn_count": len(ticket["turns"])}


def run_turn(ticket_id, body, owner_id):
    with connect_redis() as client, client.pipeline() as pipe:
        try:
            key = ticket_key(ticket_id)
            pipe.watch(key)
            ticket = checked_ticket(pipe.get(key), owner_id)
            for turn in ticket["turns"]:
                if turn["request_id"] == str(body.request_id):
                    if turn["question"] != body.question:
                        raise HTTPException(409, "같은 요청 번호의 질문이 다릅니다.")
                    return {**turn, "ticket_id": str(ticket_id), "turn_count": len(ticket["turns"]),
                            "replayed": True}
            if len(ticket["turns"]) >= 12:
                raise HTTPException(409, "한 문의는 최대 12턴입니다. 새 문의를 만드세요.")
            inputs = build_input(ticket, body.question)
            try:
                response = ask_groq(inputs)
            except (APIError, ValueError):
                raise HTTPException(502, "Groq 호출을 완료하지 못했습니다. 키·권한·호출 한도를 확인하세요.") from None
            turn = {"request_id": str(body.request_id), "question": body.question,
                    "answer": response.output_text, "response_id": response.id,
                    "context_message_count": len(inputs) - 2, "input_count": len(inputs)}
            ticket["turns"].append(turn)
            # 모델 호출 성공 뒤에만 대화 기록을 한 번에 바꾼다.
            pipe.multi()
            pipe.set(key, json.dumps(ticket, ensure_ascii=False), ex=TTL)
            pipe.expire(index_key(owner_id), TTL)
            pipe.execute()
        except WatchError:
            raise HTTPException(409, "다른 요청이 문의를 변경했습니다. 기록을 다시 확인하세요.") from None
    return {**turn, "ticket_id": str(ticket_id), "turn_count": len(ticket["turns"]), "replayed": False}



SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()
TTL_TEXT = os.getenv("SESSION_TTL_SECONDS", "1800").strip()
if not SUPABASE_URL.startswith("https://") or not SUPABASE_KEY:
    raise RuntimeError("Supabase Auth 설정을 확인하세요.")
try:
    SESSION_TTL_SECONDS = int(TTL_TEXT)
except ValueError:
    raise RuntimeError("SESSION_TTL_SECONDS는 양의 정수입니다.") from None
if SESSION_TTL_SECONDS <= 0:
    raise RuntimeError("SESSION_TTL_SECONDS는 양의 정수입니다.")
bearer = HTTPBearer(auto_error=False)

class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=1, max_length=254)
    # 비밀번호는 strip하지 않고, 검증 오류와 repr에 원문이 나오지 않도록 한다.
    password: SecretStr = Field(min_length=1, max_length=1024)

@app.exception_handler(RequestValidationError)
async def validation_error(_request, exc):
    # 비밀번호 등 원본 input 값을 응답에 포함하지 않는다.
    errors = [{"loc": e["loc"], "type": e["type"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": errors})

def make_client(http_client):
    # 요청마다 새 SDK 객체를 쓴다. 한 사용자의 인증 상태를 전역으로 공유하지 않는다.
    return create_client(SUPABASE_URL, SUPABASE_KEY, options=ClientOptions(
        persist_session=False,  # SDK 저장소 기록을 끈다. 토큰 발급 자체를 끄는 옵션이 아니다.
        auto_refresh_token=False,  # 백그라운드 자동 갱신을 끄고 만료 시 재로그인한다.
        httpx_client=http_client,  # 호출자의 timeout을 재사용한다. 호출자의 with에서 닫는다.
    ))

def raise_auth_error(exc):
    # 자격증명 오류와 인증 서비스 장애를 구분한다. 원문은 응답에 넣지 않는다.
    if exc.code in ("invalid_credentials", "bad_jwt", "user_not_found", "user_banned",
                    "session_not_found", "jwt_expired"):
        raise HTTPException(401, "로그인 정보 또는 토큰을 확인하세요.") from None
    if exc.code == "email_not_confirmed":
        raise HTTPException(403, "이메일 확인을 완료하세요.") from None
    if exc.status == 429:
        raise HTTPException(429, "인증 요청이 많습니다. 잠시 후 다시 시도하세요.") from None
    raise HTTPException(503, "인증 서비스 상태와 프로젝트 설정을 확인하세요.") from None

def session_key(token):
    # 토큰 원문을 Redis 키 이름으로 노출하지 않는다. 해시는 JWT 검증을 대신하지 않는다.
    return "kdt:user-chat:session:" + hashlib.sha256(token.encode()).hexdigest()

def read_token(credentials):
    if credentials is None:
        raise HTTPException(401, "로그인이 필요합니다.")
    return credentials.credentials

def require_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    token = read_token(credentials)
    with connect_redis() as client:
        registered_id = client.get(session_key(token))
    if registered_id is None:
        raise HTTPException(401, "로그인 세션이 없거나 만료되었습니다.")
    try:
        # 단순 디코딩 결과를 믿지 않고 Auth 서버에 토큰을 보내 사용자 정보를 검증한다.
        with httpx.Client(timeout=10.0) as http_client:
            result = make_client(http_client).auth.get_user(token)
    except AuthApiError as exc:
        raise_auth_error(exc)
    except (AuthRetryableError, httpx.HTTPError):
        raise HTTPException(503, "인증 서비스와 통신할 수 없습니다.") from None
    if result is None or result.user is None or str(result.user.id) != registered_id:
        raise HTTPException(401, "사용자를 확인할 수 없습니다.")
    # user.id는 요청 본문의 owner_id가 아니라 검증된 Auth 결과다.
    return {"id": registered_id, "email": result.user.email}

@app.post("/auth/login")
def login(body: LoginInput, response: Response):
    try:
        with httpx.Client(timeout=10.0) as http_client:
            result = make_client(http_client).auth.sign_in_with_password({
                "email": body.email.strip(), "password": body.password.get_secret_value(),
            })
    except AuthApiError as exc:
        raise_auth_error(exc)
    except (AuthRetryableError, httpx.HTTPError):
        raise HTTPException(503, "인증 서비스와 통신할 수 없습니다.") from None
    if result.session is None or result.user is None or result.session.expires_at is None:
        raise HTTPException(502, "인증 응답을 확인할 수 없습니다.")
    # Redis 세션이 원래 JWT보다 오래 살아남지 않도록 더 짧은 수명을 사용한다.
    ttl = min(SESSION_TTL_SECONDS, int(result.session.expires_at - time.time()))
    if ttl <= 0:
        raise HTTPException(401, "로그인 세션이 만료되었습니다. 다시 로그인하세요.")
    token = result.session.access_token
    with connect_redis() as client:
        client.set(session_key(token), str(result.user.id), ex=ttl)  # EX로 초 단위 고정 수명 지정.
    response.headers["Cache-Control"] = "no-store"
    # refresh_token을 UI에 전달하지 않는다. 이번 단원은 재로그인 정책이다.
    return {"access_token": token, "token_type": "bearer", "expires_in": ttl,
            "user_id": str(result.user.id), "email": result.user.email}

@app.get("/me")
def me(user: Annotated[dict, Depends(require_user)],
       credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    with connect_redis() as client:
        ttl = client.ttl(session_key(read_token(credentials)))
    if ttl == -2:
        raise HTTPException(401, "로그인 세션이 만료되었습니다.")
    if ttl == -1:
        raise HTTPException(503, "세션 만료 설정을 확인하세요.")
    return {**user, "ttl": ttl}  # 조회 시점의 남은 초. 조회는 수명을 연장하지 않는다.

@app.post("/auth/logout")
def logout(user: Annotated[dict, Depends(require_user)],
           credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    # 이 앱의 허용 목록만 제거한다. Supabase의 다른 앱/기기 세션 전체를 종료하지 않는다.
    with connect_redis() as client:
        client.delete(session_key(read_token(credentials)))
    return {"ended": True, "user_id": user["id"]}


@app.post("/tickets", status_code=201)
def new_ticket(body: TicketInput, user: Annotated[dict, Depends(require_user)]):
    return create_ticket(body, user["id"])


@app.get("/tickets")
def list_tickets(user: Annotated[dict, Depends(require_user)]):
    with connect_redis() as client:
        ids = sorted(client.smembers(index_key(user["id"])))
        result = []
        for ticket_id in ids:
            raw = client.get(ticket_key(ticket_id))
            if raw:
                ticket = checked_ticket(raw, user["id"])
                result.append({"id": ticket_id, "subject": ticket["case"]["subject"],
                               "turn_count": len(ticket["turns"])})
    return result


@app.get("/tickets/{ticket_id}")
def read_ticket(ticket_id: UUID, user: Annotated[dict, Depends(require_user)]):
    return get_ticket(ticket_id, user["id"])


@app.post("/tickets/{ticket_id}/turns")
def chat(ticket_id: UUID, body: TurnInput, user: Annotated[dict, Depends(require_user)]):
    return run_turn(ticket_id, body, user["id"])
