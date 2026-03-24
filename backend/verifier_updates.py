# Replace these blocks in _verify_output() in practice.py
# Find each 'if title ==' block and replace with the version below

# ── GRADE SYSTEM ─────────────────────────────────────────────────────────────
        if title == 'grade system':
            m = int(input_nums()[0])
            if m < 0 or m > 100:
                return 'invalid' in output_lower
            g = 'a+' if m>=90 else 'a' if m>=80 else 'b' if m>=70 else 'c' if m>=60 else 'd' if m>=50 else 'f'
            return ('fail' in output_lower or 'f' in output_lower) if g == 'f' else g in output_lower

# ── TEMPERATURE CONVERTER ────────────────────────────────────────────────────
        if title == 'temperature converter':
            il = input_lines()
            val = float(_extract_numbers(il[0])[0])
            unit = il[1].strip().upper() if len(il) > 1 else 'C'
            if unit not in ('C', 'F'):
                return 'invalid' in output_lower
            result = round(val * 9/5 + 32, 2) if unit == 'C' else round((val - 32) * 5/9, 2)
            positive_nums = [n for n in nums if not n.startswith('-')]
            if result >= 0:
                return any(abs(float(n) - result) <= 0.1 for n in positive_nums) if positive_nums else False
            return has_num(result, 0.1)

# ── FACTORIAL CALCULATOR ─────────────────────────────────────────────────────
        if title == 'factorial calculator':
            n = int(input_nums()[0])
            if n < 0:
                return 'invalid' in output_lower
            r = 1
            for i in range(2, n+1): r *= i
            return str(r) in nums

# ── PRIME NUMBER CHECKER ─────────────────────────────────────────────────────
        if title == 'prime number checker':
            n = int(input_nums()[0])
            if n < 0:
                return 'invalid' in output_lower
            is_p = n >= 2 and all(n % i != 0 for i in range(2, int(n**0.5)+1))
            if 'not prime' in output_lower:
                return not is_p
            elif 'prime' in output_lower:
                return is_p
            return False

# ── LEAP YEAR CHECKER ────────────────────────────────────────────────────────
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

# ── BASIC CALCULATOR ─────────────────────────────────────────────────────────
        if title == 'basic calculator':
            il = input_lines()
            a, b, op = float(il[0]), float(il[1]), il[2].strip()
            if op == '/' and b == 0:
                return any(w in output_lower for w in ['zero', 'cannot', 'divide', 'undefined', 'error'])
            res = {'+':(a+b), '-':(a-b), '*':(a*b), '/':(a/b if b!=0 else None)}.get(op)
            if res is None:
                return 'invalid' in output_lower
            return has_num(res, 0.01)

# ── POWER CALCULATOR ─────────────────────────────────────────────────────────
        if title == 'power calculator':
            v = list(map(int, input_nums()))
            if v[1] < 0:
                return 'invalid' in output_lower
            return str(v[0]**v[1]) in nums

# ── PALINDROME NUMBER ────────────────────────────────────────────────────────
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

# ── ARMSTRONG NUMBER ─────────────────────────────────────────────────────────
        if title == 'armstrong number':
            s = input_data.strip()
            if s.startswith('-'):
                return 'invalid' in output_lower
            d = len(s)
            is_a = sum(int(c)**d for c in s if c.isdigit()) == int(s)
            if 'not armstrong' in output_lower or 'not an armstrong' in output_lower:
                return not is_a
            elif 'armstrong' in output_lower:
                return is_a
            return False

# ── FIBONACCI SERIES ─────────────────────────────────────────────────────────
        if title == 'fibonacci series':
            n = int(input_nums()[0])
            if n <= 0:
                return 'invalid' in output_lower
            fibs = [0, 1]
            while len(fibs) < n: fibs.append(fibs[-1]+fibs[-2])
            fibs = fibs[:n]
            out = [int(float(x)) for x in nums]
            return out[-len(fibs):] == fibs

# ── GCD AND LCM ──────────────────────────────────────────────────────────────
        if title == 'gcd and lcm':
            v = list(map(int, input_nums()))
            if v[0] <= 0 or v[1] <= 0:
                return 'invalid' in output_lower
            g = gcd(v[0], v[1])
            l = abs(v[0]*v[1]) // g
            return str(g) in nums and str(l) in nums

# ── REVERSE A NUMBER ─────────────────────────────────────────────────────────
        if title == 'reverse a number':
            s = input_data.strip()
            if s.startswith('-'):
                return 'invalid' in output_lower
            rev = s[::-1].lstrip('0') or '0'
            return rev in output

# ── PALINDROME STRING ────────────────────────────────────────────────────────
        if title == 'palindrome string':
            s = input_data.strip().lower()
            is_p = s == s[::-1]
            if 'not palindrome' in output_lower or 'not a palindrome' in output_lower:
                return not is_p
            elif 'palindrome' in output_lower:
                return is_p
            return False

# ── ANAGRAM CHECKER ──────────────────────────────────────────────────────────
        if title == 'anagram checker':
            il = input_lines()
            is_a = sorted(il[0].lower()) == sorted(il[1].lower())
            if 'not anagram' in output_lower or 'not an anagram' in output_lower:
                return not is_a
            elif 'anagram' in output_lower:
                return is_a
            return False
