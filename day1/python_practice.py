"""Python 기초 실습 모음.

실행: python python_practice.py
실습할 번호를 선택하세요. 각 함수의 코드를 수정하며 연습할 수 있습니다.
"""

import random


def read_integer(message):
    """정수가 아닌 값을 입력하면 다시 입력받습니다."""
    while True:
        try:
            return int(input(message))
        except ValueError:
            print("정수를 입력하세요.")


def practice_addition():
    # 실습 1: 변수, 덧셈, print()
    # 추가 연습: 두 변수의 값을 바꾸고 뺄셈, 곱셈도 출력해 보세요.
    number1 = 100
    number2 = 200
    print("number1 + number2 =", number1 + number2)


def practice_pass_fail():
    # 실습 2: input(), int(), if/else, 비교 연산자
    # 추가 연습: 80점 이상이면 '우수'를 출력하도록 조건을 추가해 보세요.
    score = read_integer("점수를 입력하세요: ")
    if score >= 60:
        print("합격")
    else:
        print("불합격")


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


def practice_multiplication_table():
    # 실습 4: 중첩 for문, f-string, 탭(\t), 줄바꿈(\n)
    # 추가 연습: range()의 범위를 수정하여 원하는 단만 출력해 보세요.
    print("[2~4단: 각 단의 1~4까지]")
    for dan in range(2, 5):
        for i in range(1, 5):
            print(f"{dan} X {i} = {dan * i}", end="\t")
        print("\n=========================")

    print("\n[전체 구구단: 2~9단]")
    for multiplier in range(1, 10):
        for dan in range(2, 10):
            print(f"{dan} X {multiplier} = {dan * multiplier}", end="\t")
        print()


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


def main():
    practices = {
        1: practice_addition,
        2: practice_pass_fail,
        3: practice_even_numbers,
        4: practice_multiplication_table,
        5: practice_guessing_game,
    }

    while True:
        print("\n===== Python 기초 실습 =====")
        print("1. 변수와 덧셈")
        print("2. 합격 / 불합격 판정")
        print("3. 리스트에 저장하고 짝수 출력")
        print("4. 구구단 출력")
        print("5. 숫자 맞추기 게임")
        print("0. 종료")
        choice = read_integer("실습 번호: ")

        if choice == 0:
            print("실습을 종료합니다.")
            break
        if choice in practices:
            print()
            practices[choice]()
            input("\nEnter를 누르면 메뉴로 돌아갑니다.")
        else:
            print("0~5 중에서 선택하세요.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n실습을 종료합니다.")
