from flask import Blueprint, jsonify, request
import re
from math import gcd

from app import db
from app.middleware.auth import token_required
from app.models.practice import PracticeProblem, PracticeAttempt, PracticeDraft
from app.models.skill_points import SkillPointTransaction
from app.routes.profile import update_streak_on_submit
from app.services.java_executor import get_java_executor
from app.services.skill_points_service import award_monthly_goal_completion, award_practice_problem_points, award_weekly_goal_completion, get_practice_points

practice_bp = Blueprint('practice', __name__)

LEVEL_ORDER = ['beginner', 'intermediate', 'advanced']
LEVEL_MIX = 0.0


def _practice_reward_key(problem_id: int) -> str:
    return f"problem:{problem_id}"


def _practice_earned_map(user_id: int):
    rows = SkillPointTransaction.query.filter_by(
        user_id=user_id,
        event_type='practice_problem_solved'
    ).all()
    return {row.event_key for row in rows}


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

    # ── EARLY EXIT: Order-sensitive array problems — generic expected_nums check ───
    # passes any permutation of the correct values; these require exact sequence.
    if title == 'reverse an array':
        try:
            il_ra = [p.strip() for p in input_data.strip().split('\n') if p.strip()]
            arr_ra = list(map(int, re.findall(r'-?\d+(?:\.\d+)?', il_ra[1] if len(il_ra) > 1 else il_ra[0])))
            out_ra = [int(float(x)) for x in re.findall(r'-?\d+(?:\.\d+)?', output)]
            return out_ra[-len(arr_ra):] == list(reversed(arr_ra))
        except Exception:
            return len(output) > 0

    if title == 'bubble sort':
        try:
            il_bs = [p.strip() for p in input_data.strip().split('\n') if p.strip()]
            arr_bs = list(map(int, re.findall(r'-?\d+(?:\.\d+)?', il_bs[1] if len(il_bs) > 1 else il_bs[0])))
            out_bs = [int(float(x)) for x in re.findall(r'-?\d+(?:\.\d+)?', output)]
            return out_bs[-len(arr_bs):] == sorted(arr_bs)
        except Exception:
            return len(output) > 0

    if title == 'remove duplicates':
        try:
            il_rd = [p.strip() for p in input_data.strip().split('\n') if p.strip()]
            arr_rd = list(map(int, re.findall(r'-?\d+(?:\.\d+)?', il_rd[1] if len(il_rd) > 1 else il_rd[0])))
            unique_rd = list(dict.fromkeys(arr_rd))
            out_rd = [int(float(x)) for x in re.findall(r'-?\d+(?:\.\d+)?', output)]
            return out_rd[-len(unique_rd):] == unique_rd
        except Exception:
            return len(output) > 0

    if title == 'array rotation (left by k)':
        try:
            il_ar = [p.strip() for p in input_data.strip().split('\n') if p.strip()]
            arr_ar = list(map(int, re.findall(r'-?\d+(?:\.\d+)?', il_ar[1])))
            k_ar = int(re.findall(r'-?\d+(?:\.\d+)?', il_ar[2])[0]) % len(arr_ar)
            rotated = arr_ar[k_ar:] + arr_ar[:k_ar]
            out_ar = [int(float(x)) for x in re.findall(r'-?\d+(?:\.\d+)?', output)]
            return out_ar[-len(rotated):] == rotated
        except Exception:
            return len(output) > 0

    if title == 'transpose a matrix':
        try:
            il_tm = [p.strip() for p in input_data.strip().split('\n') if p.strip()]
            n_tm = int(re.findall(r'-?\d+(?:\.\d+)?', il_tm[0])[0])
            mat_tm = [list(map(int, re.findall(r'-?\d+(?:\.\d+)?', il_tm[i + 1]))) for i in range(n_tm)]
            # Expected transposed sequence row-major: col 0 first, then col 1, ...
            expected_seq = [mat_tm[j][i] for i in range(n_tm) for j in range(n_tm)]
            out_tm = [int(float(x)) for x in re.findall(r'-?\d+(?:\.\d+)?', output)]
            return out_tm[-len(expected_seq):] == expected_seq
        except Exception:
            return len(output) > 0

    # ── EARLY EXIT: Count Even/Odd — generic expected_nums causes swap confusion ─
    # e.g. expected "Even: 2\nOdd: 3" — wrong "Even: 3\nOdd: 2" has both 2&3 in nums
    if title == 'count even and odd':
        try:
            il_ce = [p.strip() for p in input_data.strip().split('\n') if p.strip()]
            arr_ce = list(map(int, re.findall(r'-?\d+(?:\.\d+)?', il_ce[1] if len(il_ce) > 1 else il_ce[0])))
            even_ce = sum(1 for x in arr_ce if x % 2 == 0)
            odd_ce = len(arr_ce) - even_ce
            # Require each count to appear adjacent to its keyword
            e_ok = re.search(rf'even[^0-9]*{even_ce}|{even_ce}[^0-9]*even', output_lower) is not None
            o_ok = re.search(rf'odd[^0-9]*{odd_ce}|{odd_ce}[^0-9]*odd', output_lower) is not None
            return e_ok and o_ok
        except Exception:
            return 'even' in output_lower and 'odd' in output_lower

    # ── EARLY EXIT: Student Result — single-letter grades ("A","B","F") confuse ─
    # the generic check which matches any output containing that letter
    if title == 'student result system':
        try:
            il_sr = [p.strip() for p in input_data.strip().split('\n') if p.strip()]
            n_sr = int(re.findall(r'-?\d+(?:\.\d+)?', il_sr[0])[0])
            marks_sr = [int(float(x)) for x in re.findall(r'-?\d+(?:\.\d+)?', '\n'.join(il_sr[1:n_sr + 1]))]
            avg_sr = sum(marks_sr) / len(marks_sr)
            g_sr = 'a+' if avg_sr >= 90 else 'a' if avg_sr >= 80 else 'b' if avg_sr >= 70 else 'c' if avg_sr >= 60 else 'd' if avg_sr >= 50 else 'f'
            if g_sr == 'a+':
                return 'a+' in output_lower
            if g_sr == 'f':
                return any(w in output_lower for w in ['fail', 'grade f', 'grade: f']) or re.search(r'(?<![a-zA-Z])f(?![a-zA-Z])', output_lower) is not None
            chk = (f'grade {g_sr}' in output_lower or f'grade: {g_sr}' in output_lower
                   or output_lower.strip() == g_sr
                   or re.search(rf'(?<![a-zA-Z]){g_sr}(?![a-zA-Z+])', output_lower) is not None)
            return chk and (g_sr != 'a' or 'a+' not in output_lower)
        except Exception:
            return any(w in output_lower for w in ['grade', 'pass', 'fail', 'average'])

    # ── EARLY EXIT: Reverse a String — case-sensitive; generic check lowercases ─
    # "AVAJ" would match expected "avaj" via generic check's output_lower comparison
    if title == 'reverse a string':
        return input_data.strip()[::-1] in output

    # ── EARLY EXIT: Remove Spaces — generic check matches "abc" inside "abc spaces ─
    # removed" because expected "abc" is a substring of the wrong output.
    # Use whole-word boundary checks to avoid matching "space" inside "nospaces".
    if title == 'remove spaces':
        expected_rs = input_data.strip().replace(' ', '')
        if expected_rs not in output:
            return False
        # Reject if suspicious context words appear as whole words
        return not any(re.search(rf'\b{w}\b', output_lower) for w in ['space', 'spaces', 'removed', 'kept', 'original'])

    # ── EARLY EXIT: Menu-Driven Program — generic check matches "executed" anywhere ─
    # so "Option 5 executed" passes when choice 1 was entered
    if title == 'menu-driven program':
        il_md = [p.strip() for p in input_data.strip().split('\n') if p.strip()]
        choices_md = []
        for v in il_md:
            try:
                choices_md.append(int(v))
            except Exception:
                pass
        valid_md   = [c for c in choices_md if c in (1, 2, 3)]
        invalid_md = [c for c in choices_md if c not in (1, 2, 3, 4)]
        exit_md    = [c for c in choices_md if c == 4]
        if invalid_md:
            return any(w in output_lower for w in ['invalid', 'error', 'wrong'])
        if valid_md:
            exec_ok = 'executed' in output_lower or 'done' in output_lower
            num_ok  = any(str(c) in output for c in valid_md)
            return exec_ok and num_ok
        if exit_md:
            return any(w in output_lower for w in ['exit', 'bye', 'goodbye', 'exiting'])
        return len(output) > 0

    # ── EARLY EXIT: Quiz Application must match exact "X/5" score string ────
    # (The generic expected_nums check below is unreliable for "X/Y" fractions.)
    if title == 'quiz application':
        try:
            correct_answers = ['B', 'C', 'B', 'A', 'B']
            il_q = [p.strip() for p in input_data.strip().split('\n') if p.strip()]
            user_answers = [a.upper() for a in il_q if a.strip().upper() in ('A', 'B', 'C', 'D')]
            score = sum(1 for i, a in enumerate(user_answers[:len(correct_answers)]) if a == correct_answers[i])
            return f"{score}/{len(correct_answers)}" in output
        except Exception:
            return 'score' in output_lower

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
            # Case-sensitive: "AVAJ" is not a valid reverse of "java"
            return input_data.strip()[::-1] in output

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
            expected_rs = input_data.strip().replace(' ', '').lower()
            if expected_rs not in output_lower:
                return False
            # Reject outputs where the result is followed by extra unrelated words
            # (e.g. "abc spaces removed" falsely contains "abc")
            return not any(w in output_lower for w in ['space', 'removed', 'kept', 'original', 'without'])

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
            # If compressed is shorter → expect comp in output
            # If compressed is same length or longer → expect original; also accept comp (some impls always compress)
            if len(comp) < len(s):
                return comp in output
            return s in output or comp in output

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
            # Handled by early-exit block above; fallback only
            il = input_lines()
            n = int(_extract_numbers(il[0])[0])
            marks = list(map(int, _extract_numbers('\n'.join(il[1:n + 1]))))
            avg = sum(marks) / len(marks)
            g = 'a+' if avg >= 90 else 'a' if avg >= 80 else 'b' if avg >= 70 else 'c' if avg >= 60 else 'd' if avg >= 50 else 'f'
            if g == 'a+':
                return 'a+' in output_lower
            if g == 'f':
                return any(w in output_lower for w in ['fail', 'grade f', 'grade: f']) or re.search(r'(?<![a-zA-Z])f(?![a-zA-Z])', output_lower) is not None
            chk = (f'grade {g}' in output_lower or f'grade: {g}' in output_lower
                   or output_lower.strip() == g
                   or re.search(rf'(?<![a-zA-Z]){g}(?![a-zA-Z+])', output_lower) is not None)
            return chk and (g != 'a' or 'a+' not in output_lower)

        if title == 'employee salary system':
            # Input: single basic salary. HRA=20%, DA=10%, Gross=Basic+HRA+DA
            values = input_nums()
            basic = values[0] if values else 0
            hra = round(basic * 0.20, 2)
            da = round(basic * 0.10, 2)
            gross = basic + hra + da
            return has_num(gross, 1)

        if title == 'menu-driven program':
            # Choices 1-3 valid, 4=Exit, anything else = invalid
            # Scan ALL inputs: prioritise invalid > valid > exit
            il = input_lines()
            choices = []
            for v in il:
                try:
                    choices.append(int(v))
                except Exception:
                    pass
            valid   = [c for c in choices if c in (1, 2, 3)]
            invalid = [c for c in choices if c not in (1, 2, 3, 4)]
            exit_ch = [c for c in choices if c == 4]
            if invalid:
                return any(w in output_lower for w in ['invalid', 'error', 'wrong'])
            if valid:
                # Require the valid choice NUMBER to appear alongside 'executed'/'done'
                # so "Option 5 executed" doesn't pass when choice 1 was entered
                exec_ok = 'executed' in output_lower or 'done' in output_lower
                num_ok = any(str(c) in output for c in valid)
                return exec_ok and num_ok
            if exit_ch:
                return any(w in output_lower for w in ['exit', 'bye', 'goodbye', 'exiting'])
            return len(output) > 0

        if title == 'custom exception demo':
            # age < 18 → throws exception, age >= 18 → valid/access granted
            age = int(input_nums()[0])
            if age < 18:
                # 'age' removed — too broad (e.g. "Age is negative" would match)
                return any(w in output_lower for w in ['exception', 'invalid', 'error', 'must be', 'underage', 'minor'])
            return any(w in output_lower for w in ['granted', 'valid', 'welcome', 'success', 'access', 'allowed'])

        if title == 'number guessing game':
            return any(w in output_lower for w in ['high', 'low', 'correct', 'guess', 'attempt', 'try'])

        # ── ADVANCED ─────────────────────────────────────────────────────────

        if title == 'student management system':
            il = input_lines()
            action = il[0] if il else ''
            # Find the LAST meaningful action in the input sequence
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3', '4'):
                    last_action = v
                    last_action_idx = i
            if last_action == '3':
                term = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                if term:
                    return term.lower() in output_lower or 'not found' in output_lower
                return 'not found' in output_lower
            if last_action == '2':
                # Display all students — must show at least the added students
                added_names = []
                for i, v in enumerate(il):
                    if v == '1' and i + 1 < len(il):
                        added_names.append(il[i + 1].lower())
                if added_names:
                    return any(n in output_lower for n in added_names)
                return len(lines) > 1
            if action == '1':
                name = il[1] if len(il) > 1 else ''
                return ('added' in output_lower or 'success' in output_lower) and (not name or name.lower() in output_lower or 'student' in output_lower)
            return len(output) > 5

        if title == 'library system':
            il = input_lines()
            action = il[0] if il else ''
            # Reject if any exceptions in output
            if any(w in output_lower for w in ['exception', 'nosuchelementexception', 'error']):
                return False
            # Find the LAST meaningful action
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3', '4'):
                    last_action = v
                    last_action_idx = i
            if last_action == '3':
                keyword = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                if not keyword:
                    return 'not found' in output_lower
                keyword_match = keyword.lower() in output_lower
                expects_not_found = any(w in expected_lower for w in ['not found', 'no books'])
                if expects_not_found:
                    return keyword_match or any(w in output_lower for w in ['not found', 'no books'])
                return keyword_match
            if last_action == '2':
                # List books — check that a previously added book title appears
                added_books = []
                for i, v in enumerate(il):
                    if v == '1' and i + 1 < len(il):
                        added_books.append(il[i + 1].lower())
                if added_books:
                    return any(b in output_lower for b in added_books)
                return len(lines) > 1
            if action == '1':
                book = il[1] if len(il) > 1 else ''
                return 'added' in output_lower or 'book' in output_lower
            return len(output) > 5

        if title == 'contact book':
            il = input_lines()
            # Find the LAST meaningful action
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3', '4'):  # exclude exit '5'
                    last_action = v
                    last_action_idx = i
            if last_action == '4':
                name = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                return any(w in output_lower for w in ['deleted', 'removed', 'not found'])
            if last_action == '3':
                name = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                if name:
                    return name.lower() in output_lower or 'not found' in output_lower
                return 'not found' in output_lower
            if last_action == '2':
                # View all — check if previously added contacts appear
                added_names = []
                for i, v in enumerate(il):
                    if v == '1' and i + 1 < len(il):
                        added_names.append(il[i + 1].lower())
                if added_names:
                    return any(n in output_lower for n in added_names)
                return len(lines) >= 1
            action = il[0] if il else ''
            if action == '1':
                return 'saved' in output_lower or 'added' in output_lower or 'contact' in output_lower
            return len(output) > 5

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
            # Find the LAST meaningful action
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3', '4'):  # exclude exit '5'
                    last_action = v
                    last_action_idx = i
            if last_action == '4':
                return any(w in output_lower for w in ['total', 'bill', 'empty', 'amount']) or len(nums) > 0
            if last_action == '3':
                item = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                return any(w in output_lower for w in ['removed', 'not found'])
            if last_action == '2':
                added_items = []
                for i, v in enumerate(il):
                    if v == '1' and i + 1 < len(il):
                        added_items.append(il[i + 1].lower())
                if added_items:
                    return any(item in output_lower for item in added_items)
                return len(lines) > 0
            action = il[0] if il else ''
            if action == '1':
                item = il[1] if len(il) > 1 else ''
                return 'added' in output_lower or (item and item.lower() in output_lower)
            return len(output) > 5

        if title == 'expense tracker':
            il = input_lines()
            # Find the LAST meaningful action
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3', '4'):  # exclude exit '5'
                    last_action = v
                    last_action_idx = i
            if last_action == '4':
                # Total — check that a number appears in output
                # Extract amounts from Add actions (every 4th line after action '1': cat, desc, amount)
                amounts = []
                i = 0
                while i < len(il):
                    if il[i] == '1' and i + 3 < len(il):
                        try:
                            amounts.append(float(il[i + 3]))
                        except ValueError:
                            pass
                        i += 4
                    else:
                        i += 1
                if amounts:
                    return has_num(sum(amounts), 5) or 'total' in output_lower
                return 'total' in output_lower or len(nums) > 0
            if last_action == '3':
                cat = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                return cat.lower() in output_lower or 'no expenses' in output_lower
            if last_action == '2':
                # View all — check that added expense data appears
                added_cats = []
                for i, v in enumerate(il):
                    if v == '1' and i + 1 < len(il):
                        added_cats.append(il[i + 1].lower())
                if added_cats:
                    return any(c in output_lower for c in added_cats)
                return len(lines) > 0
            action = il[0] if il else ''
            if action == '1':
                return 'added' in output_lower or 'expense' in output_lower
            return len(output) > 0

        if title == 'quiz application':
            # Handled by early-exit block above; this is a safety fallback
            return 'score' in output_lower

        if title == 'voting system':
            il = input_lines()
            # The program processes voter_id/candidate pairs until empty line
            # Valid candidates: Alice, Bob, Carol
            valid_candidates = {'alice', 'bob', 'carol'}
            voter_ids_seen = []
            pairs = []
            i = 0
            while i + 1 < len(il):
                voter_id = il[i]
                candidate = il[i + 1]
                pairs.append((voter_id, candidate))
                voter_ids_seen.append(voter_id.lower())
                i += 2
            if not pairs:
                return len(output) > 0
            # Check the LAST pair's expected result
            last_vid, last_cand = pairs[-1]
            # Duplicate vote check: same voter ID used earlier
            prior_vids = [v.lower() for v, c in pairs[:-1]]
            if last_vid.lower() in prior_vids:
                return any(w in output_lower for w in ['already', 'voted', 'used', 'duplicate'])
            # Invalid candidate check
            if last_cand.lower() not in valid_candidates:
                return any(w in output_lower for w in ['invalid', 'candidate', 'error'])
            # Valid vote
            return any(w in output_lower for w in ['cast', 'recorded', 'voted', 'registered', 'success'])

        if title == 'parking lot system':
            il = input_lines()
            # Find the LAST meaningful action (exclude exit '4')
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3'):
                    last_action = v
                    last_action_idx = i
            if last_action == '3':
                return any(w in output_lower for w in ['slot', 'free', 'occupied', 'status']) or len(lines) > 1
            if last_action == '2':
                plate = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                return any(w in output_lower for w in ['removed', 'left', 'not found'])
            if last_action == '1':
                plate = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                return any(w in output_lower for w in ['assigned', 'parked', 'full', 'slot'])
            return len(output) > 0

        if title == 'bank account system':
            il = input_lines()
            # Find the LAST meaningful action
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3', '4'):  # exclude exit '5'
                    last_action = v
                    last_action_idx = i
            if last_action == '3':
                return any(w in output_lower for w in ['withdraw', 'insufficient', 'balance', 'not found'])
            if last_action == '2':
                return 'deposit' in output_lower or any(w in output_lower for w in ['success', 'added', 'balance'])
            if last_action == '4':
                return len(lines) > 0
            if last_action == '1':
                return any(w in output_lower for w in ['created', 'account']) or len(nums) > 0
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
            # Find the LAST meaningful action (exclude exit '6')
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3', '4', '5'):
                    last_action = v
                    last_action_idx = i
            if last_action == '2':
                return any(w in output_lower for w in ['complete', 'done', 'not found'])
            if last_action == '3':
                return any(w in output_lower for w in ['removed', 'deleted', 'not found'])
            if last_action in ('4', '5'):
                # View tasks — check if previously added task name appears
                added_names = []
                for i, v in enumerate(il):
                    if v == '1' and i + 1 < len(il):
                        added_names.append(il[i + 1].lower())
                if added_names:
                    return any(n in output_lower for n in added_names) or 'no' in output_lower
                return len(lines) > 0 or 'no' in output_lower
            if last_action == '1':
                name = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                return 'added' in output_lower
            return len(output) > 0

        if title == 'inventory system':
            il = input_lines()
            # Find the LAST meaningful action
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3', '4'):  # exclude exit '5'
                    last_action = v
                    last_action_idx = i
            if last_action == '3':
                return any(w in output_lower for w in ['sold', 'insufficient', 'stock', 'not enough'])
            if last_action == '2':
                return any(w in output_lower for w in ['restocked', 'updated', 'added', 'quantity'])
            if last_action == '4':
                return len(lines) > 0
            if last_action == '1':
                return any(w in output_lower for w in ['added', 'product'])
            return len(output) > 0

        if title == 'ticket booking system':
            il = input_lines()
            # Find the LAST meaningful action
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3', '4'):
                    last_action = v
                    last_action_idx = i
            if last_action == '2':
                seat_to_cancel = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                return any(w in output_lower for w in ['cancelled', 'canceled', 'not booked', 'removed', 'seat not'])
            if last_action == '3':
                return len(lines) > 0
            if last_action == '1':
                seat = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                # Check if this same seat was booked earlier in the sequence
                booked_seats = []
                for i, v in enumerate(il):
                    if v == '1' and i + 1 < len(il) and i < last_action_idx:
                        booked_seats.append(il[i + 1])
                if seat in booked_seats:
                    return any(w in output_lower for w in ['already', 'booked', 'taken'])
                return any(w in output_lower for w in ['booked', 'confirmed', 'ticket', 'success', 'seat'])
            return len(output) > 5

        if title == 'restaurant billing system':
            il = input_lines()
            # Find the LAST meaningful action
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3', '4'):  # exclude exit '5'
                    last_action = v
                    last_action_idx = i
            if last_action == '4':
                return any(w in output_lower for w in ['total', 'bill', 'empty', 'order']) or len(nums) > 0
            if last_action == '2':
                return any(w in output_lower for w in ['removed', 'not found'])
            if last_action == '3':
                # View order — check if added items appear
                added_items = []
                for i, v in enumerate(il):
                    if v == '1' and i + 1 < len(il):
                        added_items.append(il[i + 1].lower())
                if added_items:
                    return any(item in output_lower for item in added_items)
                return len(lines) > 0
            if last_action == '1':
                item = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                return 'added' in output_lower or (item and item.lower() in output_lower)
            return len(output) > 0

        if title == 'simple chat simulation':
            il = input_lines()
            # Filter out 'exit' from messages
            messages = [m for m in il if m.lower() != 'exit']
            if not messages:
                return any(w in output_lower for w in ['no messages', 'empty', 'no chat'])
            # Check that messages appear in output (as "You: <msg>")
            found_messages = sum(1 for m in messages if m.lower() in output_lower)
            # Also check message count
            count_str = f"{len(messages)} message"
            has_count = count_str in output_lower
            return found_messages > 0 or has_count or any(w in output_lower for w in ['message', 'sent'])

        if title == 'simple login system':
            il = input_lines()
            # Find the LAST meaningful action
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3'):
                    last_action = v
                    last_action_idx = i
            if last_action == '1':
                return any(w in output_lower for w in ['registered', 'success'])
            if last_action == '2':
                username = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                # Count how many failed login attempts for this user
                # Check if user was registered earlier
                registered_users = {}
                failed_attempts = 0
                for i, v in enumerate(il):
                    if v == '1' and i + 2 < len(il):
                        registered_users[il[i + 1].lower()] = il[i + 2]
                    if v == '2' and i + 2 < len(il):
                        u = il[i + 1].lower()
                        p = il[i + 2]
                        if u in registered_users and registered_users[u] != p:
                            failed_attempts += 1
                # Unregistered user
                if username.lower() not in registered_users:
                    return any(w in output_lower for w in ['not found', 'invalid', 'unknown'])
                # Locked after 3 failures
                if failed_attempts >= 3:
                    return any(w in output_lower for w in ['locked', 'lock'])
                # Check last login attempt
                password = il[last_action_idx + 2] if last_action_idx + 2 < len(il) else ''
                if registered_users.get(username.lower()) == password:
                    return any(w in output_lower for w in ['welcome', 'success']) or username.lower() in output_lower
                return any(w in output_lower for w in ['incorrect', 'wrong', 'invalid', 'attempt', 'locked'])
            return len(output) > 0

        if title == 'employee management + sort by salary':
            il = input_lines()
            # Find the LAST meaningful action
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3', '4'):  # exclude exit '5'
                    last_action = v
                    last_action_idx = i
            if last_action == '4':
                dept = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                if dept:
                    # Check if added employees in that dept appear, or "no employees"
                    added_in_dept = []
                    for i, v in enumerate(il):
                        if v == '1' and i + 2 < len(il) and il[i + 2].lower() == dept.lower():
                            added_in_dept.append(il[i + 1].lower())
                    if added_in_dept:
                        return any(n in output_lower for n in added_in_dept) or 'no employees' in output_lower
                return dept.lower() in output_lower or 'no employees' in output_lower
            if last_action == '3':
                sort_choice = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else '1'
                # Extract salary numbers from output (filter out small numbers that might be indices)
                salary_nums = [float(n) for n in nums if float(n) > 100]
                if len(salary_nums) >= 2:
                    if sort_choice == '2':
                        return salary_nums == sorted(salary_nums, reverse=True)
                    return salary_nums == sorted(salary_nums)
                return len(lines) > 0
            if last_action == '2':
                return len(lines) > 0
            if last_action == '1':
                name = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                return 'added' in output_lower or 'employee' in output_lower
            return len(output) > 5

        if title == 'mini banking transaction history':
            il = input_lines()
            # Find the LAST meaningful action (exclude exit '5')
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3', '4'):
                    last_action = v
                    last_action_idx = i
            # Simulate balance to validate
            balance = 0.0
            i = 0
            while i < len(il):
                if il[i] == '1' and i + 1 < len(il):
                    try:
                        balance += float(il[i + 1])
                    except ValueError:
                        pass
                    i += 2
                elif il[i] == '2' and i + 1 < len(il):
                    try:
                        amt = float(il[i + 1])
                        if amt <= balance:
                            balance -= amt
                    except ValueError:
                        pass
                    i += 2
                else:
                    i += 1
            if last_action == '2':
                amt_str = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else '0'
                try:
                    amt = float(amt_str)
                except ValueError:
                    amt = 0
                # Check if it's an insufficient funds case (withdraw more than current balance before this action)
                pre_balance = 0.0
                j = 0
                while j < last_action_idx:
                    if il[j] == '1' and j + 1 < len(il):
                        try:
                            pre_balance += float(il[j + 1])
                        except ValueError:
                            pass
                        j += 2
                    elif il[j] == '2' and j + 1 < len(il):
                        try:
                            w = float(il[j + 1])
                            if w <= pre_balance:
                                pre_balance -= w
                        except ValueError:
                            pass
                        j += 2
                    else:
                        j += 1
                if amt > pre_balance:
                    return any(w in output_lower for w in ['insufficient', 'not enough', 'failed', 'cannot'])
                return any(w in output_lower for w in ['withdraw', 'successful', 'balance', 'debited'])
            if last_action == '4':
                # Balance display must show the actual number (not just the word "balance")
                return has_num(balance, 1)
            if last_action == '3':
                return len(lines) > 0 or 'no transaction' in output_lower or 'deposit' in output_lower
            if last_action == '1':
                return any(w in output_lower for w in ['deposit', 'successful', 'credited', 'added', 'balance'])
            return len(output) > 5

        if title == 'course enrollment system':
            il = input_lines()
            # Find the LAST meaningful action (exclude exit '5')
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3', '4'):
                    last_action = v
                    last_action_idx = i
            if last_action == '2':
                # Enroll — check if this is a duplicate or capacity issue
                student_id = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                course_id = il[last_action_idx + 2] if last_action_idx + 2 < len(il) else ''
                # Check if this student was already enrolled in this course earlier
                enrolled_pairs = []
                capacity_map = {}
                for i, v in enumerate(il):
                    if v == '1' and i + 2 < len(il):
                        cid = il[i + 1]
                        try:
                            cap = int(il[i + 2])
                        except ValueError:
                            cap = 999
                        capacity_map[cid] = cap
                    if v == '2' and i + 2 < len(il) and i < last_action_idx:
                        enrolled_pairs.append((il[i + 1], il[i + 2]))
                # Duplicate enrollment
                if (student_id, course_id) in enrolled_pairs:
                    return any(w in output_lower for w in ['already', 'duplicate', 'enrolled'])
                # Capacity check
                enrolled_in_course = sum(1 for s, c in enrolled_pairs if c == course_id)
                cap = capacity_map.get(course_id, 999)
                if enrolled_in_course >= cap:
                    return any(w in output_lower for w in ['full', 'capacity', 'no seats'])
                # Normal enrollment
                return any(w in output_lower for w in ['enrolled', 'success'])
            if last_action == '3':
                return any(w in output_lower for w in ['dropped', 'not enrolled', 'unenrolled', 'removed'])
            if last_action == '4':
                return len(lines) > 0 or 'not enrolled' in output_lower
            if last_action == '1':
                return any(w in output_lower for w in ['added', 'course', 'created'])
            return len(output) > 5

        if title == 'hotel room booking':
            il = input_lines()
            # Find the LAST meaningful action
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3', '4'):  # exclude exit '5'
                    last_action = v
                    last_action_idx = i
            if last_action == '3':
                return any(w in output_lower for w in ['invoice', 'total', 'checkout', 'checked out', 'bill', 'not booked']) or len(nums) > 0
            if last_action == '2':
                # Book — check if the room was already booked earlier
                room_no = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                booked_rooms = []
                for i, v in enumerate(il):
                    if v == '2' and i + 1 < len(il) and i < last_action_idx:
                        booked_rooms.append(il[i + 1])
                if room_no in booked_rooms:
                    return any(w in output_lower for w in ['not available', 'occupied', 'already booked', 'already'])
                return any(w in output_lower for w in ['booked', 'reserved', 'confirmed', 'room'])
            if last_action == '1':
                return len(lines) > 0 or 'no rooms' in output_lower
            if last_action == '4':
                return len(lines) > 0 or 'no bookings' in output_lower
            return len(output) > 5

        if title == 'stack implementation (manual)':
            il = input_lines()
            # Find the LAST meaningful action (exclude exit '5')
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3', '4'):
                    last_action = v
                    last_action_idx = i
            if last_action == '4':
                expr = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                stack = []
                balanced = True
                pairs_map = {')': '(', '}': '{', ']': '['}
                for ch in expr:
                    if ch in '({[':
                        stack.append(ch)
                    elif ch in ')}]':
                        if not stack or stack[-1] != pairs_map[ch]:
                            balanced = False
                            break
                        stack.pop()
                if stack:
                    balanced = False
                if balanced:
                    return 'balanced' in output_lower and 'unbalanced' not in output_lower
                else:
                    return 'unbalanced' in output_lower or 'not balanced' in output_lower
            if last_action == '2':
                # Pop — simulate the stack to know what should be popped
                stack_vals = []
                for i, v in enumerate(il):
                    if v == '1' and i + 1 < len(il):
                        try:
                            stack_vals.append(int(il[i + 1]))
                        except ValueError:
                            pass
                    if v == '2' and i == last_action_idx:
                        break
                    if v == '2' and i < last_action_idx:
                        if stack_vals:
                            stack_vals.pop()
                if not stack_vals:
                    return any(w in output_lower for w in ['underflow', 'empty', 'stack underflow'])
                expected_pop = stack_vals[-1]
                # Must confirm the CORRECT value was popped — keyword alone is not enough
                return has_num(expected_pop, 0.1) and ('popped' in output_lower or str(expected_pop) in output)
            if last_action == '1':
                return any(w in output_lower for w in ['pushed', 'overflow', 'full', 'push'])
            if last_action == '3':
                return len(nums) > 0 or 'empty' in output_lower
            return len(output) > 5

        if title == 'queue implementation (manual)':
            il = input_lines()
            # Find the LAST meaningful action (exclude exit '5')
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3', '4'):
                    last_action = v
                    last_action_idx = i
            if last_action == '4':
                # Printer demo — check if enqueued items appear as jobs
                enqueued = []
                for i, v in enumerate(il):
                    if v == '1' and i + 1 < len(il):
                        enqueued.append(il[i + 1].lower())
                if enqueued:
                    return any(item in output_lower for item in enqueued) or 'job' in output_lower
                return any(w in output_lower for w in ['job', 'queue', 'no jobs', 'pending']) or len(lines) > 0
            if last_action == '2':
                # Dequeue — simulate the queue
                queue_items = []
                dequeued_count = 0
                for i, v in enumerate(il):
                    if v == '1' and i + 1 < len(il):
                        queue_items.append(il[i + 1])
                    if v == '2' and i < last_action_idx:
                        if queue_items:
                            queue_items.pop(0)
                        dequeued_count += 1
                if not queue_items:
                    return any(w in output_lower for w in ['empty', 'underflow', 'queue empty', 'queue is empty'])
                first_item = queue_items[0].lower()
                return (first_item in output_lower or
                        any(w in output_lower for w in ['processing', 'dequeued', 'serving']))
            if last_action == '1':
                return any(w in output_lower for w in ['queued', 'added', 'full', 'enqueue', 'enqueued'])
            if last_action == '3':
                return len(output) > 0 or 'empty' in output_lower
            return len(output) > 5

        if title == 'e-voting with id validation':
            if 'already' in output_lower or 'already voted' in output_lower:
                return any(w in expected_lower for w in ['already', 'voted'])
            if 'invalid' in output_lower or 'error: invalid' in output_lower:
                return any(w in expected_lower for w in ['invalid', 'not registered', 'not found'])
            if 'recorded' in output_lower or 'cast' in output_lower or 'voted' in output_lower:
                return any(w in expected_lower for w in ['recorded', 'cast', 'voted'])
            return len(output) > 0

        if title == 'multi-user scoreboard system':
            il = input_lines()
            # Find the LAST meaningful action
            last_action = None
            last_action_idx = -1
            for i, v in enumerate(il):
                if v in ('1', '2', '3', '4', '5', '6'):
                    last_action = v
                    last_action_idx = i
            if last_action == '3':
                # Leaderboard — simulate scores and check descending order
                players = {}
                for i, v in enumerate(il):
                    if v == '1' and i + 2 < len(il):
                        name = il[i + 1]
                        try:
                            score = int(il[i + 2])
                        except ValueError:
                            score = 0
                        players[name] = score
                    if v == '2' and i + 2 < len(il):
                        name = il[i + 1]
                        try:
                            pts = int(il[i + 2])
                        except ValueError:
                            pts = 0
                        if name in players:
                            players[name] += pts
                # Check that scores appear in descending order in output
                score_nums = [float(n) for n in nums if float(n) > 0]
                if len(score_nums) >= 2:
                    return score_nums == sorted(score_nums, reverse=True)
                # Fallback: check that highest score player name appears
                if players:
                    top_player = max(players, key=players.get)
                    return top_player.lower() in output_lower or len(lines) > 0
                return len(lines) > 0
            if last_action == '4':
                # Top N — check if player names or scores appear
                n_val = int(_extract_numbers(il[last_action_idx + 1])[0]) if last_action_idx + 1 < len(il) and _extract_numbers(il[last_action_idx + 1]) else 1
                # Check if any added player names appear in output
                added_names = []
                for i, v in enumerate(il):
                    if v == '1' and i + 1 < len(il):
                        added_names.append(il[i + 1].lower())
                if added_names:
                    return any(n in output_lower for n in added_names)
                return len(lines) >= 1
            if last_action == '2':
                return any(w in output_lower for w in ['updated', 'score', 'success']) or len(nums) > 0
            if last_action == '1':
                name = il[last_action_idx + 1] if last_action_idx + 1 < len(il) else ''
                return 'added' in output_lower or (name and name.lower() in output_lower)
            if last_action == '5':
                return len(output) > 0
            return len(output) > 5

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
    earned_keys = _practice_earned_map(current_user.id)
    result = []
    for p in problems:
        summary = p.to_summary()
        summary['attempt_status'] = attempted_ids.get(p.id)
        summary['has_draft'] = p.id in drafted_ids
        summary['earnable_points'] = get_practice_points(p.level)
        summary['points_earned'] = _practice_reward_key(p.id) in earned_keys
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
    earned_keys = _practice_earned_map(current_user.id)
    payload = []
    for p in problems:
        item = p.to_summary()
        item['attempt_status'] = attempted_ids.get(p.id)
        item['has_draft'] = p.id in drafted_ids
        item['earnable_points'] = get_practice_points(p.level)
        item['points_earned'] = _practice_reward_key(p.id) in earned_keys
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
    detail['earnable_points'] = get_practice_points(problem.level)
    detail['points_earned'] = bool(SkillPointTransaction.query.filter_by(
        user_id=current_user.id,
        event_type='practice_problem_solved',
        event_key=_practice_reward_key(problem_id)
    ).first())
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
    problem = PracticeProblem.query.get_or_404(problem_id)
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
        award_practice_problem_points(current_user, problem_id, problem.level)
        award_weekly_goal_completion(current_user)
        award_monthly_goal_completion(current_user)
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
        problem = PracticeProblem.query.get(attempt.problem_id)
        if problem:
            award_practice_problem_points(current_user, attempt.problem_id, problem.level)
            award_weekly_goal_completion(current_user)
            award_monthly_goal_completion(current_user)
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
                update_streak_on_submit(current_user)
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
        verifier_flow = ''
        attempted_variants = 0

        for candidate_input in input_variants:
            attempted_variants += 1
            used_input = candidate_input
            run = executor.compile_and_execute(code, input_data=candidate_input)
            actual_output = str(run.get('output', '')).strip()
            can_verify = bool(run.get('success')) or bool(actual_output)
            if can_verify:
                if _verify_output(problem.title, candidate_input, actual_output, expected_output):
                    success = True
                    used_input = candidate_input
                    if bool(run.get('success')):
                        verifier_flow = (
                            f"Variant {attempted_variants}/{len(input_variants)} compiled and verifier matched expected output."
                        )
                    else:
                        verifier_flow = (
                            f"Variant {attempted_variants}/{len(input_variants)} had runtime failure after producing output, but verifier matched expected output."
                        )
                    break
            if not bool(run.get('success')):
                verifier_flow = (
                    f"Variant {attempted_variants}/{len(input_variants)} failed during compile/execute."
                )

        if run is None:
            run = {'errors': []}
        if not success and not verifier_flow:
            verifier_flow = (
                f"Tried {attempted_variants} input variant(s). Output did not satisfy verifier."
            )
        if success:
            passed_count += 1

        results.append({
            'index': idx,
            'input': original_input,
            'used_input': used_input.strip(),
            'attempted_variants': attempted_variants,
            'verifier_flow': verifier_flow,
            'expected_output': expected_output,
            'actual_output': actual_output,
            'success': success,
            'errors': run.get('errors', []),
        })

    solved = passed_count == len(test_cases)
    points_awarded = 0
    weekly_bonus_awarded = 0
    monthly_bonus_awarded = 0
    persist_attempt(solved, passed_count, len(test_cases))
    if solved:
        awarded, points_awarded = award_practice_problem_points(current_user, problem.id, problem.level)
        if not awarded:
            points_awarded = 0
        weekly_awarded, weekly_bonus_awarded, _ = award_weekly_goal_completion(current_user)
        if not weekly_awarded:
            weekly_bonus_awarded = 0
        monthly_awarded, monthly_bonus_awarded, _ = award_monthly_goal_completion(current_user)
        if not monthly_awarded:
            monthly_bonus_awarded = 0
        db.session.commit()
    return jsonify({
        'problem_id': problem.id,
        'title': problem.title,
        'solved': solved,
        'passed': passed_count,
        'total': len(test_cases),
        'results': results,
        'points_awarded': points_awarded,
        'weekly_bonus_awarded': weekly_bonus_awarded,
        'monthly_bonus_awarded': monthly_bonus_awarded,
        'current_points': int(getattr(current_user, 'total_points', 0) or 0),
    }), 200
