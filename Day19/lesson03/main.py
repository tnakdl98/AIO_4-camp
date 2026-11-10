"""3차시: 서버에 보관한 문의를 ID로 다시 열어 연속 상담한다."""
import os
from uuid import uuid4
import httpx
import streamlit as st
from dotenv import load_dotenv

st.title("IT 헬프데스크 · 서버 상담")
load_dotenv(".env", override=False, interpolate=False)
API_BASE_URL = os.getenv("API_BASE_URL", "").strip().rstrip("/")
if not API_BASE_URL.startswith(("http://", "https://")):
    st.error(".env의 API_BASE_URL을 확인하세요.")
    st.stop()


def api(method, path, payload=None):
    headers = {}
    token = st.session_state.get("access_token")
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        if method == "POST" and path.endswith("/turns") and st.session_state.pop("fail_next", False):
            raise httpx.ConnectError("실습용 연결 실패")
        response = httpx.request(method, API_BASE_URL + path, json=payload,
                                 headers=headers, timeout=90.0)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            for key in ("access_token", "ticket_id", "pending", "last_result", "fail_next", "rejected_question"):
                st.session_state.pop(key, None)
            st.session_state["error"] = "로그인 정보를 확인하고 다시 로그인하세요."
            st.rerun()
        if method == "POST" and path.endswith("/turns"):
            status = exc.response.status_code
            if status in (400, 403, 404, 409, 422):
                detail = exc.response.json().get("detail", "요청 조건을 확인하세요.")
                if not isinstance(detail, str):
                    detail = "입력 필드와 글자 수, 요청 번호 형식을 확인하세요."
                pending = st.session_state.get("pending") or {}
                st.session_state["rejected_question"] = pending.get("question", "")
                st.session_state["pending"] = None
                st.session_state["error"] = f"요청 거절 ({status}): {detail} 질문을 수정하거나 다른 문의를 시작하세요."
            else:
                st.session_state["error"] = f"상담 요청 실패 ({status}). 기록을 확인한 뒤 재시도하세요."
            st.rerun()
        st.error(f"요청 실패 ({exc.response.status_code}). 문의 ID 또는 서버 설정을 확인하세요.")
        st.stop()
    except httpx.RequestError:
        if method == "POST" and path.endswith("/turns"):
            st.session_state["error"] = "연결 실패. 확인 중인 질문을 같은 요청 번호로 다시 보낼 수 있습니다."
            st.rerun()
        st.error("서버에 연결할 수 없습니다. 백엔드 CMD를 확인하세요.")
        st.stop()
    return response.json()


error = st.session_state.pop("error", None)
if error:
    st.error(error)
rejected = st.session_state.pop("rejected_question", None)
if rejected:
    st.text("수정이 필요한 질문: " + rejected)
st.caption("본인 PC에서 단일 사용자가 서버 상태를 확인하는 단계입니다.")
if st.button("다른 문의로 이동"):
    if st.session_state.get("pending"):
        st.warning("확인 중인 질문을 먼저 재시도하세요. 새 문의로 이동하지 않았습니다.")
    else:
        for key in ("ticket_id", "last_result", "fail_next", "rejected_question"):
            st.session_state.pop(key, None)
        st.rerun()
if "ticket_id" not in st.session_state:
    # 문의 ID를 사용해 기존 서버 기록을 다시 연다.
    with st.form("resume"):
        saved_id = st.text_input("다시 열 문의 ID")
        resume = st.form_submit_button("기존 문의 열기")
    if resume:
        try:
            from uuid import UUID
            saved_id = str(UUID(saved_id.strip()))
        except ValueError:
            st.warning("문의 ID 전체를 입력하세요.")
        else:
            api("GET", f"/tickets/{saved_id}")
            st.session_state["ticket_id"] = saved_id
            st.rerun()
    with st.form("create"):
        subject = st.text_input("문의 제목", value="VPN 접속 문의")
        service = st.selectbox("서비스", ["VPN", "화상회의"])
        environment = st.text_input("사용 환경", value="Windows 11")
        impact = st.selectbox("영향 범위", ["본인만", "팀 전체"])
        create = st.form_submit_button("서버에 문의 만들기")
    if create:
        ticket = api("POST", "/tickets", {"subject": subject, "service": service,
                     "environment": environment, "impact": impact})
        st.session_state["ticket_id"] = ticket["id"]
        st.rerun()
    st.stop()
ticket_id = st.session_state["ticket_id"]
ticket = api("GET", f"/tickets/{ticket_id}")
st.code(ticket_id, language=None)
st.info(f"{ticket['case']['subject']} | {ticket['case']['environment']} | {ticket['case']['impact']}")
st.caption(f"서버에 저장된 성공 상담: {ticket['turn_count']}턴")
st.button("서버 기록 다시 읽기")
for turn in ticket["turns"]:
    with st.chat_message("user"):
        st.text(turn["question"])
    with st.chat_message("assistant"):
        st.text(turn["answer"])
if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    st.caption(f"직전 요청의 이전 메시지: {result['context_message_count']}개 / input 전체: {result['input_count']}개")
with st.expander("연결 실패 실습"):
    if st.button("다음 상담 한 번 실패시키기", disabled=bool(st.session_state.get("pending"))):
        st.session_state["fail_next"] = True
    if st.session_state.get("fail_next"):
        st.info("다음 상담 전송을 한 번 실패시킵니다.")
pending = st.session_state.get("pending")
question = st.chat_input("후속 질문을 입력하세요", disabled=pending is not None)
submitted = False
if question and question.strip() and pending is None:
    st.session_state["pending"] = {"question": question.strip(), "request_id": str(uuid4())}
    submitted = True
pending = st.session_state.get("pending")
retry = False
if pending:
    st.text("확인 중인 질문: " + pending["question"])
    st.caption("요청 번호: " + pending["request_id"])
    retry = st.button("같은 질문 다시 보내기")
if pending and (submitted or retry):
    result = api("POST", f"/tickets/{ticket_id}/turns", pending)
    st.session_state["pending"] = None
    st.session_state["last_result"] = result
    st.rerun()
