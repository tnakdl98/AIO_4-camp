# 리스트에서 불량을 모두 지우고 정상만 남게
items = ['정상', '불량', '불량', '정상']
# for item in items:
#     if item == '불량':
#         items.remove('불량')

result = [item for item in items if item != '불량']

print(f"검수 결과 : {result}")