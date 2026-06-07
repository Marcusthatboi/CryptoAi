from backend.auto_trading import get_all_warnings
import json

warnings = get_all_warnings()
print(f'Total warnings: {len(warnings)}')
print()
for i, w in enumerate(warnings, 1):
    title = w.get('title', 'NO TITLE')
    severity = w.get('severity', 'UNKNOWN')
    print(f'{i}. [{severity}] {title}')
