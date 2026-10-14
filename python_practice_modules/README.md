# Python 기초 실습

Python 3.6 이상이 필요하며 외부 패키지는 필요하지 않습니다.

## 실행 방법

C:\AIO4에서 다음 중 하나를 실행하세요.

```powershell
python python_practice.py
python -m python_practice_modules
python python_practice_modules/main.py
```

이 폴더 안에서는 다음 명령으로 실행할 수 있습니다.

```powershell
python main.py
```

메뉴에서 1~5를 선택하면 실습을 실행합니다. Enter를 누르면 메뉴로 돌아오고,
0을 입력하면 종료합니다. 정수가 아닌 입력은 다시 입력받습니다.

## 파일 역할

| 파일 | 역할 |
| --- | --- |
| main.py | 실습 메뉴와 실행 / 종료 처리 |
| __main__.py | python -m python_practice_modules 실행 진입점 |
| exercises/input_utils.py | 공통 정수 입력 함수 |
| exercises/addition.py | 변수와 덧셈 |
| exercises/pass_fail.py | 조건문과 합격 판정 |
| exercises/even_numbers.py | 리스트와 짝수 출력 |
| exercises/multiplication_table.py | 중첩 반복문과 구구단 |
| exercises/guessing_game.py | 난수를 사용하는 숫자 맞추기 게임 |

각 실습 파일의 주석에 있는 추가 과제를 따라 코드를 수정한 뒤 메뉴에서 실행하세요.
공통 입력 함수는 각 모듈에서 import하여 재사용합니다.
