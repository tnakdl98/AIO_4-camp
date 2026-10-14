"""공통 정수 입력 기능."""

def read_integer(message):
    """정수가 아닌 값을 입력하면 다시 입력받습니다."""
    while True:
        try:
            return int(input(message))
        except ValueError:
            print("정수를 입력하세요.")
