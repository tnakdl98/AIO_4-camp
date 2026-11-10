"""1차시: 사내 IT 문의를 처리할 수 있는 답변 초안을 만든다."""
import os
from dotenv import load_dotenv
from openai import APIError, OpenAI


load_dotenv(override=False, interpolate=False)
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


def main():
    if not os.getenv("GROQ_API_KEY", "").strip() or not MODEL:
        print(".env에 GROQ_API_KEY와 GROQ_MODEL을 입력하세요.")
        return
    question = input("IT 문의: ").strip()
    if not question or len(question) > 1000:
        print("문의는 1~1000자로 입력하세요.")
        return
    try:
        response = ask_groq(question)
    except APIError:
        print("Groq 호출 실패: 키, 모델 권한, 호출 한도를 확인하세요.")
        return
    except ValueError as exc:
        print(str(exc))
        return
    print("\n=== 상담 초안 ===")
    print(response.output_text)
    print("\n응답 ID:", response.id)
    print("완료 상태:", response.status)
    print("사용 모델:", MODEL)


if __name__ == "__main__":
    main()
