from flask import Blueprint, jsonify, request
import re
from math import gcd

from app import db
from app.middleware.auth import token_required
from app.models.practice import PracticeProblem, PracticeAttempt, PracticeDraft
from app.routes.profile import update_streak_on_submit
from app.services.java_executor import get_java_executor

practice_bp = Blueprint('practice', __name__)

LEVEL_ORDER = ['beginner', 'intermediate', 'advanced']
LEVEL_MIX = 0.0


def _extract_numbers(text: str):
    return re.findall(r'-?\d+(?:\.\d+)?', text or '')


def _normalize_problem_title_key(value: str):
    return re.sub(r'\s+', ' ', (value or '').strip().lower().replace('—', '-'))


def _build_input_variants(case_input: str):
    raw = str(case_input or "")
    normalized = raw.replace('\\n', '\n').replace('\\r', '').strip()
    variants = []

    def add_variant(value: str):
        candidate = (value or '').replace('\r\n', '\n').replace('\r', '\n')
        if candidate and not candidate.endswith('\n'):
            candidate = f"{candidate}\n"
        if candidate and candidate not in variants:
            variants.append(candidate)

    add_variant(normalized)

    if '|' in normalized:
        pipe_parts = [p.strip() for p in normalized.split('|') if p.strip()]
        if pipe_parts:
            add_variant('\n'.join(pipe_parts))
            add_variant(' '.join(pipe_parts))

    bracket_matches = re.findall(r'\[([^\]]+)\]', normalized)
    if bracket_matches:
        for match in bracket_matches:
            numbers = re.findall(r'-?\d+(?:\.\d+)?', match)
            if numbers:
                add_variant(' '.join(numbers))
                add_variant('\n'.join(numbers))
                add_variant(f"{len(numbers)}\n{' '.join(numbers)}")

    if not variants:
        add_variant('')
    else:
        base_variants = list(variants)
        for base in base_variants:
            add_variant(f"{base.rstrip()}\n6\n")
            add_variant(f"{base.rstrip()}\n5\n")
            add_variant(f"{base.rstrip()}\n0\n")

    return variants


def _verify_output(problem_title: str, input_data: str, actual_output: str, expected_output: str) -> bool:
    """
    Programmatic verifier for all 75 problems.
    Computes the correct answer from input_data in Python,
    then checks if that answer appears anywhere in actual_output.
    Format, labels, spacing — all ignored.
    Falls back to expected_output string check for unknown problems.
    """
    title = _normalize_problem_title_key(problem_title)
    output = (actual_output or '').strip()
    output_lower = output.lower()
    nums = _extract_numbers(output)
    lines = [l.strip() for l in output.splitlines() if l.strip()]
    expected_raw = (expected_output or '').strip()
    expected_lower = expected_raw.lower()
    expected_nums = _extract_numbers(expected_raw)

    if expected_lower:
        compact_output = re.sub(r'\s+', ' ', output_lower)
        compact_expected = re.sub(r'\s+', ' ', expected_lower)
        expected_is_numeric = bool(re.fullmatch(r'-?\d+(?:\.\d+)?', compact_expected))
        negated_expected = (
            f"not {compact_expected}" in compact_output
            or f"not a {compact_expected}" in compact_output
            or f"not an {compact_expected}" in compact_output
        )
        if (
            not expected_is_numeric
            and compact_expected
            and not negated_expected
            and re.search(r'(?<![.\d-])' + re.escape(compact_expected) + r'(?![.\d])', compact_output)
        ):
            return True
        if expected_nums and all(any(abs(float(n) - float(en)) < 0.1 for n in nums) for en in expected_nums):
            return True

    def has_num(val, tol=0.1):
        try:
            return any(abs(float(n) - float(val)) <= tol for n in nums)
        except Exception:
            return False

    def input_lines():
        return [p.strip() for p in input_data.strip().split('\n') if p.strip()]

    def input_nums():
        return list(map(float, _extract_numbers(input_data)))

    try:

        # ── BEGINNER ─────────────────────────────────────────────────────────

        if title == 'even / odd checker':
            n = int(input_nums()[0])
            return ('even' if n % 2 == 0 else 'odd') in output_lower

        if title == 'largest of three numbers':
            return str(int(max(input_nums()))) in nums

        if title == 'leap year checker':
            y = int(input_nums()[0])
            if y <= 0:
                return 'invalid' in output_lower
            is_leap = (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)
            if 'not a leap' in output_lower or 'not leap' in output_lower:
                return not is_leap
            elif 'leap' in output_lower:
                return is_leap
            return False

        if title == 'temperature converter':
            il = input_lines()
            val = float(_extract_numbers(il[0])[0])
            unit = il[1].strip().upper() if len(il) > 1 else 'C'
            if unit not in ('C', 'F'):
                return 'invalid' in output_lower
            if unit == 'C':
                result = round(val * 9 / 5 + 32, 2)
            else:
                result = round((val - 32) * 5 / 9, 2)
            positive_nums = [n for n in nums if not n.startswith('-')]
            if result >= 0:
                if not positive_nums:
                    return False
                return any(abs(float(n) - result) <= 0.1 for n in positive_nums)
            return has_num(result, 0.1)

        if title == 'grade system':
            m = int(input_nums()[0])
            if m < 0 or m > 100:
                return 'invalid' in output_lower
            g = 'a+' if m >= 90 else 'a' if m >= 80 else 'b' if m >= 70 else 'c' if m >= 60 else 'd' if m >= 50 else 'f'
            return ('fail' in output_lower or 'f' in output_lower) if g == 'f' else g in output_lower

        if title == 'simple interest calculator':
            v = input_nums()
            return has_num(round(v[0] * v[1] * v[2] / 100, 2), 0.5)

        if title == 'swap without third variable':
            v = list(map(int, input_nums()))
            return str(v[1]) in nums and str(v[0]) in nums

        if title == 'count vowels':
            return str(sum(1 for c in input_data.strip().lower() if c in 'aeiou')) in nums

        if title == 'character frequency':
            il = input_lines()
            if len(il) < 2:
                il = [p.strip() for p in input_data.split('|') if p.strip()]
            return str(il[0].count(il[1][0])) in nums

        if title == 'check alphabet type':
            # FIX: was checking 'digit' in output, but correct output is "Not an Alphabet"
            ch = input_data.strip()[0]
            if ch.isupper():
                return 'upper' in output_lower
            elif ch.islower():
                return 'lower' in output_lower
            else:
                # digit or special character — output should say "not an alphabet" or similar
                return ('not' in output_lower and 'alphabet' in output_lower) or 'digit' in output_lower or 'special' in output_lower

        if title == 'sum of n natural numbers':
            n = int(input_nums()[0])
            return str(n * (n + 1) // 2) in nums

        if title == 'multiplication table':
            n = int(input_nums()[0])
            out_ints = [int(float(x)) for x in nums]
            return all(n * i in out_ints for i in range(1, 11))

        if title == 'count digits':
            s = input_data.strip().lstrip('-')
            return str(len(s)) in nums

        if title == 'sum of digits':
            return str(sum(int(d) for d in input_data.strip().lstrip('-') if d.isdigit())) in nums

        if title == 'basic calculator':
            il = input_lines()
            a, b, op = float(il[0]), float(il[1]), il[2].strip()
            if op == '/' and b == 0:
                return any(w in output_lower for w in ['zero', 'cannot', 'divide', 'undefined', 'error'])
            res = {'+': (a + b), '-': (a - b), '*': (a * b), '/': (a / b if b != 0 else None)}.get(op)
            if res is None:
                return 'invalid' in output_lower
            return has_num(res, 0.01)

        if title == 'factorial calculator':
            n = int(input_nums()[0])
            if n < 0:
                return 'invalid' in output_lower
            r = 1
            for i in range(2, n + 1):
                r *= i
            return str(r) in nums

        if title == 'prime number checker':
            n = int(input_nums()[0])
            if n < 0:
                return 'invalid' in output_lower
            is_p = n >= 2 and all(n % i != 0 for i in range(2, int(n ** 0.5) + 1))
            if 'not prime' in output_lower:
                return not is_p
            elif 'prime' in output_lower:
                return is_p
            return False

        if title == 'fibonacci series':
            n = int(input_nums()[0])
            if n <= 0:
                return 'invalid' in output_lower
            fibs = [0, 1]
            while len(fibs) < n:
                fibs.append(fibs[-1] + fibs[-2])
            fibs = fibs[:n]
            out = [int(float(x)) for x in nums]
            return out[-len(fibs):] == fibs

        if title == 'reverse a number':
            s = input_data.strip()
            if s.startswith('-'):
                return 'invalid' in output_lower
            rev = s[::-1].lstrip('0') or '0'
            return rev in output

        if title == 'palindrome number':
            s = input_data.strip()
            if s.startswith('-'):
                return 'invalid' in output_lower
            is_p = s == s[::-1]
            if 'not palindrome' in output_lower or 'not a palindrome' in output_lower:
                return not is_p
            elif 'palindrome' in output_lower:
                return is_p
            return False

        if title == 'armstrong number':
            s = input_data.strip()
            if s.startswith('-'):
                return 'invalid' in output_lower
            d = len(s)
            is_a = sum(int(c) ** d for c in s if c.isdigit()) == int(s)
            if 'not armstrong' in output_lower or 'not an armstrong' in output_lower:
                return not is_a
            elif 'armstrong' in output_lower:
                return is_a
            return False

        if title == 'gcd and lcm':
            v = list(map(int, input_nums()))
            if v[0] <= 0 or v[1] <= 0:
                return 'invalid' in output_lower
            g = gcd(v[0], v[1])
            l = abs(v[0] * v[1]) // g
            return str(g) in nums and str(l) in nums

        if title == 'power calculator':
            v = list(map(int, input_nums()))
            if v[1] < 0:
                return 'invalid' in output_lower
            return str(v[0] ** v[1]) in nums

        if title == 'pattern - star pyramid':
            n = int(input_nums()[0])
            counts = [l.count('*') for l in lines if '*' in l]
            # Accept both left-aligned staircase (1,2,3...) and centred pyramid (1,3,5...)
            return (counts[-n:] == list(range(1, n + 1)) or
                    counts[-n:] == [2 * i - 1 for i in range(1, n + 1)])

        if title == 'pattern - number triangle':
            n = int(input_nums()[0])
            counts = [len(_extract_numbers(l)) for l in lines]
            return counts[-n:] == list(range(1, n + 1))

        # ── INTERMEDIATE ──────────────────────────────────────────────────────

        if title == 'find largest in array':
            il = input_lines()
            arr = list(map(int, _extract_numbers(il[1] if len(il) > 1 else il[0])))
            return str(max(arr)) in nums

        if title == 'reverse an array':
            il = input_lines()
            arr = list(map(int, _extract_numbers(il[1] if len(il) > 1 else il[0])))
            out = [int(float(x)) for x in nums]
            return out[-len(arr):] == list(reversed(arr))

        if title == 'linear search':
            il = input_lines()
            arr = list(map(int, _extract_numbers(il[1])))
            target = int(_extract_numbers(il[2])[0])
            if target in arr:
                return str(arr.index(target)) in nums
            return 'not found' in output_lower or '-1' in nums

        if title == 'sum of array elements':
            il = input_lines()
            arr = list(map(int, _extract_numbers(il[1] if len(il) > 1 else il[0])))
            return str(sum(arr)) in nums

        if title == 'count even and odd':
            il = input_lines()
            arr = list(map(int, _extract_numbers(il[1] if len(il) > 1 else il[0])))
            even = sum(1 for x in arr if x % 2 == 0)
            return str(even) in nums and str(len(arr) - even) in nums

        if title == 'find second largest':
            il = input_lines()
            arr = list(map(int, _extract_numbers(il[1] if len(il) > 1 else il[0])))
            su = sorted(set(arr), reverse=True)
            return str(su[1] if len(su) > 1 else su[0]) in nums

        if title == 'bubble sort':
            il = input_lines()
            arr = list(map(int, _extract_numbers(il[1] if len(il) > 1 else il[0])))
            out = [int(float(x)) for x in nums]
            return out[-len(arr):] == sorted(arr)

        if title == 'binary search':
            il = input_lines()
            arr = list(map(int, _extract_numbers(il[1])))
            target = int(_extract_numbers(il[2])[0])
            if target in arr:
                return str(arr.index(target)) in nums
            return 'not found' in output_lower or '-1' in nums

        if title == 'remove duplicates':
            il = input_lines()
            arr = list(map(int, _extract_numbers(il[1] if len(il) > 1 else il[0])))
            unique = list(dict.fromkeys(arr))
            out = [int(float(x)) for x in nums]
            return out[-len(unique):] == unique

        if title == 'array rotation (left by k)':
            il = input_lines()
            arr = list(map(int, _extract_numbers(il[1])))
            k = int(_extract_numbers(il[2])[0]) % len(arr)
            rotated = arr[k:] + arr[:k]
            out = [int(float(x)) for x in nums]
            return out[-len(rotated):] == rotated

        if title == 'reverse a string':
            return input_data.strip()[::-1].lower() in output_lower

        if title == 'palindrome string':
            s = input_data.strip().lower()
            is_p = s == s[::-1]
            if 'not palindrome' in output_lower or 'not a palindrome' in output_lower:
                return not is_p
            elif 'palindrome' in output_lower:
                return is_p
            return False

        if title == 'count words in a sentence':
            return str(len(input_data.strip().split())) in nums

        if title == 'remove spaces':
            return input_data.strip().replace(' ', '').lower() in output_lower

        if title == 'anagram checker':
            il = input_lines()
            is_a = sorted(il[0].lower()) == sorted(il[1].lower())
            if 'not anagram' in output_lower or 'not an anagram' in output_lower:
                return not is_a
            elif 'anagram' in output_lower:
                return is_a
            return False

        if title == 'string compression':
            s = input_data.strip()
            comp = ''
            i = 0
            while i < len(s):
                count = 1
                while i + count < len(s) and s[i + count] == s[i]:
                    count += 1
                comp += s[i] + str(count)
                i += count
            # FIX: if compressed is longer or equal, return original — check either in output
            expected = s if len(comp) >= len(s) else comp
            return expected in output

        if title == 'matrix addition':
            il = input_lines()
            n = int(_extract_numbers(il[0])[0])
            m1 = [list(map(int, _extract_numbers(il[i + 1]))) for i in range(n)]
            m2 = [list(map(int, _extract_numbers(il[i + n + 1]))) for i in range(n)]
            result = [str(m1[i][j] + m2[i][j]) for i in range(n) for j in range(len(m1[i]))]
            return all(r in nums for r in result)

        if title == 'transpose a matrix':
            il = input_lines()
            n = int(_extract_numbers(il[0])[0])
            mat = [list(map(int, _extract_numbers(il[i + 1]))) for i in range(n)]
            result = [str(mat[j][i]) for i in range(n) for j in range(n)]
            return all(r in nums for r in result)

        if title == 'matrix multiplication':
            il = input_lines()
            n = int(_extract_numbers(il[0])[0])
            m1 = [list(map(int, _extract_numbers(il[i + 1]))) for i in range(n)]
            m2 = [list(map(int, _extract_numbers(il[i + n + 1]))) for i in range(n)]
            result = [str(sum(m1[i][k] * m2[k][j] for k in range(n))) for i in range(n) for j in range(n)]
            return all(r in nums for r in result)

        if title == 'method overloading demo':
            # FIX: Input now has count as first line: count\nv1\nv2\n[v3]
            il = input_lines()
            try:
                count = int(il[0])
                values = list(map(float, _extract_numbers('\n'.join(il[1:count + 1]))))
            except Exception:
                values = input_nums()
            return has_num(sum(values), 0.01)

        if title == 'student result system':
            # FIX: only check grade letter, not total
            il = input_lines()
            n = int(_extract_numbers(il[0])[0])
            marks = list(map(int, _extract_numbers('\n'.join(il[1:n + 1]))))
            avg = sum(marks) / len(marks)
            g = 'a+' if avg >= 90 else 'a' if avg >= 80 else 'b' if avg >= 70 else 'c' if avg >= 60 else 'd' if avg >= 50 else 'f'
            if g == 'f':
                return 'fail' in output_lower or output_lower.strip() == 'f'
            return g in output_lower

        if title == 'employee salary system':
            values = input_nums()
            if len(values) >= 3:
                basic, allowance, deduction = values[0], values[1], values[2]
                net = basic + allowance - deduction
                return has_num(net, 0.5)
            if len(values) == 1:
                basic = values[0]
                hra = round(basic * 0.20, 2)
                da = round(basic * 0.10, 2)
                gross = basic + hra + da
                return has_num(hra, 1) and has_num(da, 1) and has_num(gross, 1)
            return False

        if title == 'menu-driven program':
            # FIX: choices 1-4 valid, 4=Exit, anything else = invalid
            il = input_lines()
            choice = il[0] if il else '0'
            try:
                c = int(choice)
                if c == 4 or c == 0:
                    return any(w in output_lower for w in ['exit', 'bye', 'goodbye'])
                if c not in range(1, 4):
                    return any(w in output_lower for w in ['invalid', 'error', 'wrong'])
            except ValueError:
                pass
            return len(output) > 0

        if title == 'custom exception demo':
            # FIX: age < 18 → exception, age >= 18 → valid/granted
            age = int(input_nums()[0])
            if age < 18:
                return any(w in output_lower for w in ['18', 'invalid', 'exception', 'must', 'above', 'error', 'age'])
            return any(w in output_lower for w in ['granted', 'valid', 'welcome', 'success', 'access'])

        if title == 'number guessing game':
            return any(w in output_lower for w in ['high', 'low', 'correct', 'guess', 'attempt', 'try'])

        # ── ADVANCED ─────────────────────────────────────────────────────────

        if title == 'student management system':
            il = input_lines()
            action = il[0] if il else ''
            if action == '1':
                name = il[1] if len(il) > 1 else ''
                return any(w in output_lower for w in ['added', 'success']) or name.lower() in output_lower
            if action == '2':
                return len(lines) > 1
            if action == '3':
                term = il[1] if len(il) > 1 else ''
                return term.lower() in output_lower or 'not found' in output_lower
            return len(output) > 0

        if title == 'library system':
            il = input_lines()
            action = il[0] if il else ''
            if action == '1':
                book = il[1] if len(il) > 1 else ''
                return 'added' in output_lower or book.lower() in output_lower
            if action == '2':
                return len(lines) > 1
            if action == '3':
                keyword = il[1] if len(il) > 1 else ''
                return keyword.lower() in output_lower or any(w in output_lower for w in ['not found', 'no books'])
            return len(output) > 0

        if title == 'contact book':
            il = input_lines()
            action = il[0] if il else ''
            if action == '1':
                name = il[1] if len(il) > 1 else ''
                return any(w in output_lower for w in ['saved', 'added']) or name.lower() in output_lower
            if action == '2':
                return len(lines) > 1
            if action == '3':
                name = il[1] if len(il) > 1 else ''
                return name.lower() in output_lower or 'not found' in output_lower
            if action == '4':
                name = il[1] if len(il) > 1 else ''
                return any(w in output_lower for w in ['deleted', 'removed', 'not found']) or name.lower() in output_lower
            return len(output) > 0

        if title == 'atm simulator':
            # FIX: wrong PIN check — any non-matching PIN gives denied
            il = input_lines()
            pin = il[0] if il else ''
            # If PIN is not 1234, expect denied
            if pin != '1234':
                return any(w in output_lower for w in ['denied', 'incorrect', 'invalid', 'wrong', 'access'])
            action = il[1] if len(il) > 1 else ''
            if action == '1':
                return 'balance' in output_lower or len(nums) > 0
            if action == '2':
                amount = float(_extract_numbers(il[2])[0]) if len(il) > 2 else 0
                return 'deposit' in output_lower or has_num(amount, 1)
            if action == '3':
                return any(w in output_lower for w in ['withdraw', 'insufficient', 'balance'])
            return len(output) > 0

        if title == 'shopping cart system':
            il = input_lines()
            action = il[0] if il else ''
            if action == '1':
                item = il[1] if len(il) > 1 else ''
                return 'added' in output_lower or item.lower() in output_lower
            if action == '2':
                return len(lines) > 0
            if action == '3':
                return any(w in output_lower for w in ['removed', 'not found'])
            if action == '4':
                return any(w in output_lower for w in ['total', 'bill', 'empty'])
            return len(output) > 0

        if title == 'expense tracker':
            il = input_lines()
            action = il[0] if il else ''
            if action == '1':
                return any(w in output_lower for w in ['added', 'expense'])
            if action == '2':
                return len(lines) > 0
            if action == '3':
                cat = il[1] if len(il) > 1 else ''
                return cat.lower() in output_lower or 'no expenses' in output_lower
            if action == '4':
                # Check total amount appears in output
                total_nums = _extract_numbers(input_data)
                amounts = [float(x) for x in total_nums if float(x) > 10]
                if amounts:
                    return has_num(sum(amounts[-3:]), 5) or 'total' in output_lower or len(nums) > 0
                return 'total' in output_lower or len(nums) > 0
            return len(output) > 0

        if title == 'quiz application':
            return any(w in output_lower for w in ['score', 'correct', 'wrong', 'question', 'invalid'])

        if title == 'voting system':
            il = input_lines()
            voter_id = il[0] if il else ''
            # Check if same voter_id appears more than once in input
            if input_data.lower().count(voter_id.lower()) > 1:
                return any(w in output_lower for w in ['already', 'voted', 'used'])
            # Check for invalid candidate
            candidate = il[1] if len(il) > 1 else ''
            if candidate.lower() in ['nobody', 'invalid', 'unknown']:
                return any(w in output_lower for w in ['not found', 'invalid', 'candidate'])
            return any(w in output_lower for w in ['cast', 'recorded', 'voted']) or candidate.lower() in output_lower

        if title == 'parking lot system':
            il = input_lines()
            action = il[0] if il else ''
            if action == '1':
                plate = il[1] if len(il) > 1 else ''
                return any(w in output_lower for w in ['assigned', 'parked', 'full']) or plate.lower() in output_lower
            if action == '2':
                plate = il[1] if len(il) > 1 else ''
                return any(w in output_lower for w in ['removed', 'left', 'not found']) or plate.lower() in output_lower
            if action == '3':
                return any(w in output_lower for w in ['slot', 'free', 'occupied']) or len(lines) > 0
            return len(output) > 0

        if title == 'bank account system':
            il = input_lines()
            action = il[0] if il else ''
            if action == '1':
                return any(w in output_lower for w in ['created', 'account']) or len(nums) > 0
            if action == '2':
                # FIX: don't rely on specific account ID — just check deposit keyword
                return 'deposit' in output_lower or any(w in output_lower for w in ['success', 'added', 'balance'])
            if action == '3':
                return any(w in output_lower for w in ['withdraw', 'insufficient', 'balance', 'not found'])
            if action == '4':
                return len(lines) > 0
            return len(output) > 0

        if title == 'password validator':
            p = input_data.strip()
            passed = sum([
                any(c.isupper() for c in p),
                any(c.isdigit() for c in p),
                any(c in '!@#$%' for c in p),
                ' ' not in p,
                len(p) >= 8
            ])
            exp = 'strong' if passed >= 5 else 'moderate' if passed >= 3 else 'weak'
            return exp in output_lower

        if title == 'task manager':
            il = input_lines()
            action = il[0] if il else ''
            if action == '1':
                name = il[1] if len(il) > 1 else ''
                return 'added' in output_lower or name.lower() in output_lower
            if action == '2':
                return any(w in output_lower for w in ['complete', 'done', 'not found'])
            if action == '3':
                return any(w in output_lower for w in ['removed', 'deleted', 'not found'])
            if action in ('4', '5'):
                return len(lines) > 0 or 'no' in output_lower
            return len(output) > 0

        if title == 'inventory system':
            il = input_lines()
            action = il[0] if il else ''
            if action == '1':
                return any(w in output_lower for w in ['added', 'product'])
            if action == '2':
                return any(w in output_lower for w in ['restocked', 'updated', 'added']) or len(nums) > 0
            if action == '3':
                return any(w in output_lower for w in ['sold', 'insufficient', 'stock'])
            if action == '4':
                return len(lines) > 0
            return len(output) > 0

        if title == 'ticket booking system':
            il = input_lines()
            action = il[0] if il else ''
            if action == '1':
                seat = il[1] if len(il) > 1 else ''
                return any(w in output_lower for w in ['booked', 'already']) or seat in nums
            if action == '2':
                return any(w in output_lower for w in ['cancelled', 'canceled', 'not booked'])
            if action == '3':
                return len(lines) > 0
            return len(output) > 0

        if title == 'restaurant billing system':
            il = input_lines()
            action = il[0] if il else ''
            if action == '1':
                item = il[1] if len(il) > 1 else ''
                # FIX: check item name in output or 'added' keyword
                return any(w in output_lower for w in ['added', 'order']) or item.lower() in output_lower
            if action == '2':
                return any(w in output_lower for w in ['removed', 'not found'])
            if action == '4':
                return any(w in output_lower for w in ['total', 'bill', 'gst', 'empty']) or len(nums) > 0
            return len(output) > 0

        if title == 'simple chat simulation':
            il = input_lines()
            msg = il[0] if il else ''
            if not msg:
                return any(w in output_lower for w in ['no messages', 'empty', 'no chat'])
            return msg.lower() in output_lower or any(w in output_lower for w in ['user', 'chat', 'message'])

        if title == 'simple login system':
            il = input_lines()
            action = il[0] if il else ''
            username = il[1] if len(il) > 1 else ''
            if action == '1':
                return any(w in output_lower for w in ['registered', 'success']) or username.lower() in output_lower
            if action == '2':
                if 'wrong' in input_data.lower():
                    return any(w in output_lower for w in ['invalid', 'incorrect', 'locked', 'attempt', 'wrong'])
                return any(w in output_lower for w in ['welcome', 'success', 'invalid', 'not found', 'locked']) or username.lower() in output_lower
            return len(output) > 0

        if title == 'employee management + sort by salary':
            il = input_lines()
            action = il[0] if il else ''
            if action == '1':
                name = il[1] if len(il) > 1 else ''
                return 'added' in output_lower or name.lower() in output_lower
            if action == '2':
                return len(lines) > 0
            if action == '3':
                salary_nums = [float(n) for n in nums]
                if len(salary_nums) >= 2:
                    # sort_choice is the next input after action '3'
                    action_idx = [i for i, l in enumerate(il) if l == '3']
                    sort_choice = il[action_idx[0] + 1] if action_idx and action_idx[0] + 1 < len(il) else '1'
                    if sort_choice == '1':
                        return salary_nums == sorted(salary_nums)
                    else:
                        return salary_nums == sorted(salary_nums, reverse=True)
                return len(lines) > 0
            if action == '4':
                dept = il[1] if len(il) > 1 else ''
                return dept.lower() in output_lower or 'no employees' in output_lower
            return len(output) > 0

        if title == 'mini banking transaction history':
            il = input_lines()
            action = il[0] if il else ''
            if action == '1':
                amount = float(_extract_numbers(il[1])[0]) if len(il) > 1 else 0
                return 'deposit' in output_lower or has_num(amount, 1)
            if action == '2':
                return any(w in output_lower for w in ['withdraw', 'insufficient', 'balance'])
            if action == '3':
                return len(lines) > 0 or 'no transaction' in output_lower
            if action == '4':
                return len(lines) > 0 or 'no' in output_lower
            return len(output) > 0

        if title == 'course enrollment system':
            il = input_lines()
            action = il[0] if il else ''
            if action == '1':
                return any(w in output_lower for w in ['added', 'course'])
            if action == '2':
                return any(w in output_lower for w in ['enrolled', 'already', 'full'])
            if action == '3':
                return any(w in output_lower for w in ['dropped', 'not enrolled'])
            if action == '4':
                return len(lines) > 0 or 'not enrolled' in output_lower
            return len(output) > 0

        if title == 'hotel room booking':
            il = input_lines()
            action = il[0] if il else ''
            if action == '1':
                return len(lines) > 0 or 'no rooms' in output_lower
            if action == '2':
                return any(w in output_lower for w in ['booked', 'not available', 'room'])
            if action == '3':
                return any(w in output_lower for w in ['invoice', 'total', 'checked out', 'checkout']) or len(nums) > 0
            if action == '4':
                return len(lines) > 0 or 'no bookings' in output_lower
            return len(output) > 0

        if title == 'stack implementation (manual)':
            il = input_lines()
            action = il[0] if il else ''
            if action == '1':
                val = il[1] if len(il) > 1 else ''
                return val in nums or any(w in output_lower for w in ['overflow', 'full', 'pushed', 'stack'])
            if action == '2':
                return any(w in output_lower for w in ['popped', 'underflow', 'empty']) or len(nums) > 0
            if action == '3':
                return len(nums) > 0 or 'empty' in output_lower
            if action == '4':
                expr = il[1] if len(il) > 1 else ''
                stack = []
                balanced = True
                pairs = {')': '(', '}': '{', ']': '['}
                for ch in expr:
                    if ch in '({[':
                        stack.append(ch)
                    elif ch in ')}]':
                        if not stack or stack[-1] != pairs[ch]:
                            balanced = False
                            break
                        stack.pop()
                if stack:
                    balanced = False
                return ('balanced' in output_lower and 'unbalanced' not in output_lower) == balanced
            return len(output) > 0

        if title == 'queue implementation (manual)':
            il = input_lines()
            action = il[0] if il else ''
            if action == '1':
                return any(w in output_lower for w in ['queued', 'added', 'full', 'enqueue', 'enqueued'])
            if action == '2':
                return any(w in output_lower for w in ['processing', 'dequeued', 'empty', 'removed']) or len(output) > 0
            if action == '3':
                return len(output) > 0 or 'empty' in output_lower
            if action == '4':
                return any(w in output_lower for w in ['print', 'job', 'queue']) or len(lines) > 0
            return len(output) > 0

        if title == 'e-voting with id validation':
            # FIX: pre-registered IDs are VID-001 through VID-005
            il = input_lines()
            voter_id = il[0] if il else ''
            valid_ids = {'vid-001', 'vid-002', 'vid-003', 'vid-004', 'vid-005'}
            # Duplicate vote check
            if input_data.lower().count(voter_id.lower()) > 1:
                return any(w in output_lower for w in ['already', 'voted'])
            # Invalid ID check
            if voter_id.lower() not in valid_ids:
                return any(w in output_lower for w in ['invalid', 'not registered', 'not found'])
            candidate = il[1] if len(il) > 1 else ''
            return any(w in output_lower for w in ['recorded', 'cast', 'voted']) or candidate.lower() in output_lower

        if title == 'multi-user scoreboard system':
            il = input_lines()
            action = il[0] if il else ''
            if action == '1':
                name = il[1] if len(il) > 1 else ''
                return 'added' in output_lower or name.lower() in output_lower
            if action == '2':
                return 'updated' in output_lower or 'score' in output_lower or len(nums) > 0
            if action == '3':
                score_nums = [float(n) for n in nums]
                if len(score_nums) >= 2:
                    return score_nums == sorted(score_nums, reverse=True)
                return len(lines) > 0
            if action == '4':
                n = int(_extract_numbers(il[1])[0]) if len(il) > 1 else 0
                return len(lines) <= n + 2
            if action == '5':
                return len(output) > 0
            return len(output) > 0

    except Exception:
        exp = (expected_output or '').strip()
        if not exp:
            return len(output) > 0
        compact_out = re.sub(r'\s+', ' ', output_lower)
        compact_exp = re.sub(r'\s+', ' ', exp.lower()).strip()
        if compact_out.strip() == compact_exp:
            return True
        return bool(re.search(r'(?<![.\d-])' + re.escape(compact_exp) + r'(?![.\d])', compact_out))

    exp = (expected_output or '').strip()
    if not exp:
        return len(output) > 0
    compact_out = re.sub(r'\s+', ' ', output_lower)
    compact_exp = re.sub(r'\s+', ' ', exp.lower()).strip()
    if compact_out.strip() == compact_exp:
        return True
    return bool(re.search(r'(?<![.\d-])' + re.escape(compact_exp) + r'(?![.\d])', compact_out))


def _problems_for_level(level: str, include_mix: bool = True):
    main_problems = (
        PracticeProblem.query.filter_by(level=level)
        .order_by(PracticeProblem.order_index.asc(), PracticeProblem.id.asc())
        .all()
    )
    if not include_mix or not main_problems:
        return main_problems
    if LEVEL_MIX <= 0:
        return main_problems
    idx = LEVEL_ORDER.index(level) if level in LEVEL_ORDER else 0
    mixed = []
    if idx + 1 < len(LEVEL_ORDER):
        next_level = LEVEL_ORDER[idx + 1]
        harder = (
            PracticeProblem.query.filter_by(level=next_level)
            .order_by(PracticeProblem.order_index.asc(), PracticeProblem.id.asc())
            .limit(max(1, int(len(main_problems) * LEVEL_MIX)))
        ).all()
        mixed.extend(harder)
    return main_problems + mixed


@practice_bp.route('/problems', methods=['GET'])
@token_required
def list_problems(current_user):
    level = request.args.get('level', '').lower() or (current_user.skill_level or 'beginner')
    if level not in LEVEL_ORDER:
        return jsonify({'error': 'Invalid level'}), 400
    tags = request.args.get('tags', '')
    problems = _problems_for_level(level, include_mix=True)
    if tags:
        tag_list = [t.strip().lower() for t in tags.split(',')]
        problems = [p for p in problems if any(t in (p.tags or []) for t in tag_list)]
    attempted_ids = {
        a.problem_id: a.status
        for a in PracticeAttempt.query.filter_by(user_id=current_user.id).all()
    }
    drafted_ids = {
        d.problem_id
        for d in PracticeDraft.query.filter_by(user_id=current_user.id).all()
    }
    result = []
    for p in problems:
        summary = p.to_summary()
        summary['attempt_status'] = attempted_ids.get(p.id)
        summary['has_draft'] = p.id in drafted_ids
        result.append(summary)
    return jsonify(result)


@practice_bp.route('/catalog', methods=['GET'])
@token_required
def get_catalog(current_user):
    problems = PracticeProblem.query.order_by(
        PracticeProblem.level.asc(),
        PracticeProblem.section.asc(),
        PracticeProblem.order_index.asc(),
        PracticeProblem.id.asc(),
    ).all()
    attempted_ids = {
        a.problem_id: a.status
        for a in PracticeAttempt.query.filter_by(user_id=current_user.id).all()
    }
    drafted_ids = {
        d.problem_id
        for d in PracticeDraft.query.filter_by(user_id=current_user.id).all()
    }
    payload = []
    for p in problems:
        item = p.to_summary()
        item['attempt_status'] = attempted_ids.get(p.id)
        item['has_draft'] = p.id in drafted_ids
        payload.append(item)
    return jsonify(payload)


@practice_bp.route('/problems/<int:problem_id>', methods=['GET'])
@token_required
def get_problem(current_user, problem_id):
    problem = PracticeProblem.query.get_or_404(problem_id)
    detail = problem.to_detail()
    draft = PracticeDraft.query.filter_by(
        user_id=current_user.id, problem_id=problem_id
    ).first()
    detail['draft_code'] = draft.code if draft else problem.starter_code
    return jsonify(detail)


@practice_bp.route('/attempts', methods=['POST'])
@token_required
def create_attempt(current_user):
    data = request.get_json(silent=True) or {}
    problem_id = data.get('problem_id')
    status = data.get('status', 'started')
    last_code = data.get('last_code')
    score = data.get('score')
    time_ms = data.get('time_ms')
    if not problem_id:
        return jsonify({'error': 'problem_id is required'}), 400
    if status not in ('started', 'passed', 'failed'):
        return jsonify({'error': 'Invalid status'}), 400
    PracticeProblem.query.get_or_404(problem_id)
    attempt = PracticeAttempt(
        user_id=current_user.id,
        problem_id=problem_id,
        status=status,
        last_code=last_code,
        score=score,
        time_ms=time_ms
    )
    db.session.add(attempt)
    if status == 'passed':
        update_streak_on_submit(current_user)
    db.session.commit()
    return jsonify(attempt.to_dict()), 201


@practice_bp.route('/attempts/<int:attempt_id>', methods=['PATCH'])
@token_required
def update_attempt(current_user, attempt_id):
    attempt = PracticeAttempt.query.filter_by(id=attempt_id, user_id=current_user.id).first_or_404()
    data = request.get_json(silent=True) or {}
    for field in ('status', 'last_code', 'score', 'time_ms'):
        if field in data:
            setattr(attempt, field, data[field])
    if data.get('status') == 'passed':
        update_streak_on_submit(current_user)
    db.session.commit()
    return jsonify(attempt.to_dict())


@practice_bp.route('/attempts', methods=['GET'])
@token_required
def list_attempts(current_user):
    attempts = (
        PracticeAttempt.query
        .filter_by(user_id=current_user.id)
        .order_by(PracticeAttempt.submitted_at.desc())
        .all()
    )
    return jsonify([a.to_dict() for a in attempts])


@practice_bp.route('/drafts', methods=['GET'])
@token_required
def get_draft(current_user):
    problem_id = request.args.get('problem_id', type=int)
    if not problem_id:
        return jsonify({'error': 'problem_id is required'}), 400
    draft = PracticeDraft.query.filter_by(
        user_id=current_user.id, problem_id=problem_id
    ).first()
    if not draft:
        PracticeProblem.query.get_or_404(problem_id)
        return jsonify({'problem_id': problem_id, 'code': '', 'updated_at': None, 'has_draft': False})
    payload = draft.to_dict()
    payload['has_draft'] = True
    return jsonify(payload)


@practice_bp.route('/drafts', methods=['PUT'])
@token_required
def save_draft(current_user):
    data = request.get_json(silent=True) or {}
    problem_id = data.get('problem_id')
    code = data.get('code', '')
    if not problem_id:
        return jsonify({'error': 'problem_id is required'}), 400
    PracticeProblem.query.get_or_404(problem_id)
    draft = PracticeDraft.query.filter_by(
        user_id=current_user.id, problem_id=problem_id
    ).first()
    if draft:
        draft.code = code
        draft.updated_at = db.func.now()
    else:
        draft = PracticeDraft(user_id=current_user.id, problem_id=problem_id, code=code)
        db.session.add(draft)
    db.session.commit()
    payload = draft.to_dict()
    payload['has_draft'] = True
    return jsonify(payload)


@practice_bp.route('/validate', methods=['POST'])
@token_required
def validate_solution(current_user):
    data = request.get_json(silent=True) or {}
    problem_id = data.get('problem_id')
    code = data.get('code', '')

    if not problem_id:
        return jsonify({'error': 'problem_id is required'}), 400
    if not code or not isinstance(code, str):
        return jsonify({'error': 'code is required'}), 400

    problem = PracticeProblem.query.get_or_404(problem_id)

    draft = PracticeDraft.query.filter_by(
        user_id=current_user.id, problem_id=problem.id
    ).first()
    if draft:
        draft.code = code
        draft.updated_at = db.func.now()
    else:
        db.session.add(PracticeDraft(
            user_id=current_user.id,
            problem_id=problem.id,
            code=code,
        ))

    def persist_attempt(solved: bool, passed: int, total: int):
        status = 'passed' if solved else 'failed'
        numeric_score = float((passed / total) * 100) if total > 0 else 0.0
        attempt = PracticeAttempt.query.filter_by(
            user_id=current_user.id, problem_id=problem.id
        ).order_by(PracticeAttempt.id.desc()).first()
        if attempt:
            attempt.status = status
            attempt.last_code = code
            attempt.score = numeric_score
            attempt.submitted_at = db.func.now()
        else:
            db.session.add(PracticeAttempt(
                user_id=current_user.id,
                problem_id=problem.id,
                status=status,
                last_code=code,
                score=numeric_score,
                time_ms=None,
            ))
        db.session.commit()
        if solved:
            try:
                update_streak_on_submit(current_user.id)
            except Exception:
                db.session.rollback()

    test_cases = problem.test_cases or []
    if not isinstance(test_cases, list) or len(test_cases) == 0:
        db.session.commit()
        return jsonify({'error': 'No test cases configured for this problem'}), 400

    executor = get_java_executor()
    results = []
    passed_count = 0

    for idx, test_case in enumerate(test_cases, start=1):
        original_input = str((test_case or {}).get('input', ''))
        input_variants = _build_input_variants(original_input)
        expected_output = str((test_case or {}).get('output', '')).strip()
        run = None
        actual_output = ''
        success = False
        used_input = input_variants[0] if input_variants else ''

        for candidate_input in input_variants:
            run = executor.compile_and_execute(code, input_data=candidate_input)
            actual_output = str(run.get('output', '')).strip()
            if bool(run.get('success')):
                if _verify_output(problem.title, candidate_input, actual_output, expected_output):
                    success = True
                    used_input = candidate_input
                    break

        if run is None:
            run = {'errors': []}
        if success:
            passed_count += 1

        results.append({
            'index': idx,
            'input': original_input,
            'used_input': used_input.strip(),
            'expected_output': expected_output,
            'actual_output': actual_output,
            'success': success,
            'errors': run.get('errors', []),
        })

    solved = passed_count == len(test_cases)
    persist_attempt(solved, passed_count, len(test_cases))
    return jsonify({
        'problem_id': problem.id,
        'title': problem.title,
        'solved': solved,
        'passed': passed_count,
        'total': len(test_cases),
        'results': results,
    })
