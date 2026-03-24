from app import create_app
from app.models.practice import PracticeProblem
from app.routes.practice import _verify_output


def _norm(title: str):
    return (title or "").strip().lower()


def get_correct_output(title: str, input_data: str, expected_output: str):
    t = _norm(title)
    expected = (expected_output or "").strip()
    if not expected:
        return "Output generated."

    if t == "temperature converter":
        return f"Enter value and unit (C/F): {expected} F"
    if t == "leap year checker":
        return f"Enter year: {expected}"
    if t == "grade system":
        return f"Final result -> {expected}"
    if t == "basic calculator":
        return f"Result: {expected}"
    if t in {
        "prime number checker",
        "palindrome number",
        "palindrome string",
        "armstrong number",
        "anagram checker",
    }:
        return f"Answer: {expected}"
    if t in {
        "fibonacci series",
        "reverse an array",
        "bubble sort",
        "remove duplicates",
        "array rotation (left by k)",
        "matrix addition",
        "transpose a matrix",
        "matrix multiplication",
    }:
        return f"Computed output:\n{expected}"
    if t in {"gcd and lcm", "count even and odd", "student result system"}:
        return f"Details:\n{expected}"
    if t in {"count vowels", "count digits", "sum of digits", "count words in a sentence"}:
        return f"Count = {expected}"
    if t in {"sum of n natural numbers", "sum of array elements", "find largest in array", "find second largest"}:
        return f"Computed value: {expected}"
    if t in {"employee salary system", "simple interest calculator", "power calculator", "factorial calculator"}:
        return f"Final value = {expected}"
    if t in {"check alphabet type", "character frequency", "reverse a string", "remove spaces", "string compression"}:
        return f"Output: {expected}"
    if "invalid" in expected.lower():
        return f"Invalid input: {expected}"
    return f"Program Output: {expected}"


def main():
    app = create_app()
    with app.app_context():
        rows = PracticeProblem.query.order_by(PracticeProblem.id.asc()).all()
        total = 0
        failed = []
        for row in rows:
            test_cases = row.test_cases or []
            for idx, case in enumerate(test_cases, start=1):
                total += 1
                case_input = str((case or {}).get("input", ""))
                expected = str((case or {}).get("output", ""))
                actual = get_correct_output(row.title, case_input, expected)
                ok = _verify_output(row.title, case_input, actual, expected)
                if not ok:
                    failed.append((row.title, idx, case_input, expected, actual))

        print(f"TOTAL_CASES={total}")
        print(f"FAILED_CASES={len(failed)}")
        if failed:
            seen = set()
            for title, _, _, _, _ in failed:
                if title not in seen:
                    print(f"FAIL_TITLE={title}")
                    seen.add(title)
            for title, idx, case_input, expected, actual in failed[:50]:
                print(
                    f"DETAIL={title}#{idx} | input={case_input!r} | expected={expected!r} | actual={actual!r}"
                )


if __name__ == "__main__":
    main()
