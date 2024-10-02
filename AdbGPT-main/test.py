import re

step = 2
line = '2. [Long-tap] ["123"]'

# 使用 re.match 来匹配完整的模式
match = re.match(f"{step}\. \[([A-Za-z0-9.^_-]+)\]", line)

print(match)  # 如果匹配成功，返回 Match 对象；否则返回 None
