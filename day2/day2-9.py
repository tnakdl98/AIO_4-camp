# what          : 무엇을 만들지
# Consistants   : 어떤 제약으로 동작해야 하는지
# How           : 구현은 어떻게
# Vibe Check    : 결과를 검증
# 3대 핵심 룰 P(Prompt) -> G(Generator) -> V(Validator)
# P(Prompt) : 입력(input), 출력(output), 알고리즘 제약 조건, 함수 명시
# validator : 결과검증, 테스트케이스 검증

# 1부터 N까지의 짝수 합과 개수 구하기
# Bad : 짝수 합 구해줘

'''
[problem] 1부터 n까지의 정수 중 짝수들의 합과 짝수의 총 개수를 계산한다.
[Function] calculate_even_sum_and_count(n)
[Rules]
    - n이 1미만인 경우 합 0, 개수 0을 반환할 것
    - for문과 if문을 활용하여 짝수(i % 2 == 0)를 판단할 것
[Output]    {"Sum" : int, "Count" : int}
'''

# 실습 규칙
'''
문제정의/ 입력값/ 출력값/ 제약조건을 작성
assert함수를 활용하여 테스트 케이스
'''