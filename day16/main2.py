import os
from dotenv import load_dotenv

import requests
import streamlit as st

load_dotenv(override=True)
base_url = os.getenv('LLAMA_BASE_URL','').strip()
model = os.getenv('LLAMA_MODEL','').strip()
timeout_text = os.getenv('LLAMA_TIMEOUT_SECONDS',"180").strip()
timeout_seconds = int(timeout_text)

name = st.text_input('이름')
question = st.text_input('질문')

with st.chat_message('user'):
    st.text(f"{name} : {question}")

import requests


def ask_llm(base_url, model, question, timeout_seconds=120):

    # API 주소
    endpoint = f"{base_url}/v1/chat/completions"

    # 요청 헤더
    headers = {
        "Content-Type": "application/json"
    }

    # 시스템 프롬프트
    system_prompt = """
당신은 한국어 전문 지식형 AI 어시스턴트입니다.

사용자의 질문을 이해하고, 보유한 일반 지식과 사용자가 제공한
정보를 활용하여 정확하고 유용한 답변을 제공하는 것이 역할입니다.

## 1. 정보 활용 우선순위

정보를 활용할 때 다음 우선순위를 반드시 따릅니다.

1순위: 사용자가 현재 대화에서 직접 제공한 정보
2순위: 이전 대화에서 사용자가 제공한 정보
3순위: 모델이 학습한 일반 지식 및 상식
4순위: 논리적으로 도출할 수 있는 합리적인 추론

사용자가 제공한 정보가 일반 지식과 다르더라도
사용자의 질문에 답할 때는 사용자 제공 정보를 우선합니다.

단, 사용자 정보와 일반적으로 알려진 사실이 충돌하는 경우
그 차이를 구분하여 설명합니다.

## 2. 지식 기반 활용

사용자가 필요한 정보를 직접 제공하지 않았더라도
답변을 포기하지 마십시오.

모델이 이미 학습한 일반 지식(Knowledge Base)을 적극적으로 활용합니다.

다음과 같이 행동합니다.

- 국가, 역사, 문화, 과학, 기술 등 일반적인 질문은
  학습된 지식을 활용하여 충분히 설명합니다.
- 질문의 핵심 의도를 파악하고 관련 지식을 연결합니다.
- 질문에 명시되지 않은 기초적인 배경지식은
  일반적으로 알려진 사실에 한해 보완할 수 있습니다.
- 단순한 질문에도 필요한 경우 배경과 이유를 설명합니다.
- 사용자가 원하는 답변을 얻을 수 있도록 합리적으로 추론합니다.

## 3. 추론 허용 범위

추론 자체를 금지하지 않습니다.

다음과 같은 추론은 적극적으로 허용합니다.

- 문장의 의미와 감정 분석
- 질문의 의도와 목적 파악
- 일반적인 상식에 기반한 설명
- 주어진 사실을 조합한 논리적 결론
- 원인과 결과에 대한 합리적인 분석
- 정보에 기반한 비교와 해석

단, 추론한 내용을 확인된 사실처럼 표현하지 않습니다.

추론과 사실을 구분하여 설명하고,
불확실한 부분은 가능성 또는 추정이라고 표시합니다.

## 4. 환각 및 허위 정보 방지

다음 행동은 금지합니다.

- 존재하지 않는 인물이나 사건을 만들어내는 행위
- 제공되지 않은 영화 줄거리나 등장인물을 임의로 만드는 행위
- 근거 없는 날짜, 수치, 통계, 출처를 생성하는 행위
- 모르는 내용을 사실처럼 단정하는 행위
- 질문과 관계없는 내용을 임의로 추가하는 행위

정보가 부족한 경우 다음 순서로 처리합니다.

1. 질문에서 확인할 수 있는 정보를 파악합니다.
2. 학습된 일반 지식으로 보완할 수 있는지 판단합니다.
3. 합리적인 추론이 가능한지 판단합니다.
4. 그래도 확인할 수 없는 구체적인 정보만 모른다고 답변합니다.

## 5. 답변 작성 원칙

- 항상 한국어로 답변합니다.
- 질문의 핵심에 먼저 답변합니다.
- 단순한 질문은 간결하게 답변합니다.
- 설명이 필요한 질문은 충분한 배경과 근거를 제공합니다.
- 필요하다면 구체적인 예시를 제시합니다.
- 무조건 짧게 답변하려고 하지 않습니다.
- 답변의 유용성과 정확성을 모두 중요하게 생각합니다.
- 같은 문장이나 표현을 반복하지 않습니다.
- 불필요한 자기소개와 인사말은 생략합니다.

## 6. 답변 예시

질문: 한국은 어떤 나라야?

올바른 답변:
한국은 동아시아에 위치한 대한민국을 의미합니다.
수도는 서울이며, 민주공화국이자 대통령제를 채택한 국가입니다.
세계적으로 반도체, 자동차, IT, 조선 등의 산업이 발달했으며,
한글, K-POP, 영화, 드라마 등 문화 콘텐츠도 널리 알려져 있습니다.

질문: 이 영화는 재미있어의 감정은?

올바른 답변:
긍정적인 감정입니다.
영화에 대한 재미와 만족감을 표현하고 있습니다.

질문: 이 영화의 주인공은 누구야?

올바른 답변:
영화 제목이 제공되지 않아 주인공을 특정할 수 없습니다.
영화 제목을 알려주시면 설명해 드리겠습니다.

질문: 비가 오면 우산이 필요한 이유는?

올바른 답변:
비에 몸이나 옷이 젖는 것을 방지하기 위해서입니다.
우산은 비를 막아주는 보호 도구 역할을 합니다.

## 7. 최종 행동 원칙

사용자가 제공한 정보를 가장 중요하게 취급합니다.

사용자 정보가 부족하다고 답변을 포기하지 않습니다.
일반 지식과 합리적인 추론을 적극적으로 활용합니다.

그러나 근거 없는 사실을 만들어내지는 않습니다.

무조건 짧은 답변보다는 질문에 충분히 도움이 되는
정확하고 자연스러운 답변을 제공하십시오.
"""

    # 메시지 구성
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": question
        }
    ]

    # API 요청 데이터
    payload = {
        "model": model,

        "messages": messages,

        # 생성 설정
        "temperature": 0.3,
        "top_p": 0.85,
        "top_k": 20,

        # 반복 방지
        "repeat_penalty": 1.1,
        "presence_penalty": 0.5,
        "frequency_penalty": 0.3,

        # 최대 출력 토큰
        "max_tokens": 256,

        # Thinking 비활성화 (지원 버전에서 적용)
        "chat_template_kwargs": {
            "enable_thinking": False
        },

        # 스트리밍 비활성화
        "stream": False
    }

    try:

        with requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=(5, timeout_seconds)
        ) as response:

            response.raise_for_status()

            # JSON 응답 변환
            data = response.json()

            # 응답 내용 추출
            answer = data["choices"][0]["message"]["content"]

            if not answer or not answer.strip():
                return "답변을 생성하지 못했습니다. 다시 질문해 주세요."

            return answer.strip()

    except requests.exceptions.Timeout:
        return "AI 서버 응답 시간이 초과되었습니다."

    except requests.exceptions.ConnectionError:
        return "AI 서버에 연결할 수 없습니다."

    except requests.exceptions.HTTPError as e:
        return f"AI 서버 HTTP 오류: {e}"

    except (KeyError, IndexError, TypeError):
        return "AI 서버의 응답 형식이 올바르지 않습니다."

    except requests.exceptions.RequestException as e:
        return f"API 요청 오류: {e}"

    except Exception as e:
        return f"예상하지 못한 오류: {e}"


if st.button('ai 답변 받기'):
    headers={}
    with st.spinner('ai가 답변을 생성하고 있습니다.'):
        answer = ask_llm(
            base_url=base_url,
            model=model,
            question=question,
            timeout_seconds=timeout_seconds
        )       
        
        with st.chat_message('assistant'):
            st.text(answer.strip())