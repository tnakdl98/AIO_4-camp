"""실습 5: 숫자 맞추기 게임."""

import random

from .input_utils import read_integer


def practice_guessing_game():
    # 실습 5: random.randint(), while, if/elif/else, break
    # 추가 연습: 최대 시도 횟수를 정하거나 숫자 범위를 바꿔 보세요.
    com_num = random.randint(1, 100)
    count = 0
    print("컴퓨터가 고른 1~100 사이의 숫자를 맞춰 보세요.")

    while True:
        user_num = read_integer("1~100: ")
        if not 1 <= user_num <= 100:
            print("1~100 사이의 정수를 입력하세요.")
            continue

        count += 1
        if user_num > com_num:
            print("컴퓨터보다 큽니다.")
        elif user_num < com_num:
            print("컴퓨터보다 작습니다.")
        else:
            print(f"정답입니다! 총 시도 횟수: {count}")
            break
