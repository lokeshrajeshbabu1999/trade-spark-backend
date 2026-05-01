import base64
import os

encoded = b'='

decoded = base64.b64decode(encoded).decode('utf-8')
file_path = r'..\trade-spark\src\components\TradeModal.tsx'
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(decoded)
print('Updated TradeModal.tsx')
