"""08장 메모리 저장소: 서버 재시작 시 데이터가 사라진다."""
from .models import MemberOut, TaskCreate

members: dict[int, dict] = {}
tasks: dict[int, dict] = {}
_next_member_id = 1
_next_task_id = 1


def reset() -> None:
    global _next_member_id, _next_task_id
    members.clear()
    tasks.clear()
    _next_member_id = 1
    _next_task_id = 1


def add_member(member: MemberOut) -> dict:
    members[member.id] = member.model_dump(mode='json')
    return members[member.id]


def next_member_id() -> int:
    global _next_member_id
    value = _next_member_id
    _next_member_id += 1
    return value


def add_task(task: TaskCreate) -> dict:
    task_id = next_task_id()
    record = {'id': task_id, **task.model_dump(mode='json')}
    tasks[task_id] = record
    return record


def next_task_id() -> int:
    global _next_task_id
    value = _next_task_id
    _next_task_id += 1
    return value