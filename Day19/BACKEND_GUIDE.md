# 환경과 백엔드 연결

## 실행 구성과 차이

| 차시 | 실행 폴더 | 필요한 프로세스 | 기록의 주인 |
| --- | --- | --- | --- |
| 1 | lesson01 | Python CMD → Groq | 이번 문의 한 건 |
| 2 | lesson02 | Streamlit → Groq | 같은 브라우저 연결 |
| 3 | lesson03 + backend03 | Streamlit → FastAPI → Groq, Redis | 서버의 문의 ID |
| 4 | lesson04 + backend04 | 위 구성 + Supabase Auth | 검증된 계정의 문의 ID |

backend03과 backend04는 같은 8000 포트를 사용하므로 하나만 실행합니다. 4차시로 넘어갈 때 backend03을 Ctrl+C로 종료하고 backend04를 실행합니다. 모델은 모든 차시에서 Groq Responses API와 openai/gpt-oss-20b입니다. 로컬 모델 서버와 이전 LLM_BASE_URL 설정은 사용하지 않습니다.

3차시 문의는 owner_id=local로 생성됩니다. 4차시는 실제 인증 ID를 사용하므로 3차시의 ID를 그대로 열면 404입니다. A 계정으로 새 문의를 만듭니다. 4차시에서 만든 문의는 같은 계정 재로그인 후 수명 안에서 복원할 수 있습니다. 예전 kdt_user_chat DB 테이블은 변경하지 않습니다.

## Python 환경

Windows CMD에서 수업용 가상환경을 준비합니다. 이미 정상 환경이 있으면 재사용합니다.

```bat
cd /d C:\AI4\Groq_MultiTurn_Morning
python -m venv .venv
.venv\Scripts\activate
```

이후 같은 가상환경의 CMD에서 각 폴더 requirements를 설치합니다. 다른 CMD를 열었다면 같은 .venv의 activate를 실행합니다. 종료는 각 서버 CMD의 Ctrl+C이며 Redis는 별도 프로세스입니다.

## Groq 키

https://console.groq.com/keys 에서 키를 준비하고 해당 실행 폴더의 .env에 입력합니다. 실제 키를 교안·코드·채팅으로 공유하지 않습니다.

```dotenv
GROQ_API_KEY=REPLACE_WITH_YOUR_GROQ_KEY
GROQ_MODEL=openai/gpt-oss-20b
```

1~2차시는 해당 lesson 폴더에 이 설정을 둡니다. 3~4차시는 backend 폴더에만 둡니다. UI의 API_BASE_URL은 Groq 주소가 아니라 본인 FastAPI 주소 http://127.0.0.1:8000 입니다.

OpenAI SDK를 사용하지만 모델 호출 대상은 Groq입니다. Responses의 input과 output_text를 사용합니다. Groq가 현재 지원하지 않는 previous_response_id와 store는 넘기지 않습니다.

## Redis 준비

기존 수업 컨테이너가 있으면 시작합니다.

```bat
docker start kdt-redis
docker exec kdt-redis redis-cli PING
```

예상 결과는 PONG입니다. 처음 설치하는 경우에만 컨테이너를 만듭니다. 아래 설정은 임시 데이터를 영구 보관하지 않습니다.

```bat
docker run -d --name kdt-redis -p 127.0.0.1:6379:6379 redis:7.4 redis-server --save "" --appendonly no
```

## 3차시 백엔드

별도 Windows CMD에서 실행합니다. .env가 이미 있으면 copy를 생략합니다. 메모장에서 실제 Groq 키를 입력하고 저장한 뒤 서버를 시작합니다.

```bat
cd /d C:\AI4\Groq_MultiTurn_Morning\backend03
python -m pip install -r requirements.txt
copy .env.example .env
notepad .env
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

.env에는 Groq 두 값과 `REDIS_URL=redis://127.0.0.1:6379/0`이 필요합니다. http://127.0.0.1:8000/docs 에서 POST /tickets, GET /tickets/{ticket_id}, POST /tickets/{ticket_id}/turns가 보여야 합니다. 로그인 없는 단일 사용자 PC 테스트이며 인터넷에 공개하지 않습니다.

## 4차시 백엔드

Supabase 프로젝트의 정상 로그인 가능한 A·B 계정을 준비합니다. 확인 이메일이 필요한 계정은 먼저 확인을 마칩니다. 가입 UI는 이번 코드에 없으며 기존 인증 실습 계정을 사용합니다.

backend03을 종료한 뒤 아래 순서로 실행합니다.

```bat
cd /d C:\AI4\Groq_MultiTurn_Morning\backend04
python -m pip install -r requirements.txt
copy .env.example .env
notepad .env
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Groq·Redis 값에 아래 인증 설정을 추가합니다. 프로젝트 URL과 publishable key는 Supabase 프로젝트 API Keys 화면에서 확인합니다. 실제 비밀번호는 로그인 폼에서만 입력합니다.

```dotenv
SUPABASE_URL=https://PROJECT_REF.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_REPLACE_ME
SESSION_TTL_SECONDS=1800
```

4차시 서버는 기존 Auth 실습의 sign_in_with_password·get_user와 Redis 앱 로그인 등록을 재사용합니다. 새로 추가한 것은 문의의 owner_id 검사, 내 문의 목록, /tickets 보호입니다. SDK 옵션 전체를 새로 외우지 않고 토큰 추출·인증·소유권을 구분합니다.

로그인 수명은 최대 1800초이며 실제 Supabase 토큰이 더 일찍 만료되면 그 시점을 따릅니다. 문의 기록도 마지막 성공 저장 후 1800초 동안 남습니다. 조회만으로 연장되지 않습니다. Redis 데이터가 사라지면 문의도 사라지므로 이번 저장을 영구 저장으로 취급하지 않습니다.

## 화면 실행

3차시 예시입니다. 4차시는 폴더를 lesson04로 바꿉니다.

```bat
cd /d C:\AI4\Groq_MultiTurn_Morning\lesson03
python -m pip install -r requirements.txt
copy .env.example .env
python -m streamlit run main.py --server.address 127.0.0.1 --server.port 8501
```

http://127.0.0.1:8501 을 엽니다. 제목과 문의 생성 폼이 보이면 3차시, 로그인 폼이 먼저 보이면 4차시입니다. 서버 창을 닫지 않고 별도 CMD에서 화면을 실행합니다.
