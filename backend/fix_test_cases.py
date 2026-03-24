from app import create_app
from app.models.practice import PracticeProblem
from app import db

app = create_app()
ctx = app.app_context()
ctx.push()

fixes = {

    # ID 4 — Temperature Converter
    # Description says: accept value AND unit (C or F)
    # Fix: add unit line to all inputs, fix expected outputs
    4: [
        {'input': '100\nC', 'output': '212.0'},
        {'input': '32\nF',  'output': '0.0'},
        {'input': '37\nC',  'output': '98.6'},
    ],

    # ID 10 — Check Alphabet Type
    # No TC change needed — verifier fix handles this
    # But update expected outputs to be consistent
    10: [
        {'input': 'A', 'output': 'Uppercase'},
        {'input': 'z', 'output': 'Lowercase'},
        {'input': '3', 'output': 'Not an Alphabet'},
    ],

    # ID 41 — String Compression
    # TC2: 'abcd' compressed = 'a1b1c1d1' (longer) so return original
    41: [
        {'input': 'aabcccdd', 'output': 'a2b1c3d2'},
        {'input': 'abcd',     'output': 'abcd'},      # fixed: was 'a1b1c1d1'
        {'input': 'aaaa',     'output': 'a4'},
    ],

    # ID 45 — Method Overloading
    # Add count as first line so student knows how many values to read
    45: [
        {'input': '2\n5\n3',    'output': '8'},
        {'input': '2\n10\n20',  'output': '30'},
        {'input': '3\n1\n2\n3', 'output': '6'},
    ],

    # ID 46 — Student Result System
    # TC expected output: grade letter only (verifier will only check grade)
    46: [
        {'input': '5\n70\n75\n80\n85\n90', 'output': 'B'},
        {'input': '5\n95\n97\n98\n96\n99', 'output': 'A+'},
        {'input': '5\n20\n25\n30\n35\n40', 'output': 'F'},
    ],

    # ID 47 — Employee Salary System
    # Description: single input = basic salary, HRA=20%, DA=10%, Gross=basic+HRA+DA
    47: [
        {'input': '50000',  'output': 'HRA: 10000.0  DA: 5000.0  Gross: 65000.0'},
        {'input': '30000',  'output': 'HRA: 6000.0  DA: 3000.0  Gross: 39000.0'},
        {'input': '100000', 'output': 'HRA: 20000.0  DA: 10000.0  Gross: 130000.0'},
    ],

    # ID 48 — Menu-Driven Program
    # Standardise: choices 1-4, 4=Exit. Invalid choice = anything outside 1-4
    48: [
        {'input': '99\n4', 'output': 'Invalid'},
        {'input': '2\n4',  'output': 'Option 2'},
        {'input': '4',     'output': 'Exit'},
    ],

    # ID 49 — Custom Exception Demo
    # TC3: age=10 should throw exception (< 18), not be valid. Fix to age=20
    49: [
        {'input': '-1', 'output': 'Exception'},
        {'input': '0',  'output': 'Exception'},
        {'input': '20', 'output': 'Valid'},       # fixed: was '10'
    ],

    # ID 54 — ATM Simulator
    # Add note: PIN is 1234. TC inputs already correct, just ensure consistency
    54: [
        {'input': '1234\n2\n5000\n4', 'output': 'deposit'},
        {'input': '1234\n1\n4',       'output': 'balance'},
        {'input': '9999\n4',          'output': 'denied'},   # wrong PIN, no 'wrong' keyword needed
    ],

    # ID 60 — Bank Account System
    # TC2 assumes first account ID = 1001 — make verifier keyword-based, keep TC
    # No TC change needed — verifier fix handles this
    # But clarify TC2 to not rely on specific ID
    60: [
        {'input': '1\nPriya\n5',              'output': 'created'},
        {'input': '1\nRaj\n2\n1001\n5000\n5', 'output': 'deposit'},
        {'input': '3\n9999\n1000\n5',         'output': 'not found'},
    ],

    # ID 65 — Restaurant Billing System
    # TC1 used item code P01 — replace with item name approach
    65: [
        {'input': '1\nBurger\n5',    'output': 'added'},
        {'input': '1\nPizza\n4\n5',  'output': 'total'},
        {'input': '4\n5',            'output': 'empty'},
    ],

    # ID 74 — E-Voting with ID Validation
    # Pre-registered IDs must be VID-001 to VID-005 (stated in description)
    74: [
        {'input': 'VID-001\nAlice',              'output': 'recorded'},
        {'input': 'VID-001\nAlice\nVID-001\nBob', 'output': 'already'},
        {'input': 'INVALID-ID\nAlice',           'output': 'invalid'},
    ],
}

updated = 0
for pid, tcs in fixes.items():
    p = PracticeProblem.query.get(pid)
    if not p:
        print(f"NOT FOUND: ID:{pid}")
        continue
    p.test_cases = tcs
    updated += 1
    print(f"Updated ID:{pid} | {p.title}")

db.session.commit()
print(f"\nDone. Updated {updated} problems.")
ctx.pop()
