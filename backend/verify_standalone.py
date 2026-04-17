"""
Standalone verifier for advanced problems — no Flask required.
Imports _verify_output directly from practice.py by monkey-patching imports.
"""
import sys, re, types

# Stub out all Flask/DB dependencies so we can import just the verifier
flask_mod = types.ModuleType('flask')
class _FakeBP:
    def route(self, *a, **kw):
        return lambda f: f
    def __call__(self, *a, **kw):
        return self
flask_mod.Blueprint = lambda *a, **kw: _FakeBP()
flask_mod.jsonify = lambda *a, **kw: None
flask_mod.request = None
sys.modules['flask'] = flask_mod

for name in ['app', 'app.middleware', 'app.middleware.auth',
             'app.models', 'app.models.practice', 'app.models.skill_points',
             'app.routes', 'app.routes.profile',
             'app.services', 'app.services.java_executor',
             'app.services.skill_points_service']:
    m = types.ModuleType(name)
    sys.modules[name] = m

# Provide stubs for names used at module level
sys.modules['app'].db = None
sys.modules['app.middleware.auth'].token_required = lambda f: f
sys.modules['app.models.practice'].PracticeProblem = None
sys.modules['app.models.practice'].PracticeAttempt = None
sys.modules['app.models.practice'].PracticeDraft = None
sys.modules['app.models.skill_points'].SkillPointTransaction = None
sys.modules['app.routes.profile'].update_streak_on_submit = lambda *a: None
sys.modules['app.services.java_executor'].get_java_executor = lambda: None
sys.modules['app.services.skill_points_service'].award_monthly_goal_completion = lambda *a: None
sys.modules['app.services.skill_points_service'].award_practice_problem_points = lambda *a: None
sys.modules['app.services.skill_points_service'].award_weekly_goal_completion = lambda *a: None
sys.modules['app.services.skill_points_service'].get_practice_points = lambda *a: None

import importlib.util, pathlib
spec = importlib.util.spec_from_file_location(
    "practice_routes",
    pathlib.Path(__file__).parent / "app/routes/practice.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

verify = mod._verify_output

# Also grab test cases from seed_content
seed_spec = importlib.util.spec_from_file_location(
    "seed_content",
    pathlib.Path(__file__).parent / "seed_content.py"
)
seed_mod = importlib.util.module_from_spec(seed_spec)
# Patch seed_content imports
for name in ['app', 'app.models', 'app.models.practice']:
    if name not in sys.modules:
        sys.modules[name] = types.ModuleType(name)
sys.modules['app.models.practice'].PracticeProblem = None

# We just need the function, not the whole module
seed_src = open(pathlib.Path(__file__).parent / "seed_content.py").read()
# Extract just the build_problem_test_cases function from seed_content.py
# by finding where it starts and exec-ing only the relevant portion
import ast
seed_lines = seed_src.split('\n')
# Find the function def line
func_start = None
for i, line in enumerate(seed_lines):
    if line.startswith('def build_problem_test_cases'):
        func_start = i
        break

if func_start is None:
    raise RuntimeError("build_problem_test_cases not found in seed_content.py")

func_src = '\n'.join(seed_lines[func_start:])
seed_globals = {'__builtins__': __builtins__, 're': re}
exec(compile(func_src, 'seed_content.py', 'exec'), seed_globals)
build_tcs = seed_globals['build_problem_test_cases']

# ──────────────────────────────────────────────────────────────────────
# Test data: (title, correct_output, wrong_output)
# correct_output → should return True
# wrong_output   → should return False
# ──────────────────────────────────────────────────────────────────────

REJECT_TESTS = [
    # (title, input, wrong_output that should be rejected)
    # Using CURRENT seed_content test case inputs
    ("Student Management System",  "1\nAlice\n5", "Error occurred"),
    ("Library System",             "1\nBook1\n3", "Error occurred"),
    ("Contact Book",               "1\nAlice\n1234567890\n5", "Error occurred"),
    ("ATM Simulator",              "1234\n1\n4", "Error occurred"),
    ("Shopping Cart System",       "1\nApple\n50\n1\n5", "Error occurred"),
    ("Expense Tracker",            "1\nFood\nLunch\n100\n5", "Error occurred"),
    ("Quiz Application",           "B\nC\nB\nA\nB", "Score: 3/5"),
    ("Quiz Application",           "A\nA\nA\nA\nA", "Score: 5/5"),
    ("Voting System",              "V101\nAlice\n", "Error occurred"),
    ("Parking Lot System",         "1\nMH01AB1234\n4", "Error occurred"),     # exit='4'
    ("Bank Account System",        "1\nRaj\n5", "Error occurred"),             # exit='5'
    ("Password Validator",         "StrongPass1!", "Weak password"),
    ("Task Manager",               "1\nStudy\nHigh\n6", "Error occurred"),    # exit='6'
    ("Scoreboard System",          "1\nAlice\n95\n6", "Error occurred"),
    ("Inventory System",           "1\nApple\n5\n10.0\n5", "Error occurred"),
    ("Restaurant Billing System",  "1\nBurger\n50\n1\n4", "Error occurred"),
    ("Employee Management System", "1\nJohn\n5000\n5", "Error occurred"),
    ("Hotel Room Booking",         "2\n101\nAsha\n2\n5", "Error occurred"),   # exit='5'
    ("Stack Implementation (Manual)", "1\n10\n1\n20\n2\n5", "Popped: 10"),
    ("Queue Simulation",           "1\nReport.pdf\n2\n5", "Error occurred"),
    ("Mini Banking System",        "admin\n1\nAlice\n5", "Error occurred"),
    ("Course Enrollment System",   "1\nCS101\n30\n2\nS001\nCS101\n5", "Error occurred"),  # exit='5'
    ("Hostel Room Allocator",      "1\nAlice\nCS\n4", "Error occurred"),
    ("Supermarket Checkout",       "1\nBread\n2\n50\n5", "Error occurred"),
]

pass_fail = []
reject_fail = []

print("=== PASS TESTS (correct output must be accepted) ===")
problems_25 = [
    "Student Management System", "Library System", "Contact Book",
    "ATM Simulator", "Shopping Cart System", "Expense Tracker",
    "Quiz Application", "Voting System", "Parking Lot System",
    "Bank Account System", "Password Validator", "Task Manager",
    "Scoreboard System", "Inventory System", "Restaurant Billing System",
    "Employee Management System", "Hotel Room Booking",
    "Stack Implementation (Manual)", "Queue Simulation",
    "Mini Banking System", "Course Enrollment System",
    "Hostel Room Allocator", "Supermarket Checkout",
    "Number Guessing Game", "Simple Chat Application",
]

all_pass_ok = True
for title in problems_25:
    tcs = build_tcs(title)
    if not tcs:
        print(f"  MISSING test cases for: {title}")
        all_pass_ok = False
        continue
    for i, tc in enumerate(tcs, 1):
        inp = tc['input']
        exp = tc['output']
        result = verify(title, inp, exp, exp)
        status = "OK" if result else "FAIL"
        if not result:
            all_pass_ok = False
            print(f"  FAIL {title} case {i}: expected='{exp}'")

if all_pass_ok:
    print("  All pass tests OK!")

print()
print("=== REJECT TESTS (wrong output must be rejected) ===")
all_reject_ok = True
for title, inp, wrong_out in REJECT_TESTS:
    tcs = build_tcs(title)
    exp = tcs[0]['output'] if tcs else ''
    result = verify(title, inp, wrong_out, exp)
    if result:
        all_reject_ok = False
        print(f"  FAIL (accepted wrong output) {title}: input={repr(inp)} wrong={repr(wrong_out)}")

if all_reject_ok:
    print(f"  All {len(REJECT_TESTS)}/{len(REJECT_TESTS)} correctly rejected!")

print()
print("=== SUMMARY ===")
issues = (not all_pass_ok) or (not all_reject_ok)
if not issues:
    print("ALL CLEAR — 0 issues remaining.")
else:
    print("Issues remain (see above).")
