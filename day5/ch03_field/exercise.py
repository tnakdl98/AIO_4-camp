from pydantic import BaseModel, Field


class Product(BaseModel):
    # TODO title: 최소 2자, 최대 60자
    title : str = Field(min_length=2, max_length=60)
    # TODO price: 0보다 커야 함
    price : int = Field(gt=0)
    # TODO stock: 0 이상, 기본값 0
    stock : int = Field(ge=0, default=0)
    # TODO sku: SKU-와 숫자 네 자리 패턴
    sku : str = Field(pattern = r'^SKU-[0-9]{4}$')


def main() -> None:
    result = Product(title='football', price = '20', stock = '13', sku = 'SKU-0005')
    print(result.model_dump())


if __name__ == '__main__':
    main()