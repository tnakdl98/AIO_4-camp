"""실제 API 호출 없이 main4의 스트리밍 상태 전이를 검증한다."""
from pathlib import Path
from types import SimpleNamespace as NS
from streamlit.testing.v1 import AppTest


class Stream:
    def __init__(self, events):
        self.events = events

    def __enter__(self):
        return iter(self.events)

    def __exit__(self, *args):
        return False


class Responses:
    def __init__(self):
        self.calls = []
        self.mode = 'success'

    def create(self, **kwargs):
        self.calls.append(kwargs)
        events = [NS(type='response.output_text.delta', delta='서울 여행 ')]
        if self.mode == 'success':
            events += [NS(type='response.output_text.delta', delta='추천입니다.'),
                       NS(type='response.completed', response=NS(usage=None))]
        elif self.mode in ('response.failed', 'response.incomplete'):
            events += [NS(type=self.mode)]
        elif self.mode == 'empty':
            events = [NS(type='response.completed', response=NS(usage=None))]
        return Stream(events)


def test_pending_retry_cancel():
    responses = Responses()
    at = AppTest.from_file(str(Path(__file__).with_name('main4.py')), default_timeout=20).run()
    assert not at.exception
    at.session_state.client = NS(responses=responses)
    at.button(key='arm_failure').click().run()
    at.chat_input(key='question').set_value('서울 일정').run()
    assert not at.exception
    assert at.session_state.pending['partial'] == '서울 여행 '
    assert at.session_state.success_count == 0
    assert at.session_state.history == []
    assert not at.session_state.fail_next
    at.button(key='retry').click().run()
    assert not at.exception
    assert at.session_state.pending is None
    assert at.session_state.success_count == 1
    assert len(at.session_state.history) == 2
    assert responses.calls[0]['input'] == responses.calls[1]['input']
    for mode in ['truncated', 'response.failed', 'response.incomplete', 'empty']:
        responses.mode = mode
        at.chat_input(key='question').set_value('다음 일정').run()
        assert not at.exception
        assert at.session_state.pending is not None
        assert len(at.session_state.history) == 2
        assert at.session_state.success_count == 1
        assert responses.calls[-1]['input'] == at.session_state.history + [
            {'role': 'user', 'content': '다음 일정'}]
        at.button(key='cancel').click().run()
        assert at.session_state.pending is None
        assert at.session_state.success_count == 1
    at.button(key='reset').click().run()
    assert not at.exception
    assert at.session_state.history == []
    assert at.session_state.success_count == 0
