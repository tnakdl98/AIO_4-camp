"""8차시: 로그인 유지, 대화 전환, 저장 실패와 재시도."""
import os
from uuid import uuid4

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv(".env", override=False, interpolate=False)
API_BASE_URL = os.getenv("API_BASE_URL", "").strip().rstrip("/")
if not API_BASE_URL.startswith(("http://", "https://")):
    st.error(".env의 API_BASE_URL 설정을 확인하세요.")
    st.stop()

for key, value in {"access_token": "", "user": None, "pending": None}.items():
    if key not in st.session_state:
        st.session_state[key] = value


def clear_private():
    for key in (
        "access_token", "user", "conversations", "selected_id", "messages",
        "pending", "bound_user_id", "fail_next_save", "save_error", "notice",
    ):
        st.session_state.pop(key, None)


def api(method, path, payload=None):
    headers = {}
    token = st.session_state.get("access_token")
    if token:
        headers["Authorization"] = "Bearer " + token

    simulated_failure = False
    try:
        # 로그인·조회 요청은 건드리지 않고 다음 메시지 저장만 한 번 실패시킨다.
        if (
            method == "POST"
            and path.startswith("/conversations/")
            and path.endswith("/messages")
            and st.session_state.pop("fail_next_save", False)
        ):
            simulated_failure = True
            raise httpx.ConnectError("실습용 저장 연결 실패")

        response = httpx.request(
            method, API_BASE_URL + path,
            json=payload, headers=headers, timeout=15.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 401:
            clear_private()
            st.session_state["notice"] = (
                "로그인 정보를 확인하세요." if path == "/auth/login"
                else "로그인이 만료되었거나 유효하지 않습니다. 다시 로그인하세요."
            )
            st.rerun()
        elif status == 503:
            st.error("서버 또는 저장소가 응답하지 않습니다. 잠시 후 다시 시도하세요.")
        elif status == 404:
            st.session_state.pop("messages", None)
            st.error("대화를 찾을 수 없습니다. 대화 목록을 확인하세요.")
        else:
            st.error(f"요청에 실패했습니다. 상태 코드: {status}")
        st.stop()
    except httpx.RequestError:
        if simulated_failure:
            # pending은 남겨 두고, 입력창이 즉시 잠기도록 화면을 다시 그린다.
            st.session_state["save_error"] = (
                "실습용 저장 실패가 발생했습니다. 메시지는 아직 서버에 보내지 않았습니다."
            )
            st.rerun()
        st.error("서버와 통신할 수 없습니다. 연결을 확인하고 화면 다시 실행을 누르세요.")
        st.stop()
    return response.json()


def logout_and_clear():
    token = st.session_state.get("access_token", "")
    ended = False
    try:
        response = httpx.post(
            API_BASE_URL + "/auth/logout",
            headers={"Authorization": "Bearer " + token}, timeout=15.0,
        )
        ended = response.status_code in (200, 401)
    except httpx.RequestError:
        pass
    clear_private()
    st.session_state["notice"] = (
        "로그아웃했습니다." if ended
        else "화면의 로그인 정보는 지웠습니다. 서버 로그아웃은 확인하지 못했습니다."
    )
    st.rerun()


st.title("두 계정으로 로그인·이력·전환 확인하기")
st.button("화면 다시 실행")
notice = st.session_state.pop("notice", None)
if notice:
    st.info(notice)
save_error = st.session_state.pop("save_error", None)
if save_error:
    st.error(save_error)

if not st.session_state.get("access_token"):
    with st.form("login_form", clear_on_submit=True):
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인")
    if submitted:
        if not email.strip() or not password:
            st.warning("이메일과 비밀번호를 입력하세요.")
        else:
            result = api("POST", "/auth/login", {
                "email": email.strip(), "password": password,
            })
            clear_private()
            st.session_state["access_token"] = result["access_token"]
            st.session_state["user"] = {
                "id": result["user_id"], "email": result["email"],
            }
            st.rerun()
    st.stop()

if st.button("로그아웃"):
    logout_and_clear()
if st.button("계정 바꾸기"):
    logout_and_clear()

profile = api("GET", "/me")
st.session_state["user"] = {"id": profile["id"], "email": profile["email"]}
st.success("로그인 유지 중")
st.text("현재 계정: " + (profile["email"] or profile["id"]))
st.caption(f"로그인 세션 남은 시간: {profile['ttl']}초 (조회 시점)")

if st.session_state.get("bound_user_id") != profile["id"]:
    for key in ("conversations", "selected_id", "messages", "pending", "fail_next_save"):
        st.session_state.pop(key, None)
    st.session_state["bound_user_id"] = profile["id"]

rooms = api("GET", "/conversations")
st.session_state["conversations"] = rooms
if not rooms:
    st.info("저장된 대화가 없습니다. 백엔드에서 샘플 대화를 준비하세요.")
    st.stop()

labels = {room["id"]: room["title"] + " · " + room["id"][:8] for room in rooms}
ids = list(labels)
if st.session_state.get("selected_id") not in ids:
    st.session_state["selected_id"] = ids[0]


def room_label(room_id):
    return labels[room_id]


selected_id = st.selectbox(
    "대화 선택", ids, format_func=room_label, key="selected_id",
)
pending = st.session_state.get("pending")

# ① 예약 → ② 메시지 전송 → ③ 다른 대화 선택 → ④ 원래 대화에서 재시도
if st.button("실습: 다음 저장 한 번 실패시키기", disabled=pending is not None):
    st.session_state["fail_next_save"] = True
if st.session_state.get("fail_next_save"):
    st.info("실패가 예약되었습니다. 메시지를 입력하고 전송하세요.")

if pending is None:
    st.caption("저장 대기 없음 · pending = None")
else:
    st.caption("미확정 메시지 1건 · 저장 확인 전까지 새 입력을 잠급니다.")

text = st.chat_input("저장할 메시지를 입력하세요", disabled=pending is not None)
new_submission = False
if text and pending is None:
    cleaned = text.strip()
    if not cleaned or len(cleaned) > 1000:
        st.warning("앞뒤 공백을 제거한 메시지는 1~1000자로 입력하세요.")
    else:
        st.session_state["pending"] = {
            "conversation_id": selected_id,
            "request_id": str(uuid4()),
            "content": cleaned,
        }
        new_submission = True

pending = st.session_state.get("pending")
retry = False
if pending:
    if pending["conversation_id"] != selected_id:
        st.warning("미확정 저장이 다른 대화에 있습니다. 원래 대화로 돌아가 확인하세요.")
    else:
        st.text("저장 확인 중인 메시지: " + pending["content"])
        retry = st.button("저장 확인/재시도")

if pending and pending["conversation_id"] == selected_id and (new_submission or retry):
    saved = api("POST", f"/conversations/{selected_id}/messages", {
        "content": pending["content"], "request_id": pending["request_id"],
    })
    # 성공 응답을 받은 경우에만 미확정 상태를 지운다.
    st.session_state["pending"] = None
    st.session_state["notice"] = (
        "저장을 확인했습니다. "
        + ("기존 저장 결과입니다." if saved["replayed"] else "새 기록입니다.")
    )
    st.rerun()

st.session_state["messages"] = []
st.session_state["messages"] = api("GET", f"/conversations/{selected_id}/messages")
st.write("저장된 메시지 수:", len(st.session_state["messages"]))
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.text(message["content"])