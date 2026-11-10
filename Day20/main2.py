
import os
import time

import streamlit as st
from dotenv import load_dotenv
from openai import APIError, OpenAI

load_dotenv()

# =========================================================
# 1. 기본 설정
# =========================================================

MODEL = "openai/gpt-oss-20b"

# 첫 텍스트 수신이 이 시간보다 늦으면 긴 대기 안내로 분류
LONG_WAIT_SECONDS = 3.0

# 대화 이력 최대 보관 개수 (질문 + 답변 쌍)
MAX_HISTORY = 20


# =========================================================
# 2. Groq 모델 클라이언트 생성
# =========================================================

def create_client():

    key = os.getenv("GROQ_API_KEY", "").strip()

    if not key:
        raise ValueError(
            "GROQ_API_KEY 환경변수가 설정되지 않았습니다."
        )

    args = {
        "api_key": key,
        "base_url": "https://api.groq.com/openai/v1",
        "timeout": 60.0,
        "max_retries": 0
    }

    return OpenAI(**args)


# =========================================================
# 3. 메세지 조합 함수
# =========================================================

def build_input(history, question):

    system_messages = {
        "role": "system",
        "content": """
너는 여행 계획 및 관광 정보를 전문적으로 제공하는 AI 여행 Agent다.

[1. 역할과 목적]
- 사용자의 여행 목적과 요구사항을 분석하고 최적의 여행 정보를 제공한다.
- 여행지 추천, 관광 명소, 맛집, 숙박, 교통, 여행 경로,
  예상 비용, 일정 등을 종합적으로 안내한다.
- 국내 여행과 해외여행 모두 지원한다.
- 실제 여행에 활용할 수 있는 구체적이고 실용적인 답변을 제공한다.

[2. 사용자 입력 분석]
- 사용자가 제공한 여행 정보를 가장 우선적으로 반영한다.
- 여행 지역, 기간, 출발지, 인원, 예산, 교통수단,
  여행 목적, 선호 활동 등을 분석한다.
- 정보가 충분하지 않더라도 일반적인 여행 패턴과
  지역 특성을 바탕으로 합리적인 추천과 추론을 수행한다.
- 필수 정보가 부족한 경우에만 핵심 내용을 질문한다.
- 일반적인 추천 기준보다 사용자의 명시적인 조건을 우선한다.

[3. 여행지 및 관광 정보]
- 대표 관광지, 자연경관, 역사·문화 유적, 체험 활동, 축제 등을 고려한다.
- 여행자의 연령대, 동행자, 여행 목적에 적합한 장소를 추천한다.
- 관광지 간 거리와 이동 시간을 고려하여 효율적인 동선을 구성한다.
- 지역별 특색과 계절적 특성을 반영한다.
- 실제 존재 여부가 불확실한 장소를 임의로 만들어내지 않는다.

[4. 여행 일정 수립]
- 여행 기간에 맞춰 일자별 일정을 구성한다.
- 시간대, 방문 장소, 활동 내용, 이동 방법을 포함한다.
- 불필요한 장거리 이동이나 지나치게 많은 관광지를 포함하지 않는다.
- 식사, 휴식, 이동 시간을 적절하게 배분한다.
- 운영 시간과 휴무일은 확인되지 않은 경우 확인 필요로 표시한다.
- 사용자의 체력과 여행 스타일에 맞춰 일정을 제안한다.

[5. 교통 및 숙박]
- 자동차, 대중교통, 도보, 항공, 철도 등을 고려한다.
- 이동 거리와 예상 소요 시간을 안내한다.
- 숙박은 주요 관광지와의 접근성을 고려한다.
- 숙박비와 교통비를 예산에 포함한다.
- 확인되지 않은 요금이나 예약 가능 여부를 확정적으로 표현하지 않는다.

[6. 맛집 및 음식 추천]
- 지역 대표 음식과 특산물을 우선 고려한다.
- 여행 동선과 가까운 식당을 추천한다.
- 음식 종류, 가격대, 특징을 설명한다.
- 실제 영업 여부와 운영 시간은 확인이 필요한 정보임을 구분한다.
- 존재하지 않는 식당이나 메뉴를 만들어내지 않는다.

[7. 예산 및 비용 분석]
- 교통비, 숙박비, 식비, 입장료, 체험비, 기타 비용을 구분한다.
- 여행 인원과 기간을 기준으로 예상 비용을 산출한다.
- 정확한 금액을 모르는 경우 합리적인 추정 범위로 제공한다.
- 실제 가격과 예상 가격을 구분한다.
- 제한된 예산에 적합한 대안을 추천한다.

[8. 정보 신뢰성]
- 검증된 사실과 추론 또는 예상 정보를 구분한다.
- 실시간 확인이 필요한 정보는 확인되지 않은 사실처럼 답변하지 않는다.
- 외부 검색이나 API 데이터가 제공되면 해당 데이터를 우선 활용한다.
- 정보가 없으면 모른다고 설명하고 임의로 생성하지 않는다.
- 과거 정보와 현재 정보가 다를 수 있으면 최신 확인이 필요하다고 안내한다.

[9. 답변 작성 원칙]
- 한국어로 쉽고 명확하게 답변한다.
- 결론과 핵심 추천을 먼저 제시한다.
- 여행 일정은 날짜별 또는 시간대별로 구분한다.
- 장소 추천 시 이유와 특징을 함께 설명한다.
- 필요에 따라 표, 목록, 번호를 활용한다.
- 불필요한 반복과 장황한 설명은 피한다.
- 간단한 질문에는 간결하게, 상세한 계획에는 충분하게 답변한다.

[10. 최종 목표]
사용자가 별도의 여행 전문가 도움 없이도 실제 여행 계획을
수립할 수 있도록 정확하고 실용적인 정보를 제공한다.
"""
    }

    # 이전 대화 + 현재 질문
    # 시스템 메시지는 별도 instructions로 전달한다.
    return {
        "instructions": system_messages["content"],
        "input": history + [
            {
                "role": "user",
                "content": question
            }
        ]
    }


# =========================================================
# 4. 스트리밍 응답 생성
# =========================================================

def render_answer(client, inputs, stats):
    """
    Groq Responses API를 이용한 실시간 답변 생성

    stats:
        first   : 첫 텍스트 수신 시간
        total   : 전체 응답 생성 시간
        partial : 현재까지 생성된 텍스트
        updates : 수신 이벤트 개수
        usage   : 토큰 사용량
    """

    # 요청 시작 시간
    started = time.perf_counter()

    # 통계 초기화
    stats.update(
        first=None,
        total=None,
        partial="",
        updates=0,
        usage=None
    )

    # Streamlit 출력 영역
    answer_placeholder = st.empty()

    # 답변 생성 상태 표시
    status = st.status(
        "여행 정보를 분석하고 있습니다...",
        expanded=True
    )

    try:

        # Responses API 스트리밍 호출
        with client.responses.create(
            model=MODEL,
            input=inputs["input"],
            instructions=inputs["instructions"],
            stream=True,
            max_output_tokens=2048
        ) as stream:

            for event in stream:

                # -----------------------------------------
                # 텍스트 조각 수신
                # -----------------------------------------

                if event.type == "response.output_text.delta":

                    # 첫 텍스트가 도착한 시점
                    if stats["first"] is None:

                        stats["first"] = (
                            time.perf_counter() - started
                        )

                        if stats["first"] >= LONG_WAIT_SECONDS:

                            status.update(
                                label="분석 시간이 길어졌습니다. 답변을 생성하고 있습니다...",
                                state="running"
                            )

                        else:

                            status.update(
                                label="답변을 생성하고 있습니다...",
                                state="running"
                            )

                    # 새로 수신된 텍스트 누적
                    stats["partial"] += event.delta

                    stats["updates"] += 1

                    # 실시간 화면 출력
                    answer_placeholder.markdown(
                        stats["partial"] + "▌"
                    )

                # -----------------------------------------
                # 응답 완료
                # -----------------------------------------

                elif event.type == "response.completed":

                    # 전체 응답 종료 시간
                    stats["total"] = (
                        time.perf_counter() - started
                    )

                    # 토큰 사용량 정보
                    response = event.response

                    if response.usage:

                        stats["usage"] = {
                            "input_tokens": response.usage.input_tokens,
                            "output_tokens": response.usage.output_tokens,
                            "total_tokens": response.usage.total_tokens
                        }

                # -----------------------------------------
                # 응답 실패 및 오류
                # -----------------------------------------

                elif event.type in (
                    "response.failed",
                    "response.incomplete"
                ):

                    raise RuntimeError(
                        f"응답 생성이 정상적으로 완료되지 않았습니다: "
                        f"{event.type}"
                    )

                elif event.type == "error":

                    raise RuntimeError(
                        str(event)
                    )

        # 최종 답변 출력
        answer_placeholder.markdown(
            stats["partial"]
        )

        status.update(
            label="답변 생성 완료",
            state="complete",
            expanded=False
        )

        return stats["partial"]

    except Exception:

        status.update(
            label="답변 생성 중 오류가 발생했습니다.",
            state="error",
            expanded=True
        )

        raise


# =========================================================
# 5. 응답 시간 및 사용량 출력
# =========================================================

def show_stats(stats):

    st.divider()

    st.markdown("#### 📊 응답 성능")

    col1, col2, col3 = st.columns(3)

    first = stats.get("first")
    total = stats.get("total")

    with col1:

        st.metric(
            label="첫 텍스트 수신 (TTFT)",
            value=(
                f"{first:.2f}초"
                if first is not None else "-"
            )
        )

    with col2:

        st.metric(
            label="전체 응답 시간",
            value=(
                f"{total:.2f}초"
                if total is not None else "-"
            )
        )

    with col3:

        st.metric(
            label="텍스트 수신 이벤트",
            value=stats.get("updates", 0)
        )

    # 토큰 사용량
    usage = stats.get("usage")

    if usage:

        st.caption(
            f"입력 토큰: {usage['input_tokens']:,} | "
            f"출력 토큰: {usage['output_tokens']:,} | "
            f"총 토큰: {usage['total_tokens']:,}"
        )


# =========================================================
# 6. 메인 함수 - Streamlit UX
# =========================================================

def main():

    st.set_page_config(
        page_title="AI 여행 Agent",
        page_icon="✈️",
        layout="wide"
    )

    st.title("✈️ AI 여행 Agent")

    st.caption(
        "Groq GPT-OSS-20B 기반 여행 계획 및 관광 정보 도우미"
    )

    # ---------------------------------------------
    # Session State 초기화
    # ---------------------------------------------

    if "history" not in st.session_state:

        # API에 전달할 대화 이력
        st.session_state.history = []

    if "stats" not in st.session_state:

        # 마지막 요청의 응답 통계
        st.session_state.stats = {}

    if "client" not in st.session_state:

        # 클라이언트 재사용
        st.session_state.client = None

    # ---------------------------------------------
    # 사이드바
    # ---------------------------------------------

    with st.sidebar:

        st.subheader("⚙️ 설정")

        st.write(f"모델: `{MODEL}`")

        st.write(
            f"대화 이력: {len(st.session_state.history) // 2}회"
        )

        if st.button("🗑️ 대화 초기화", use_container_width=True):

            st.session_state.history = []
            st.session_state.stats = {}

            st.rerun()

        st.divider()

        st.caption(
            "첫 텍스트 수신 시간과 전체 응답 시간을 측정합니다."
        )

    # ---------------------------------------------
    # 이전 대화 출력
    # ---------------------------------------------

    for message in st.session_state.history:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

    # ---------------------------------------------
    # 마지막 응답 성능 출력
    # ---------------------------------------------

    if st.session_state.stats:

        show_stats(st.session_state.stats)

    # ---------------------------------------------
    # 사용자 질문 입력
    # ---------------------------------------------

    question = st.chat_input(
        "어디로 여행을 떠나고 싶으신가요?"
    )

    if not question:

        return

    # ---------------------------------------------
    # 사용자 질문 화면 출력
    # ---------------------------------------------

    with st.chat_message("user"):

        st.markdown(question)

    # ---------------------------------------------
    # API 호출
    # ---------------------------------------------

    try:

        # 클라이언트 생성 및 재사용
        if st.session_state.client is None:

            st.session_state.client = create_client()

        client = st.session_state.client

        # 이전 대화 내용을 기반으로 입력 구성
        inputs = build_input(
            st.session_state.history,
            question
        )

        # 답변 생성
        with st.chat_message("assistant"):

            stats = {}

            answer = render_answer(
                client,
                inputs,
                stats
            )

            # 응답 통계 저장
            st.session_state.stats = stats

            # 응답 성능 표시
            show_stats(stats)

        # -----------------------------------------
        # 대화 이력 저장
        # -----------------------------------------

        if answer:

            st.session_state.history.extend([
                {
                    "role": "user",
                    "content": question
                },
                {
                    "role": "assistant",
                    "content": answer
                }
            ])

            # 오래된 대화부터 제거
            # MAX_HISTORY는 질문/답변 쌍의 개수
            st.session_state.history = (
                st.session_state.history[-(MAX_HISTORY * 2):]
            )

    except APIError as e:

        st.error(
            f"Groq API 호출 오류: {e}"
        )

    except ValueError as e:

        st.error(str(e))

    except Exception as e:

        st.error(
            f"응답 생성 중 오류가 발생했습니다: {e}"
        )


# =========================================================
# 7. 프로그램 실행
# =========================================================

if __name__ == "__main__":

    main()
