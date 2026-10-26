"""실습 메뉴. 이 파일을 직접 실행하거나 패키지로 실행할 수 있습니다."""

if __package__:
    from .exercises.addition import practice_addition
    from .exercises.pass_fail import practice_pass_fail
    from .exercises.even_numbers import practice_even_numbers
    from .exercises.multiplication_table import practice_multiplication_table
    from .exercises.guessing_game import practice_guessing_game
    from .exercises.input_utils import read_integer
else:
    from exercises.addition import practice_addition
    from exercises.pass_fail import practice_pass_fail
    from exercises.even_numbers import practice_even_numbers
    from exercises.multiplication_table import practice_multiplication_table
    from exercises.guessing_game import practice_guessing_game
    from exercises.input_utils import read_integer


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


def run():
    """종료 입력과 Ctrl+C를 처리하며 메뉴를 실행합니다."""
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n실습을 종료합니다.")


if __name__ == "__main__":
    run()
