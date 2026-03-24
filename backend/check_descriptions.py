from app import create_app
from app.models.practice import PracticeProblem

app = create_app()
ctx = app.app_context()
ctx.push()

problems = PracticeProblem.query.filter(
    PracticeProblem.level.in_(['beginner', 'intermediate'])
).order_by(PracticeProblem.order_index).all()

for p in problems:
    print(f"=== ID:{p.id} | {p.title} ===")
    print(f"DESCRIPTION:\n{p.description or 'NONE'}")
    print(f"CONSTRAINTS: {p.constraints or 'NONE'}")
    print("TEST CASES:")
    for i, tc in enumerate(p.test_cases or [], 1):
        print(f"  TC{i}: input={repr(tc.get('input'))}  output={repr(tc.get('output'))}")
    print()

ctx.pop()
