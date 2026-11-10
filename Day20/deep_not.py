students = [{
    "std_number" : "001",
    "info":{
        "name":"홍길동",
        "score":{
            'kor':100,'eng':98,'math':100
        },
        'address' : '서울시 강남구 대치동',
        'grade':1,    
        },
    },
    {
    "std_number" : "002",
    "info":{
        "name":"이순신",
        "score":{
            'kor':100,'eng':98,'math':100
        },
        'address' : '서울시 강남구 대치동',
        'grade':1,    
        }
    }
]

# 전달하는 의도는 값을 복사해서 즉 우리가 알고있는 복사본을 전달
def read_infomation(s):
    # 함수에서는 복사본이기 때문에.. 내부로직에따라 맘대로 수정하고 삭제하고. 등등. 
    scores = s[0]['info']['score']
    scores['kor'] += 50


read_infomation(students.copy())
print(students)