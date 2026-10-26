
from fastapi.testclient import TestClient
from main import app, tasks

client = TestClient(app)


# 1. POST - 데이터 생성
def test_create_task():
    tasks.clear()

    response = client.post("/tasks", json={
        "id": 1,
        "name": "홍길동",
        "message": "동해번쩍"
    })

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "홍길동",
        "message": "동해번쩍"
    }


# 2. GET - 전체 조회
def test_get_tasks():
    tasks.clear()
    tasks.append({
        "id": 1,
        "name": "홍길동",
        "message": "동해번쩍"
    })

    response = client.get("/tasks")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "홍길동"


# 3. GET - 개별 조회
def test_get_task():
    tasks.clear()
    tasks.append({
        "id": 1,
        "name": "홍길동",
        "message": "동해번쩍"
    })

    response = client.get("/tasks/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["name"] == "홍길동"


# 4. PUT - 전체 수정
def test_put_task():
    tasks.clear()
    tasks.append({
        "id": 1,
        "name": "홍길동",
        "message": "동해번쩍"
    })

    response = client.put("/tasks/1", json={
        "id": 1,
        "name": "이순신",
        "message": "거북선"
    })

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "이순신",
        "message": "거북선"
    }


# 5. PATCH - 부분 수정
def test_patch_task():
    tasks.clear()
    tasks.append({
        "id": 1,
        "name": "홍길동",
        "message": "동해번쩍"
    })

    response = client.patch("/tasks/1", json={
        "message": "서해번쩍"
    })

    assert response.status_code == 200
    assert response.json()["message"] == "서해번쩍"

    # 수정하지 않은 필드는 유지
    assert response.json()["name"] == "홍길동"
    assert response.json()["id"] == 1


# 6. DELETE - 데이터 삭제
def test_delete_task():
    tasks.clear()
    tasks.append({
        "id": 1,
        "name": "홍길동",
        "message": "동해번쩍"
    })

    response = client.delete("/tasks/1")

    assert response.status_code == 204
    assert response.content == b""
    assert len(tasks) == 0


# 7. GET - 존재하지 않는 데이터
def test_get_not_found():
    tasks.clear()

    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Task not found"
    }
