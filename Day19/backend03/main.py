"""3차시: 문의 컨텍스트와 성공한 상담을 서버의 Redis에서 관리한다."""
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


@app.post("/tickets", status_code=201)
def new_ticket(body: TicketInput):
    return create_ticket(body, "local")


@app.get("/tickets/{ticket_id}")
def read_ticket(ticket_id: UUID):
    return get_ticket(ticket_id, "local")


@app.post("/tickets/{ticket_id}/turns")
def chat(ticket_id: UUID, body: TurnInput):
    return run_turn(ticket_id, body, "local")
