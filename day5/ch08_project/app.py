"""08장 종합: FastAPI 회원·작업 관리 CRUD. 실행: uvicorn ch08_project.app:app --reload"""
from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import ValidationError

from . import store
from .models import MemberCreate, MemberOut, TaskCreate, TaskOut, TaskPatch

app = FastAPI(title='Pydantic 최종 실습 - 회원 및 작업 관리', version='1.0.0')


def get_member_or_404(member_id: int) -> dict:
    member = store.members.get(member_id)
    if member is None:
        raise HTTPException(status_code=404, detail='회원이 존재하지 않습니다')
    return member


def get_task_or_404(task_id: int) -> dict:
    task = store.tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail='작업이 존재하지 않습니다')
    return task


@app.get('/')
def home() -> dict[str, str]:
    return {'message': 'Pydantic 최종 프로젝트입니다. /docs를 방문하세요.'}


@app.post('/members', response_model=MemberOut, status_code=status.HTTP_201_CREATED)
def create_member(payload: MemberCreate) -> dict:
    if any(m['email'] == str(payload.email) for m in store.members.values()):
        raise HTTPException(status_code=409, detail='이메일이 이미 사용 중입니다')
    member = MemberOut(id=store.next_member_id(), **payload.model_dump())
    return store.add_member(member)


@app.get('/members', response_model=list[MemberOut])
def list_members() -> list[dict]:
    return list(store.members.values())


@app.get('/members/{member_id}', response_model=MemberOut)
def read_member(member_id: int) -> dict:
    return get_member_or_404(member_id)


@app.post('/tasks', response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate) -> dict:
    get_member_or_404(payload.owner_id)
    return store.add_task(payload)


@app.get('/tasks', response_model=list[TaskOut])
def list_tasks(
    owner_id: int | None = Query(default=None, gt=0),
    done: bool | None = None,
) -> list[dict]:
    results = list(store.tasks.values())
    if owner_id is not None:
        results = [record for record in results if record['owner_id'] == owner_id]
    if done is not None:
        results = [record for record in results if record['done'] == done]
    return results


@app.get('/tasks/{task_id}', response_model=TaskOut)
def read_task(task_id: int) -> dict:
    return get_task_or_404(task_id)


@app.patch('/tasks/{task_id}', response_model=TaskOut)
def patch_task(task_id: int, payload: TaskPatch) -> dict:
    record = get_task_or_404(task_id)
    changes = payload.model_dump(exclude_unset=True, mode='json')
    # 모델 수준의 일관성을 보장하기 위해 합친 데이터를 전체 모델로 다시 검증한다.
    # title/done/priority에 명시적인 null이 오면 TaskCreate가 거부한다.
    try:
        validated = TaskCreate.model_validate({**{key: value for key, value in record.items() if key != 'id'}, **changes})
    except ValidationError as error:
        # 일반적으로 FastAPI의 입력 모델 검증에서 422가 발생한다.
        # 병합 결과 오류에 대해서도 명시적으로 422로 변환한다.
        raise HTTPException(
            status_code=422,
            detail=[{'loc': list(e['loc']), 'msg': e['msg'], 'type': e['type']}
                    for e in error.errors()],
        ) from error
    updated = {'id': task_id, **validated.model_dump(mode='json')}
    store.tasks[task_id] = updated
    return updated


@app.delete('/tasks/{task_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int) -> Response:
    get_task_or_404(task_id)
    del store.tasks[task_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)