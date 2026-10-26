names = ['홍길동', '이순신', '강감찬']

# id = 1
# for name in names:
#     print(f'{id}.{name}')
#     id += 1

# for id, name in enumerate(names, start = 1):
#     print(id, name)

raw_logs = [
    "epoch=1,loss=0.45,acc=88.5",
    "epoch=2,loss=invalid,acc=91.0",
    "epoch=3,loss=0.31", 
    "epoch=4,loss=0.22,acc=94.2",
]

for line in raw_logs:
    parts = dict(item.split("=") for item in line.split(','))

    try:
        record = {
            "epoch": int(parts["epoch"]),
            "loss": float(parts["loss"]),
            "acc": float(parts["acc"]),
            }
        print(record)
    except ValueError as e:
        print("값이 잘못되었습니다",e)

    except KeyError as e:
        print('키값을 확인하세요',e)

# int('abc')        ValueError
# dict_1 = {}
# dict_1['abc']     KeyError