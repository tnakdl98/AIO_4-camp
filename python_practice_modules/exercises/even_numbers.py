"""실습 3: 리스트와 짝수 출력."""

from .input_utils import read_integer


def practice_even_numbers():
    # 실습 3: 리스트, append(), for, range(), 나머지 연산자 %
    # 추가 연습: 홀수 출력 또는 입력한 숫자들의 합계 출력을 추가해 보세요.
    scores = []
    for i in range(5):
        score = read_integer(f"{i + 1}: 숫자를 입력하세요: ")
        scores.append(score)

    print("입력한 숫자:", scores)
    print("짝수:")
    for number in scores:
        if number % 2 == 0:
            print(number)
