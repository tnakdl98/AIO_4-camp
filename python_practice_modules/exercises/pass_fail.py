"""실습 2: 합격 / 불합격 판정."""

from .input_utils import read_integer


def practice_pass_fail():
    # 실습 2: input(), int(), if/else, 비교 연산자
    # 추가 연습: 80점 이상이면 '우수'를 출력하도록 조건을 추가해 보세요.
    score = read_integer("점수를 입력하세요: ")
    if score >= 60:
        print("합격")
    else:
        print("불합격")
