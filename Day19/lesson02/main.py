"""2차시: 문의 카드, 연속 상담, 담당자 인계 메모를 연결한다."""
import os
from uuid import uuid4
import httpx
import streamlit as st
from dotenv import load_dotenv
from openai import APIConnectionError, APIError, OpenAI

st.title("IT 헬프데스크 · 문의 카드 상담")

load_dotenv(".env", override=False, interpolate=False)
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()

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

if not os.getenv("GROQ_API_KEY", "").strip() or not MODEL:
    st.error(".env의 GROQ_API_KEY와 GROQ_MODEL을 입력하세요.")
    st.stop()


def case_message(case):
    return {"role": "user", "content": (
        f"[문의 카드] 제목: {case['subject']} / 서비스: {case['service']} / "
        f"환경: {case['environment']} / 영향: {case['impact']}"
    )}


def build_input(case, history, question):
    return [case_message(case)] + history + [{"role": "user", "content": question}]


def handoff_question():
    return "앞선 상담을 [확인된 사실], [미확인 사항], [다음 담당자 조치]로 정리하세요. 각 항목은 한 문장입니다."


if st.button("새 문의 카드"):
    for key in ("case", "history", "last_input", "handoff", "fail_next"):
        st.session_state.pop(key, None)
    st.rerun()
if "case" not in st.session_state:
    with st.form("case_form"):
        subject = st.text_input("문의 제목", value="VPN 접속 문의")
        service = st.selectbox("서비스", ["VPN", "화상회의"])
        environment = st.text_input("사용 환경", value="Windows 11")
        impact = st.selectbox("영향 범위", ["본인만", "팀 전체"])
        created = st.form_submit_button("문의 카드 시작")
    if created:
        if not subject.strip() or not environment.strip():
            st.warning("제목과 사용 환경을 입력하세요.")
        else:
            st.session_state["case"] = {"id": str(uuid4()), "subject": subject.strip(),
                "service": service, "environment": environment.strip(), "impact": impact}
            st.session_state["history"] = []
            st.rerun()
    st.stop()
case = st.session_state["case"]
history = st.session_state["history"]
st.info(f"{case['subject']} | {case['service']} | {case['environment']} | {case['impact']}")
st.caption(f"성공한 상담: {len(history) // 2}턴")
st.button("화면 다시 실행")
for message in history:
    with st.chat_message(message["role"]):
        st.text(message["content"])
if "last_input" in st.session_state:
    with st.expander("Groq에 전달한 input"):
        st.json(st.session_state["last_input"])
if st.button("담당자 인계 메모 만들기", disabled=not history):
    inputs = build_input(case, history, handoff_question())
    try:
        response = ask_groq(inputs, instructions=("한국어 IT 문의 인계 메모 작성자입니다. 기록에 있는 사실만 사용하세요. "
            "[확인된 사실], [미확인 사항], [다음 담당자 조치] 세 제목을 사용하세요. "
            "비밀번호나 토큰을 요청하지 말고 실제 작업을 수행했다고 주장하지 마세요."))
    except (APIError, ValueError):
        st.error("인계 메모 생성 실패. 성공한 상담 기록은 유지합니다.")
    else:
        st.session_state["handoff"] = response.output_text
if st.session_state.get("handoff"):
    st.subheader("담당자 인계 메모")
    st.text(st.session_state["handoff"])
with st.expander("연결 실패 실습"):
    if st.button("다음 상담 한 번 실패시키기"):
        st.session_state["fail_next"] = True
    if st.session_state.get("fail_next"):
        st.info("다음 질문 전송을 한 번 실패시킵니다.")
question = st.chat_input("새로 확인한 사실이나 후속 질문을 입력하세요")
if question and question.strip():
    question = question.strip()
    if len(question) > 1000 or len(history) >= 24:
        st.warning("문의는 1000자, 한 카드는 최대 12턴입니다. 새 문의 카드를 시작하세요.")
        st.stop()
    inputs = build_input(case, history, question)
    try:
        if st.session_state.pop("fail_next", False):
            raise APIConnectionError(request=httpx.Request("POST", "https://api.groq.com/openai/v1/responses"))
        response = ask_groq(inputs)
    except (APIError, ValueError):
        st.error("상담 요청 실패. 성공한 기록은 그대로입니다. 같은 질문을 다시 입력하세요.")
        st.stop()
    st.session_state["last_input"] = inputs
    st.session_state.pop("handoff", None)
    history.extend([{"role": "user", "content": question},
                    {"role": "assistant", "content": response.output_text}])
    st.rerun()
