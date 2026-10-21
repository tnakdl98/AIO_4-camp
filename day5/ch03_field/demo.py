# Field 범위, 길이 패턴이 대해서 엄격하게 검사
from pydantic import BaseModel, Field, ValidationError, EmailStr, ConfigDict
from typing import Literal

class Registration(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    name : str = Field(min_length=2, max_length=20, description='설명')
    age : int = Field(ge = 14, le = 100)
    email : EmailStr
    level : Literal['basic', 'premium'] = 'basic'
    code : str = Field(pattern=r'^STU-[0-9]{4}$')       # r'^STU-[0-9]{4}$'(정규표현식) -> STU-0001
    agreed : bool = Field(strict=True)

def main() -> None:
    user1 = Registration(name = 'lee', age = 30, email='lee234@abc.com', code = 'STU-0001', agreed=True)
    print('검증성공', user1.model_dump())
    print('오류확인')

    try:
        user2 = Registration(name = 'lee', age = '500', email='lee234@abc', code = 'STU-001')
        print(user2.age)
    except Exception as e:
        for error in e.errors():
            print(error['loc'],error['type'])

if __name__ == '__main__':
    main()