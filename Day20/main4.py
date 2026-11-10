"""main4.md: 미완성 질문 보관, 한 번 실패시키기, 재시도/취소.

수정 전(main3.py의 설명을 구현한 main3-1.py):
- 완료 이벤트를 확인한 뒤에만 history에 질문/답변을 저장한다.
- 오류가 나면 질문과 부분 답변을 재시도할 별도 상태가 없다.
수정 후:
- 제출한 질문을 pending에 먼저 보관한다. history는 성공 대화만 담는다.
- 첫 텍스트 조각 직후 실패를 재현하고, 부분 답변과 오류를 pending에 남긴다.
- 재시도는 성공 history와 원래 질문으로 새로 요청한다(부분 답변 제외).
- 완료 확인 후에만 질문/답변 쌍을 저장하고 pending을 비운다.
- 취소는 pending만 비운다. 실패/취소 시 성공 대화 수는 변하지 않는다.

실행: streamlit run main4.py
"""

import os
import time

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

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

def render_answer(client, inputs, stats, fail_once=False):
    """
    Groq Responses API 스트리밍 응답

    진행 상태:
        1. 요청 중
        2. 수신 중
        3. 완료

    측정 항목:
        first : 첫 텍스트 수신 시간
        total : 전체 응답 시간
    """

    # ---------------------------------------------
    # 1. 요청 시작 시간 측정
    # ---------------------------------------------

    started = time.perf_counter()

    completed = False

    stats.update(
        first=None,
        total=None,
        partial="",
        updates=0,
        usage=None
    )

    # ---------------------------------------------
    # 2. 화면 출력 영역 생성
    # ---------------------------------------------

    answer_placeholder = st.empty()

    # 첫 글자가 도착하기 전 빈 화면 방지
    answer_placeholder.info(
        "⏳ 여행 정보를 분석하고 있습니다. 잠시 기다려 주세요."
    )

    # ---------------------------------------------
    # 3. 요청 상태 표시
    # ---------------------------------------------

    status = st.status(
        "🔵 요청 중 - 여행 정보를 분석하고 있습니다.",
        state="running",
        expanded=True
    )

    # 요청 상태 상세 안내
    status.write("Groq API에 여행 질문을 전달했습니다.")
    status.write("모델의 첫 번째 응답을 기다리고 있습니다.")

    try:

        # -----------------------------------------
        # 4. Groq API 스트리밍 요청
        # -----------------------------------------

        with client.responses.create(
            model=MODEL,
            input=inputs["input"],
            instructions=inputs["instructions"],
            stream=True,
            max_output_tokens=2048
        ) as stream:

            for event in stream:

                # ---------------------------------
                # 5. 첫 번째 텍스트 수신
                # ---------------------------------

                if event.type == "response.output_text.delta" and event.delta:

                    # 최초 텍스트 수신 시각 측정
                    if stats["first"] is None:

                        stats["first"] = (
                            time.perf_counter() - started
                        )

                        # 요청 중 -> 수신 중으로 상태 변경
                        status.update(
                            label="🟡 수신 중 - 답변을 생성하고 있습니다.",
                            state="running",
                            expanded=True
                        )

                        status.write(
                            f"첫 텍스트 수신 완료 "
                            f"({stats['first']:.2f}초)"
                        )

                    # ---------------------------------
                    # 6. 수신된 텍스트 누적
                    # ---------------------------------

                    stats["partial"] += event.delta

                    stats["updates"] += 1

                    # 실시간 답변 출력
                    answer_placeholder.markdown(
                        stats["partial"] + "▌"
                    )

                    # AFTER: 첫 조각을 화면에 표시한 직후 한 번만 실패시킨다.
                    # fail_once는 요청 시작 전에 소비하므로 재시도에는 적용되지 않는다.
                    if fail_once:
                        raise RuntimeError("실패 재현: 첫 텍스트 조각 수신 후 연결을 끊었습니다.")

                # ---------------------------------
                # 7. 정상 완료 이벤트
                # ---------------------------------

                elif event.type == "response.completed":

                    completed = True

                    # 전체 응답 완료 시간
                    stats["total"] = (
                        time.perf_counter() - started
                    )

                    response = event.response

                    # 토큰 사용량
                    if response.usage:

                        stats["usage"] = {
                            "input_tokens": response.usage.input_tokens,
                            "output_tokens": response.usage.output_tokens,
                            "total_tokens": response.usage.total_tokens
                        }

                # ---------------------------------
                # 8. 실패 또는 미완료 이벤트
                # ---------------------------------

                elif event.type in (
                    "response.failed",
                    "response.incomplete"
                ):

                    raise RuntimeError(
                        f"응답이 정상적으로 완료되지 않았습니다: "
                        f"{event.type}"
                    )

                elif event.type == "error":

                    raise RuntimeError(str(event))

        # -----------------------------------------
        # 9. 완료 이벤트 수신 여부 확인
        # -----------------------------------------

        if not completed:

            raise RuntimeError(
                "서버에서 정상적인 완료 이벤트를 받지 못했습니다."
            )

        if not stats["partial"].strip():
            raise RuntimeError("완료 이벤트를 받았지만 텍스트 답변이 비어 있습니다.")

        status.write(f"전체 응답 완료 ({stats['total']:.2f}초)")
        status.update(
            label="🟢 완료 - 답변 생성이 끝났습니다.",
            state="complete",
            expanded=False,
        )

        # 최종 답변 출력
        answer_placeholder.markdown(
            stats["partial"]
        )

        return stats["partial"]

    except Exception as e:

        # 오류 발생 시간 기록
        stats["total"] = (
            time.perf_counter() - started
        )

        # 오류 상태는 펼쳐서 상세 내용 표시
        status.update(
            label="🔴 오류 - 응답 생성에 실패했습니다.",
            state="error",
            expanded=True
        )

        status.write(str(e))
        answer_placeholder.markdown(
            stats["partial"] or "수신한 텍스트가 없습니다."
        )
        st.warning("미완성 답변입니다. 성공 대화 이력에는 저장하지 않습니다.")

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
    st.set_page_config(page_title="AI 여행 Agent", page_icon="✈️", layout="wide")
    st.title("✈️ AI 여행 Agent")
    st.caption("Groq GPT-OSS-20B · 요청 → 수신 → 완료 · 미완성 질문 재시도/취소")

    for key, value in {
        "history": [], "stats": {}, "client": None,
        "pending": None, "fail_next": False, "success_count": 0,
    }.items():
        st.session_state.setdefault(key, value)

    with st.sidebar:
        st.subheader("설정")
        st.write(f"모델: `{MODEL}`")
        st.metric("누적 성공 대화", st.session_state.success_count)
        st.caption(f"현재 보관한 성공 대화: {len(st.session_state.history) // 2}회")
        st.write(f"미완성 질문: {int(st.session_state.pending is not None)}개")
        if st.button("한번 실패시키기", key="arm_failure", width="stretch"):
            st.session_state.fail_next = True
        if st.session_state.fail_next:
            st.info("다음 시도에서 첫 텍스트 조각을 표시한 뒤 한 번 실패합니다.")
        st.caption("버튼을 누른 뒤 질문을 제출하세요. 재시도에도 적용할 수 있습니다.")
        if st.button("대화 초기화", key="reset", width="stretch"):
            st.session_state.history = []
            st.session_state.stats = {}
            st.session_state.pending = None
            st.session_state.fail_next = False
            st.session_state.success_count = 0
            st.rerun()

    with st.expander("수정 전 / 수정 후 비교"):
        st.markdown("""
| 항목 | 수정 전 (main3-1.py) | 수정 후 (main4.py) |
|---|---|---|
| 정상 이력 저장 | 완료 확인 후 저장 | 완료 확인 후에만 저장 (유지) |
| 실패한 질문 | 별도 보관 없음 | pending에 질문·부분 답변·오류 보관 |
| 중단 상황 재현 | 없음 | 첫 조각 이후 한 번 실패 버튼 |
| 재시도 | 질문을 다시 입력 | 원래 질문으로 새 요청, 부분 답변 제외 |
| 취소 | 없음 | pending만 제거, 성공 기록 유지 |
""")
        st.caption("실패 → 성공 수 유지, 재시도 성공 → 1 증가, 취소 → 성공 수 유지")

    for message in st.session_state.history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if st.session_state.stats:
        show_stats(st.session_state.stats)

    retry = False
    pending = st.session_state.pending
    if pending is not None:
        with st.container(border=True):
            st.subheader("미완성 질문 보관함")
            st.write(pending["question"])
            st.caption(f"시도 횟수: {pending['attempts']} · 상태: {pending['state']}")
            st.warning("이 질문과 부분 답변은 성공 대화 및 다음 요청의 과거 이력에 포함되지 않습니다.")
            if pending["error"]:
                st.error(pending["error"])
            with st.expander("미완성 답변 확인"):
                st.markdown(pending["partial"] or "수신한 텍스트가 없습니다.")
            left, right = st.columns(2)
            retry = left.button("재시도", key="retry", width="stretch")
            if right.button("취소", key="cancel", width="stretch"):
                st.session_state.pending = None
                st.rerun()

    question = st.chat_input(
        "미완성 질문을 재시도하거나 취소하세요." if pending else "어디로 여행을 떠나고 싶으신가요?",
        key="question", disabled=pending is not None,
    )
    if question and pending is None:
        question = question.strip()
        if not question:
            return
        # AFTER: API 호출보다 먼저 질문을 보관한다.
        st.session_state.pending = {
            "question": question, "partial": "", "error": None,
            "attempts": 0, "state": "대기",
        }
    elif not retry:
        return

    pending = st.session_state.pending
    pending.update(partial="", error=None, state="요청 중")
    pending["attempts"] += 1
    # 한 번만 소비: API 오류가 먼저 발생해도 다음 재시도에 남기지 않는다.
    fail_once = st.session_state.fail_next
    st.session_state.fail_next = False
    stats = {}
    with st.chat_message("user"):
        st.markdown(pending["question"])
    try:
        if st.session_state.client is None:
            st.session_state.client = create_client()
        inputs = build_input(st.session_state.history, pending["question"])
        with st.chat_message("assistant"):
            answer = render_answer(st.session_state.client, inputs, stats, fail_once)
    except Exception as exc:
        # 실패 시 history를 건드리지 않고 pending만 갱신한다.
        pending.update(partial=stats.get("partial", ""), error=str(exc), state="미완료")
    else:
        # render_answer가 완료 이벤트와 비어 있지 않은 답변을 확인한 경우만 저장.
        st.session_state.history = (st.session_state.history + [
            {"role": "user", "content": pending["question"]},
            {"role": "assistant", "content": answer},
        ])[-(MAX_HISTORY * 2):]
        st.session_state.success_count += 1
        st.session_state.pending = None
    st.session_state.stats = stats
    # 성공 수/보관함/버튼을 최신 상태로 즉시 다시 표시한다.
    st.rerun()


if __name__ == "__main__":
    main()
