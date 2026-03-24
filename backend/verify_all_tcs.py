import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app import create_app
from app.models.practice import PracticeProblem

app = create_app()
ctx = app.app_context()
ctx.push()

problems = PracticeProblem.query.order_by(PracticeProblem.order_index).all()

for p in problems:
    print(f"ID:{p.id} | {p.level} | {p.title}")
    for i, tc in enumerate(p.test_cases or [], 1):
        print(f"  TC{i}: input={repr(tc.get('input'))}  output={repr(tc.get('output'))}")
    print()

ctx.pop()
