# zip

list_1 = ['a', 'b', 'c']
list_2 = [100, 200, 300]
result = zip(list_1, list_2)
for i in result:
    print(i)

# zip으로 생성한 객체를 dictionary 변환
result2 = dict(result)
print(result2)


# R I O C
# Role          : 역할
# Input         : 입력
# Output        : 출력
# Constraints   : 제약조건(어떤 알고리즘/규칙, 뭘 하지 말아야 하는지)

# 리스트 컴프리헨션
result = []

list_1 = ['1','2','3','4','5']

result = [int(i) for i in list_1 if int(i) > 3]

print(result)

menu = ['아메리카노', '라떼', '초코']
ice_menu = [ '아이스'+ i for i in menu]
len_menu = [len(i) for i in menu if len(i) % 2 == 0]

print(len_menu)

ages = [20, 15, 30 ,60, 25, 27, 45]
print([i for i in ages if i >= 20])
print(['성인' if i >= 20 else '미성년' for i in ages])

bad_words = ['바보', '멍충이','', '멍텅구리','', '멍충이']
words = sorted(set(word for word in bad_words if word), key=len, reverse=True)
print(words)

import re
pattern = "|".join(re.escape(word) for word in words)
print(pattern)

chat_message = '철수는 멍충이'
result = re.sub(pattern, lambda match: "*" * len(match.group(0)),
                  chat_message, flags=re.IGNORECASE)

print(result)