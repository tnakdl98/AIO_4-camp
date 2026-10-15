# 포함관계(in, not in)
# if role == 'admin' or role == 'manager' or role == 'staffe'

allowed_roles = ['admin', 'manager', 'staffe']
role = 'admin'

if role not in allowed_roles:
    print('접근 허용')
else:
    print('접근 불가')