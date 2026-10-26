
from fastapi.testclient import TestClient
from main import app, tasks

client = TestClient(app)


# ==========================================
# 1. POST - 데이터 생성 확장 테스트
# ==========================================

# 1-1. 중복 ID 생성 방지
def test_create_duplicate_id():
    tasks.clear()
    tasks.append({
        "id": 1, "name": "홍길동", "message": "동해번쩍"
    })

    response = client.post("/tasks", json={
        "id": 1, "name": "이순신", "message": "거북선"
    })

    assert response.status_code == 409
    assert response.json()["detail"] == "Task ID already exists"
    assert len(tasks) == 1


# 1-2. ID가 0인 경우
def test_create_id_zero():
    tasks.clear()

    response = client.post("/tasks", json={
        "id": 0, "name": "홍길동", "message": "동해번쩍"
    })

    assert response.status_code == 422
    assert len(tasks) == 0


# 1-3. ID가 음수인 경우
def test_create_negative_id():
    tasks.clear()

    response = client.post("/tasks", json={
        "id": -1, "name": "홍길동", "message": "동해번쩍"
    })

    assert response.status_code == 422
    assert len(tasks) == 0


# 1-4. name이 빈 문자열인 경우
def test_create_empty_name():
    tasks.clear()

    response = client.post("/tasks", json={
        "id": 1, "name": "", "message": "동해번쩍"
    })

    assert response.status_code == 422
    assert len(tasks) == 0


# 1-5. message가 빈 문자열인 경우
def test_create_empty_message():
    tasks.clear()

    response = client.post("/tasks", json={
        "id": 1, "name": "홍길동", "message": ""
    })

    assert response.status_code == 422
    assert len(tasks) == 0


# 1-6. 필수 필드 누락
def test_create_missing_field():
    tasks.clear()

    response = client.post("/tasks", json={
        "id": 1, "name": "홍길동"
    })

    assert response.status_code == 422
    assert len(tasks) == 0


# 1-7. ID에 문자열 입력
def test_create_invalid_id():
    tasks.clear()

    response = client.post("/tasks", json={
        "id": "abc", "name": "홍길동", "message": "동해번쩍"
    })

    assert response.status_code == 422
    assert len(tasks) == 0


# ==========================================
# 2. GET - 데이터 조회 확장 테스트
# ==========================================

# 2-1. 데이터가 없는 경우 전체 조회
def test_get_empty_tasks():
    tasks.clear()

    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == []


# 2-2. 여러 데이터 전체 조회
def test_get_multiple_tasks():
    tasks.clear()
    tasks.append({
        "id": 1, "name": "홍길동", "message": "동해번쩍"
    })
    tasks.append({
        "id": 2, "name": "이순신", "message": "거북선"
    })

    response = client.get("/tasks")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["id"] == 1
    assert response.json()[1]["id"] == 2


# 2-3. 존재하지 않는 ID 조회
def test_get_invalid_task():
    tasks.clear()

    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


# 2-4. 문자열 ID로 조회
def test_get_string_id():
    tasks.clear()

    response = client.get("/tasks/abc")

    assert response.status_code == 422


# ==========================================
# 3. PUT - 전체 수정 확장 테스트
# ==========================================

# 3-1. 존재하지 않는 데이터 수정
def test_put_not_found():
    tasks.clear()

    response = client.put("/tasks/999", json={
        "id": 999, "name": "홍길동", "message": "수정"
    })

    assert response.status_code == 404
    assert len(tasks) == 0


# 3-2. URL ID와 요청 데이터 ID 불일치
def test_put_id_mismatch():
    tasks.clear()
    tasks.append({
        "id": 1, "name": "홍길동", "message": "동해번쩍"
    })

    response = client.put("/tasks/1", json={
        "id": 2, "name": "이순신", "message": "거북선"
    })

    assert response.status_code == 400
    assert response.json()["detail"] == "Task ID mismatch"
    assert tasks[0]["id"] == 1
    assert tasks[0]["name"] == "홍길동"


# 3-3. PUT 필수 필드 누락
def test_put_missing_field():
    tasks.clear()
    tasks.append({
        "id": 1, "name": "홍길동", "message": "동해번쩍"
    })

    response = client.put("/tasks/1", json={
        "id": 1, "name": "이순신"
    })

    assert response.status_code == 422
    assert tasks[0]["message"] == "동해번쩍"


# 3-4. PUT 전체 데이터 교체
def test_put_replace_all():
    tasks.clear()
    tasks.append({
        "id": 1, "name": "홍길동", "message": "동해번쩍"
    })

    response = client.put("/tasks/1", json={
        "id": 1, "name": "이순신", "message": "거북선"
    })

    assert response.status_code == 200
    assert response.json() == {
        "id": 1, "name": "이순신", "message": "거북선"
    }
    assert len(tasks) == 1


# ==========================================
# 4. PATCH - 부분 수정 확장 테스트
# ==========================================

# 4-1. name만 수정
def test_patch_name_only():
    tasks.clear()
    tasks.append({
        "id": 1, "name": "홍길동", "message": "동해번쩍"
    })

    response = client.patch("/tasks/1", json={
        "name": "이순신"
    })

    assert response.status_code == 200
    assert response.json()["name"] == "이순신"
    assert response.json()["message"] == "동해번쩍"


# 4-2. message만 수정
def test_patch_message_only():
    tasks.clear()
    tasks.append({
        "id": 1, "name": "홍길동", "message": "동해번쩍"
    })

    response = client.patch("/tasks/1", json={
        "message": "서해번쩍"
    })

    assert response.status_code == 200
    assert response.json()["name"] == "홍길동"
    assert response.json()["message"] == "서해번쩍"


# 4-3. name과 message 동시 수정
def test_patch_multiple_fields():
    tasks.clear()
    tasks.append({
        "id": 1, "name": "홍길동", "message": "동해번쩍"
    })

    response = client.patch("/tasks/1", json={
        "name": "이순신",
        "message": "거북선"
    })

    assert response.status_code == 200
    assert response.json()["name"] == "이순신"
    assert response.json()["message"] == "거북선"


# 4-4. 존재하지 않는 데이터 수정
def test_patch_not_found():
    tasks.clear()

    response = client.patch("/tasks/999", json={
        "name": "이순신"
    })

    assert response.status_code == 404


# 4-5. 빈 문자열로 수정 시도
def test_patch_empty_name():
    tasks.clear()
    tasks.append({
        "id": 1, "name": "홍길동", "message": "동해번쩍"
    })

    response = client.patch("/tasks/1", json={
        "name": ""
    })

    assert response.status_code == 422
    assert tasks[0]["name"] == "홍길동"


# 4-6. 빈 JSON으로 PATCH 요청
def test_patch_empty_payload():
    tasks.clear()
    tasks.append({
        "id": 1, "name": "홍길동", "message": "동해번쩍"
    })

    response = client.patch("/tasks/1", json={})

    assert response.status_code == 200
    assert response.json() == {
        "id": 1, "name": "홍길동", "message": "동해번쩍"
    }


# 4-7. PATCH에서 명시적 null 입력 방지
def test_patch_null_name():
    tasks.clear()
    tasks.append({
        "id": 1, "name": "홍길동", "message": "동해번쩍"
    })

    response = client.patch("/tasks/1", json={
        "name": None
    })

    assert response.status_code == 422
    assert tasks[0]["name"] == "홍길동"


# ==========================================
# 5. DELETE - 삭제 확장 테스트
# ==========================================

# 5-1. 존재하지 않는 데이터 삭제
def test_delete_not_found():
    tasks.clear()

    response = client.delete("/tasks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


# 5-2. 삭제 후 다시 조회
def test_delete_then_get():
    tasks.clear()
    tasks.append({
        "id": 1, "name": "홍길동", "message": "동해번쩍"
    })

    delete_response = client.delete("/tasks/1")
    get_response = client.get("/tasks/1")

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert get_response.status_code == 404
    assert len(tasks) == 0


# 5-3. 여러 데이터 중 하나만 삭제
def test_delete_one_of_multiple():
    tasks.clear()
    tasks.append({
        "id": 1, "name": "홍길동", "message": "동해번쩍"
    })
    tasks.append({
        "id": 2, "name": "이순신", "message": "거북선"
    })

    response = client.delete("/tasks/1")

    assert response.status_code == 204
    assert len(tasks) == 1
    assert tasks[0]["id"] == 2


# 5-4. 동일 데이터 두 번 삭제
def test_delete_twice():
    tasks.clear()
    tasks.append({
        "id": 1, "name": "홍길동", "message": "동해번쩍"
    })

    first = client.delete("/tasks/1")
    second = client.delete("/tasks/1")

    assert first.status_code == 204
    assert second.status_code == 404
    assert len(tasks) == 0


# ==========================================
# 6. CRUD - 전체 흐름 통합 테스트
# ==========================================

# 6-1. 생성 -> 조회 -> PUT -> PATCH -> 삭제
def test_crud_full_flow():
    tasks.clear()

    # CREATE
    create = client.post("/tasks", json={
        "id": 1, "name": "홍길동", "message": "동해번쩍"
    })

    assert create.status_code == 201

    # READ
    read = client.get("/tasks/1")

    assert read.status_code == 200
    assert read.json()["name"] == "홍길동"

    # PUT
    put = client.put("/tasks/1", json={
        "id": 1, "name": "이순신", "message": "거북선"
    })

    assert put.status_code == 200
    assert put.json()["name"] == "이순신"

    # PATCH
    patch = client.patch("/tasks/1", json={
        "message": "한산도 대첩"
    })

    assert patch.status_code == 200
    assert patch.json()["name"] == "이순신"
    assert patch.json()["message"] == "한산도 대첩"

    # DELETE
    delete = client.delete("/tasks/1")

    assert delete.status_code == 204

    # 삭제 후 조회
    read_again = client.get("/tasks/1")

    assert read_again.status_code == 404
    assert len(tasks) == 0
