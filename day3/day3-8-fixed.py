# 수정: 등급별 할인율과 쿠폰 금액에 이름을 붙여 정책을 한곳에서 관리합니다.
# 등급의 실제 명칭은 정해지지 않았으므로 기존 번호 1, 2, 3을 유지합니다.
DISCOUNT_PERCENT_BY_GRADE = {1: 5, 2: 10, 3: 20}
COUPON_AMOUNT = 3000


def calc_order(u_type, price, qty, coupon):
    """등급 할인 후 쿠폰을 적용하고, 원 미만을 버린 결제 금액을 반환합니다.

    u_type: 등급 번호 1, 2, 3 중 하나
    price: 0 이상의 정수 가격(원)
    qty: 0 이상의 정수 수량
    coupon: bool 또는 YES/NO 문자열(대소문자와 앞뒤 공백 무시)

    자료형이 잘못되면 TypeError, 허용 범위를 벗어나면 ValueError를 발생시킵니다.
    """
    # 수정: bool은 Python에서 int의 하위 타입이므로 정확한 int 타입을 검사합니다.
    if type(u_type) is not int:
        raise TypeError("u_type은 정수 등급 번호여야 합니다.")
    if u_type not in DISCOUNT_PERCENT_BY_GRADE:
        raise ValueError("u_type은 1, 2, 3 중 하나여야 합니다.")

    # 수정: 음수 입력이 0원으로 감춰지거나 양수로 계산되지 않도록 먼저 검사합니다.
    # 가격은 정수 원 단위, 수량은 정수로 제한하며 기존처럼 0은 허용합니다.
    for name, value in (("price", price), ("qty", qty)):
        if type(value) is not int:
            raise TypeError(f"{name}는 정수여야 합니다.")
        if value < 0:
            raise ValueError(f"{name}는 0 이상이어야 합니다.")

    # 수정: 'yes', ' YES '도 인식하고, 오타를 쿠폰 미사용으로 넘기지 않습니다.
    if isinstance(coupon, bool):
        use_coupon = coupon
    elif isinstance(coupon, str):
        normalized_coupon = coupon.strip().upper()
        if normalized_coupon not in ("YES", "NO"):
            raise ValueError("coupon 문자열은 YES 또는 NO여야 합니다.")
        use_coupon = normalized_coupon == "YES"
    else:
        raise TypeError("coupon은 bool 또는 YES/NO 문자열이어야 합니다.")

    # 수정: float 대신 정수 비율로 계산해 부동소수점 오차를 피합니다.
    # 금액을 100배 한 상태에서 등급 할인 → 쿠폰 차감 순서를 유지합니다.
    discount_percent = DISCOUNT_PERCENT_BY_GRADE[u_type]
    total_scaled = price * qty * (100 - discount_percent)
    if use_coupon:
        total_scaled -= COUPON_AMOUNT * 100

    # 수정: 유효한 주문의 쿠폰 초과분만 0원 처리하고, 마지막에 원 미만을 버립니다.
    return max(total_scaled, 0) // 100


# 수정: 다른 파일에서 불러올 때 예제 실행과 출력이 발생하지 않게 분리합니다.
if __name__ == "__main__":
    result = calc_order(1, 100, 20, "yes")
    print(f"최종 결제 금액: {result}원")
