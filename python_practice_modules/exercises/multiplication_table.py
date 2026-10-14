"""실습 4: 중첩 반복문과 구구단."""

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
