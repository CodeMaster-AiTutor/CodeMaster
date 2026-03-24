from app import create_app
from app.models.practice import PracticeProblem

app = create_app()
ctx = app.app_context()
ctx.push()

problems = PracticeProblem.query.filter(
    PracticeProblem.level.in_(['beginner', 'intermediate'])
).order_by(PracticeProblem.order_index).all()

for p in problems:
    print('ID:%s | %s | %s' % (p.id, p.level, p.title))
    for i, tc in enumerate(p.test_cases or [], 1):
        inp = tc.get('input', '')
        out = tc.get('output', '')
        print('  TC%d: input=%s | output=%s' % (i, repr(inp), repr(out)))
    print()

ctx.pop()
