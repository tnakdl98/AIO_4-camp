import os
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict, EmailStr, SecretStr
from supabase.client import ClientOptions
from supabase import create_client, AuthApiError, AuthRetryableError


load_dotenv(override = True)  # .env 파일의 값을 환경변수로 불러오고, 기존 값은 덮어씁니다.
print(os.getenv('host',""))

supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
supabase_key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()
if not supabase_url or not supabase_key:
    raise RuntimeError('SUPABASE_URL or SUPABASE_PUBLISHABLE_KEY missing')

app = FastAPI(title="Supabase Auth - 회원가입")
# pydentic을 이용한 타입검사
class SignupRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email : EmailStr
    password : SecretStr = Field(min_length=8, max_length=128)

class SignupResponse(BaseModel):
    message : str

@app.exception_handler(RequestValidationError)  # 요청 데이터 검증 오류를 아래 함수에서 처리하도록 등록
async def handler_validation_error(_request:Request, exc:RequestValidationError):  # 요청과 검증 오류를 받아 처리
    errors = [
        {'loc':error['loc'], 'type': error['type']} 
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={'detail': errors})

@app.post('/auth/signup',response_model=SignupResponse)

def signup(body : SignupRequest):
    try:
        # 요청할때마다 클라이언트를 만들고 통신(Supabase)이 끝나면 자동으로 닫는다.
        with httpx.Client(timeout=10.0) as http_client:
            supabase = create_client(
                supabase_url = supabase_url, 
                supabase_key = supabase_key,
                options= ClientOptions(
                    persist_session=False,
                    auto_refresh_token=False,
                    httpx_client=http_client
                )
            )
            supabase.auth.sign_up(
                {
                    'email' : str(body.email),
                    'password':body.password.get_secret_value()
            })
    except AuthApiError as err:
        print("Supabase 인증 오류:", err)
        if err.status == 429:
            raise HTTPException(429, '요청이 많습니다. 잠시 후 다시 시도하세요')
        if err.status >= 500 or err.status == 401:
            
            raise HTTPException(503, '인증 서비스 상태 또는 연결 설정을 확인')
        raise HTTPException(400, '입력과 auth 설정을 확인하세요')
    
    except (AuthRetryableError, httpx.HTTPError):
        raise HTTPException(503, '인증서비스에 연결할 수 없습니다. 잠시 후 다시 시도하세요')
    return SignupResponse(message='가입요청을 처리했습니다. 이메일 확인 설정이 켜져있다면 받을 메일을 확인해보세요')

class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email : EmailStr
    password : SecretStr = Field(min_length=1)

class LoginResponse(BaseModel):
    # 토큰을 호출자에게 전달 - 응답필드는 str로 선언
    access_token : str 
    refresh_token : str
    token_type : str
    expires_in : int
    expires_at : int | None
    user_id : str
    email : str | None

@app.post('/auth/login',response_model=LoginResponse)       # 반환할 json구조를 검증하고 swagger에 표시
def login(body : LoginRequest, response : Response):
    with httpx.Client(timeout=10.0) as http_client:
        supabase = create_client(
            supabase_url = supabase_url, 
            supabase_key = supabase_key,
            options= ClientOptions(
                persist_session=False,                      # session을 자동으로 하지않음.
                auto_refresh_token=False,
                httpx_client=http_client
            )
        )
        result = supabase.auth.sign_in_with_password(
            {
                'email' : str(body.email),
                'password':body.password.get_secret_value()
            }
        )
    session = result.session
    user = result.user
    response.headers['Cache-Control'] = 'no-store'          # 토큰이 포함된 응답을 브라우저와 중간 캐시에 저장하지 않도록 설정
    return LoginResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        token_type=session.token_type,
        expires_in=session.expires_in,
        expires_at=session.expires_at,
        user_id=user.id,
        email=user.email
    )

# 필요한 정보만 담는다(토큰, 패스워드는 제외)
class CurrentUser(BaseModel):
    id:str
    email:str | None    


    