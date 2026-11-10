
import os
import time
import re
import streamlit as st

from dotenv import load_dotenv
from openai import (
    APIError,
    AuthenticationError,
    RateLimitError,
    OpenAI
)

load_dotenv()


# =========================================================
# 1. Groq API Client 생성
# =========================================================
def create_client():

    key = os.getenv("GROQ_API_KEY", "").strip()

    if not key:
        raise ValueError("GROQ_API_KEY 환경변수가 설정되지 않았습니다.")

    args = {
        "api_key": key,
        "base_url": "https://api.groq.com/openai/v1",
        "timeout": 60.0,
        "max_retries": 0
    }

    return OpenAI(**args)


# =========================================================
# 2. 여행 Agent System Prompt
# =========================================================
SYSTEM_PROMPT = """
너는 여행 계획 및 관광 정보를 전문적으로 제공하는 AI 여행 Agent다.

[1. 역할과 목적]
- 사용자의 여행 목적과 요구사항을 분석하고 최적의 여행 정보를 제공한다.
- 여행지 추천, 관광 명소, 맛집, 숙박, 교통, 여행 경로, 예상 비용, 일정 등을 종합적으로 안내한다.
- 국내 여행과 해외여행 모두 지원한다.
- 단순한 정보 나열보다 실제 여행에 활용할 수 있는 구체적이고 실용적인 답변을 제공한다.

[2. 사용자 입력 분석]
- 사용자가 제공한 여행 정보를 가장 우선적으로 반영한다.
- 여행 지역, 여행 기간, 출발지, 인원, 예산, 교통수단, 여행 목적, 선호하는 활동 등을 분석한다.
- 정보가 충분하지 않더라도 일반적인 여행 패턴과 지역 특성을 바탕으로 합리적인 추천과 추론을 수행한다.
- 필수 정보가 부족하여 정확한 계획을 수립하기 어려운 경우에만 핵심 내용을 질문한다.
- 사용자가 명시한 조건과 일반적인 추천 기준이 충돌하면 반드시 사용자 조건을 우선한다.

[3. 여행지 및 관광 정보]
- 지역의 대표 관광지, 자연경관, 역사·문화 유적, 체험 활동, 축제 등을 고려한다.
- 여행자의 연령대, 동행자, 여행 목적에 적합한 장소를 추천한다.
- 관광지 간 거리와 이동 시간을 고려하여 효율적인 여행 동선을 구성한다.
- 지역별 특색과 계절적 특성을 반영한다.
- 실제 존재 여부가 불확실한 장소나 시설을 임의로 만들어내지 않는다.

[4. 여행 일정 수립]
- 여행 기간에 맞춰 일자별 일정을 구성한다.
- 각 일정은 시간대, 방문 장소, 활동 내용, 이동 방법을 포함한다.
- 불필요한 장거리 이동이나 지나치게 많은 관광지를 포함하지 않는다.
- 식사, 휴식, 이동 시간을 적절하게 배분한다.
- 여행지의 운영 시간, 휴무일, 계절별 이용 가능 여부를 고려한다.
- 사용자의 체력과 여행 스타일에 맞춰 무리하지 않는 일정을 제안한다.

[5. 교통 및 숙박]
- 자동차, 대중교통, 도보, 항공, 철도 등 적절한 이동 수단을 고려한다.
- 이동 거리와 예상 소요 시간을 안내한다.
- 숙박 장소는 주요 관광지와의 접근성 및 이동 효율성을 고려한다.
- 숙박비와 교통비는 예산 계획에 포함할 수 있도록 안내한다.
- 확인되지 않은 요금이나 예약 가능 여부를 확정적으로 표현하지 않는다.

[6. 맛집 및 음식 추천]
- 지역을 대표하는 음식과 특산물을 우선적으로 고려한다.
- 여행 동선과 가까운 식당을 추천한다.
- 음식 종류, 가격대, 특징 등을 설명한다.
- 실제 영업 여부나 운영 시간은 확인이 필요한 정보임을 구분한다.
- 존재하지 않는 식당이나 메뉴를 만들어내지 않는다.

[7. 예산 및 비용 분석]
- 교통비, 숙박비, 식비, 입장료, 체험비, 기타 비용을 구분한다.
- 여행 인원과 기간을 기준으로 예상 비용을 산출한다.
- 정확한 금액을 확인할 수 없는 경우 합리적인 추정 범위로 제공한다.
- 실제 가격과 예상 가격을 명확하게 구분한다.
- 예산이 제한된 경우 비용 대비 만족도가 높은 대안을 추천한다.

[8. 정보 신뢰성 및 할루시네이션 방지]
- 검증된 사실과 추론 또는 예상 정보를 구분한다.
- 실시간 확인이 필요한 항공권, 숙박 예약, 교통편, 날씨, 입장료, 영업시간 등은 확인되지 않은 정보를 사실처럼 답변하지 않는다.
- 외부 검색이나 API 데이터가 제공되면 해당 데이터를 우선적으로 활용한다.
- 정보가 없으면 모른다고 명확하게 설명하고 임의로 생성하지 않는다.
- 과거 정보와 현재 정보가 다를 수 있는 경우 최신 확인이 필요하다고 안내한다.

[9. 답변 작성 원칙]
- 기본적으로 한국어로 쉽고 명확하게 답변한다.
- 결론과 핵심 추천을 먼저 제시한다.
- 여행 일정은 날짜별 또는 시간대별로 구분한다.
- 여러 장소를 추천할 때는 추천 이유와 특징을 함께 설명한다.
- 필요에 따라 표, 목록, 번호 등을 활용한다.
- 불필요한 반복이나 장황한 설명은 피한다.
- 사용자가 간단한 답변을 요청하면 핵심 내용만 제공한다.
- 사용자가 상세한 계획을 요청하면 충분한 설명과 구체적인 정보를 제공한다.

[10. 최종 목표]
사용자가 별도의 여행 전문가 도움 없이도 실제 여행 계획을 세울 수 있도록 정확하고 실용적이며 실행 가능한 여행 정보를 제공한다.
"""


# =========================================================
# 3. 메시지 조합
# =========================================================
def build_input(history, question):

    system_messages = {
        "role": "system",
        "content": SYSTEM_PROMPT
    }

    return (
        [system_messages]
        + history
        + [{"role": "user", "content": question}]
    )


# =========================================================
# 4. 시간 문자열 변환
# =========================================================
def format_reset_time(value):

    if not value:
        return "정보 없음"

    # Groq 응답 예: 7.66s, 2m59.56s, 1h
    value = str(value).strip()

    pattern = (
        r"(?:(\d+(?:\.\d+)?)h)?"
        r"(?:(\d+(?:\.\d+)?)m)?"
        r"(?:(\d+(?:\.\d+)?)s)?"
    )

    match = re.fullmatch(pattern, value)

    if not match:
        return value

    hours = float(match.group(1) or 0)
    minutes = float(match.group(2) or 0)
    seconds = float(match.group(3) or 0)

    total = int(hours * 3600 + minutes * 60 + seconds)

    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)

    if h:
        return f"{h}시간 {m}분"
    elif m:
        return f"{m}분 {s}초"
    else:
        return f"{s}초"


# =========================================================
# 5. Groq API 응답 헤더 분석
# =========================================================
def extract_rate_limits(headers):

    # Groq 응답 헤더에서 Rate Limit 정보 추출
    return {
        "request_limit": headers.get(
            "x-ratelimit-limit-requests"
        ),
        "request_remaining": headers.get(
            "x-ratelimit-remaining-requests"
        ),
        "request_reset": headers.get(
            "x-ratelimit-reset-requests"
        ),
        "token_limit": headers.get(
            "x-ratelimit-limit-tokens"
        ),
        "token_remaining": headers.get(
            "x-ratelimit-remaining-tokens"
        ),
        "token_reset": headers.get(
            "x-ratelimit-reset-tokens"
        ),
        "retry_after": headers.get(
            "retry-after"
        )
    }


# =========================================================
# 6. LLM 응답 생성
# =========================================================
def render_answer(client, input_items):

    model = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-20b"
    )

    # 일반 create() 대신 with_raw_response를 사용하여
    # 답변과 HTTP 응답 헤더를 함께 확보한다.
    raw_response = client.chat.completions.with_raw_response.create(

        model=model,
        messages=input_items,

        temperature=0.5,
        top_p=0.9,
        max_tokens=2048,

        stream=False
    )

    # HTTP 응답 헤더 추출
    rate_limits = extract_rate_limits(
        raw_response.headers
    )

    # 실제 LLM 응답 데이터 파싱
    response = raw_response.parse()

    answer = response.choices[0].message.content

    if not answer:
        answer = "답변을 생성하지 못했습니다."

    # 모델이 실제 사용한 토큰 수
    usage = {
        "prompt_tokens": (
            response.usage.prompt_tokens
            if response.usage else 0
        ),
        "completion_tokens": (
            response.usage.completion_tokens
            if response.usage else 0
        ),
        "total_tokens": (
            response.usage.total_tokens
            if response.usage else 0
        )
    }

    # 답변, 제한 정보, 실제 사용 토큰 반환
    return answer.strip(), rate_limits, usage


# =========================================================
# 7. 숫자 포맷 함수
# =========================================================
def format_number(value):

    if value is None:
        return "-"

    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)


# =========================================================
# 8. 사용량 모니터링 UI
# =========================================================
def render_usage_panel():

    st.subheader("📊 Groq API 사용량")

    limits = st.session_state.groq_limits

    if not limits:

        st.info(
            "아직 API 호출 기록이 없습니다. "
            "첫 질문을 전송하면 사용량 정보가 표시됩니다."
        )

        st.markdown(
            "[Groq Usage Dashboard](https://console.groq.com/usage)"
        )

        return

    # ---------------------------------------------
    # 일일 요청 한도
    # ---------------------------------------------
    request_limit = limits.get("request_limit")
    request_remaining = limits.get("request_remaining")

    # ---------------------------------------------
    # 분당 토큰 한도
    # ---------------------------------------------
    token_limit = limits.get("token_limit")
    token_remaining = limits.get("token_remaining")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("**일일 요청 한도 (RPD)**")

        st.metric(
            "남은 요청",
            format_number(request_remaining),
            delta=(
                f"전체 {format_number(request_limit)}"
                if request_limit is not None
                else None
            )
        )

        if request_limit and request_remaining is not None:

            ratio = max(
                0.0,
                min(1.0, float(request_remaining) / float(request_limit))
            )

            st.progress(ratio)

        st.caption(
            "초기화: "
            + format_reset_time(limits.get("request_reset"))
        )

    with col2:

        st.markdown("**분당 토큰 한도 (TPM)**")

        st.metric(
            "남은 토큰",
            format_number(token_remaining),
            delta=(
                f"전체 {format_number(token_limit)}"
                if token_limit is not None
                else None
            )
        )

        if token_limit and token_remaining is not None:

            ratio = max(
                0.0,
                min(1.0, float(token_remaining) / float(token_limit))
            )

            st.progress(ratio)

        st.caption(
            "초기화: "
            + format_reset_time(limits.get("token_reset"))
        )

    st.divider()

    # ---------------------------------------------
    # 최근 요청의 실제 토큰 사용량
    # ---------------------------------------------
    usage = st.session_state.last_usage

    st.markdown("**최근 요청 토큰 사용량**")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "입력 토큰",
            format_number(usage.get("prompt_tokens"))
        )

    with col2:
        st.metric(
            "출력 토큰",
            format_number(usage.get("completion_tokens"))
        )

    with col3:
        st.metric(
            "전체 토큰",
            format_number(usage.get("total_tokens"))
        )

    st.caption(
        "※ 입력/출력 토큰은 가장 최근 요청 1회의 사용량입니다."
    )

    st.caption(
        "※ 위 Rate Limit은 마지막 API 응답 기준이며, "
        "브라우저 새로고침만으로 최신 값으로 갱신되지는 않습니다."
    )

    st.markdown(
        "[Groq 전체 사용량 확인](https://console.groq.com/usage) "
        "| "
        "[모델별 제한 확인](https://console.groq.com/settings/limits)"
    )


# =========================================================
# 9. Streamlit 메인 UI
# =========================================================
def main():

    st.set_page_config(
        page_title="AI 여행 Agent",
        page_icon="✈️",
        layout="wide"
    )

    st.title("✈️ AI 여행 전문 Agent")

    st.caption(
        "여행지 추천부터 일정, 교통, 숙박, 예상 비용까지!"
    )

    # ---------------------------------------------
    # Session State 초기화
    # ---------------------------------------------
    defaults = {
        "messages": [],
        "total_time": 0.0,
        "response_count": 0,
        "total_response_time": 0.0,
        "groq_limits": None,
        "last_usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value

    # ---------------------------------------------
    # 사이드바
    # ---------------------------------------------
    with st.sidebar:

        st.subheader("✈️ Travel Agent")

        st.info(
            "Groq LLM 기반 여행 전문 AI Agent입니다."
        )

        st.divider()

        st.markdown("### 📈 대화 통계")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "누적 대화",
                st.session_state.response_count
            )

        with col2:
            avg_time = (
                st.session_state.total_response_time
                / st.session_state.response_count
                if st.session_state.response_count > 0
                else 0
            )

            st.metric(
                "평균 응답",
                f"{avg_time:.2f}초"
            )

        st.metric(
            "최근 응답 시간",
            f"{st.session_state.total_time:.2f}초"
        )

        st.divider()

        # 사용량 모니터링
        render_usage_panel()

        st.divider()

        # 대화 초기화
        if st.button(
            "🗑️ 대화 초기화",
            use_container_width=True
        ):

            st.session_state.messages = []
            st.session_state.total_time = 0.0
            st.session_state.response_count = 0
            st.session_state.total_response_time = 0.0

            # 사용량 정보는 초기화하지 않는다.
            # API 사용량은 대화 이력과 별개이기 때문이다.

            st.rerun()

    # ---------------------------------------------
    # 이전 대화 출력
    # ---------------------------------------------
    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

            if (
                message["role"] == "assistant"
                and "elapsed" in message
            ):

                st.caption(
                    f"⏱️ 응답 시간: {message['elapsed']:.2f}초"
                )

    # ---------------------------------------------
    # 사용자 질문 입력
    # ---------------------------------------------
    question = st.chat_input(
        "여행에 대해 무엇이든 질문하세요."
    )

    if question:

        # 사용자 질문 출력
        with st.chat_message("user"):

            st.markdown(question)

        # 사용자 질문 저장
        st.session_state.messages.append({
            "role": "user",
            "content": question
        })

        # -----------------------------------------
        # 대화 이력 구성
        # elapsed 등의 UI 전용 데이터는 제거하고
        # OpenAI API가 요구하는 role/content만 전달
        # -----------------------------------------
        history = [
            {
                "role": message["role"],
                "content": message["content"]
            }
            for message in st.session_state.messages[:-1]
        ]

        # 모델 입력 메시지 생성
        input_items = build_input(
            history,
            question
        )

        # -----------------------------------------
        # AI 답변 생성
        # -----------------------------------------
        with st.chat_message("assistant"):

            try:

                # 클라이언트 생성
                client = create_client()

                with st.spinner(
                    "✈️ 여행 정보를 분석하고 있습니다..."
                ):

                    start_time = time.perf_counter()

                    # LLM 호출
                    answer, limits, usage = render_answer(
                        client,
                        input_items
                    )

                    elapsed = (
                        time.perf_counter() - start_time
                    )

                # ---------------------------------
                # 사용량 정보 Session State 저장
                # ---------------------------------
                st.session_state.groq_limits = limits
                st.session_state.last_usage = usage

                # ---------------------------------
                # 답변 화면 출력
                # ---------------------------------
                st.markdown(answer)

                st.caption(
                    f"⏱️ 응답 시간: {elapsed:.2f}초"
                )

                # ---------------------------------
                # 답변 이력 저장
                # ---------------------------------
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "elapsed": elapsed
                })

                # ---------------------------------
                # 응답 통계 갱신
                # ---------------------------------
                st.session_state.total_time = elapsed

                st.session_state.response_count += 1

                st.session_state.total_response_time += elapsed

                # ---------------------------------
                # 사이드바 사용량 정보 즉시 갱신
                # ---------------------------------
                st.rerun()

            # -------------------------------------
            # API 예외 처리
            # -------------------------------------
            except AuthenticationError:

                st.error(
                    "Groq API 인증 오류입니다. API Key를 확인하세요."
                )

            except RateLimitError as e:

                # 429 오류의 retry-after 확인
                retry_after = None

                if getattr(e, "response", None) is not None:
                    retry_after = e.response.headers.get(
                        "retry-after"
                    )

                if retry_after:
                    st.error(
                        f"API 사용량 제한에 도달했습니다. "
                        f"{retry_after}초 후 다시 시도하세요."
                    )
                else:
                    st.error(
                        "API 사용량 제한에 도달했습니다. "
                        "Groq Console에서 제한 상태를 확인하세요."
                    )

            except APIError as e:

                st.error(
                    f"Groq API 호출 오류: {str(e)}"
                )

            except Exception as e:

                st.error(
                    f"오류가 발생했습니다: {str(e)}"
                )


# =========================================================
# 10. 프로그램 시작
# =========================================================
if __name__ == "__main__":

    main()
