import json
import os
import re
from app import create_app, db
from app.models.assessment import Question

app = create_app()

LEVEL_MAP = {
    "BEGINNER LEVEL": "beginner",
    "INTERMEDIATE LEVEL": "intermediate",
    "ADVANCED LEVEL": "advanced",
}

QUESTION_BANK_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "problems", "Java_Question_Bank_Updated.txt")
)

def _clean_text(value: str) -> str:
    return re.sub(r'\s+', ' ', (value or '').strip())

def _strip_option_prefix(value: str) -> str:
    return re.sub(r'^[A-Z]\)\s*', '', value.strip())

def _parse_mcq_msq(section_text: str, level: str, q_type: str):
    lines = section_text.splitlines()
    questions = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("SECTION ") or line.startswith("[") or line.startswith("━") or line.startswith("="):
            i += 1
            continue
        if re.match(r'^[A-Z]\)\s+', line):
            i += 1
            continue
        question_lines = [line]
        i += 1
        while i < len(lines):
            current = lines[i].strip()
            if not current:
                i += 1
                continue
            if re.match(r'^[A-Z]\)\s+', current):
                break
            if current.startswith("Answer:"):
                break
            question_lines.append(current)
            i += 1
        options = []
        while i < len(lines):
            current = lines[i].strip()
            if re.match(r'^[A-Z]\)\s+', current):
                options.append(current)
                i += 1
                continue
            break
        if i >= len(lines) or not lines[i].strip().startswith("Answer:"):
            i += 1
            continue
        answer_raw = lines[i].strip().split("Answer:", 1)[1].strip()
        i += 1
        option_map = {}
        for opt in options:
            key = opt[0]
            option_map[key] = _strip_option_prefix(opt)
        if q_type == "mcq":
            correct = option_map.get(answer_raw[:1], "")
        else:
            keys = [part.strip()[:1] for part in answer_raw.split(",") if part.strip()]
            correct = json.dumps([option_map.get(k, "") for k in keys if option_map.get(k, "")], ensure_ascii=False)
        questions.append({
            "question_text": _clean_text(" ".join(question_lines)),
            "question_type": q_type,
            "options": [_strip_option_prefix(opt) for opt in options],
            "correct_answer": correct,
            "explanation": "Imported from Java Question Bank",
            "difficulty": level,
            "tags": ["assessment", q_type]
        })
    return questions

def _parse_coding(section_text: str, level: str):
    blocks = [b.strip() for b in re.split(r'\n-{20,}\n', section_text) if b.strip()]
    questions = []
    for block in blocks:
        lines = [ln.rstrip() for ln in block.splitlines() if ln.strip()]
        if len(lines) < 4:
            continue
        title = lines[0].strip()
        problem_idx = next((idx for idx, ln in enumerate(lines) if ln.strip().lower() == "problem statement"), -1)
        if problem_idx == -1:
            continue
        concepts_idx = next((idx for idx, ln in enumerate(lines) if ln.strip().lower() == "concepts covered"), -1)
        input_idx = next((idx for idx, ln in enumerate(lines) if ln.strip().lower().startswith("example input")), -1)
        output_idx = next((idx for idx, ln in enumerate(lines) if ln.strip().lower().startswith("expected output")), -1)
        output_sample_idx = next((idx for idx, ln in enumerate(lines) if ln.strip().lower() == "output sample"), -1)
        statement_end = min([idx for idx in [concepts_idx, input_idx, output_idx, output_sample_idx] if idx != -1], default=len(lines))
        statement_lines = lines[problem_idx + 1:statement_end]
        statement = " ".join(statement_lines).strip()
        if title.lower() == "problem statement":
            title = (statement_lines[0].strip() if statement_lines else "Coding Problem")[:120]
        example_input = ""
        example_output = ""
        if input_idx != -1:
            next_boundary = output_idx if output_idx > input_idx else len(lines)
            example_input = "\n".join(lines[input_idx + 1:next_boundary]).strip()
        if output_idx != -1:
            next_boundary = output_sample_idx if output_sample_idx > output_idx else len(lines)
            example_output = "\n".join(lines[output_idx + 1:next_boundary]).strip()
        output_sample = ""
        if output_sample_idx != -1:
            output_sample = "\n".join(lines[output_sample_idx + 1:]).strip()
        test_cases = []
        if example_input or example_output:
            test_cases.append({"input": example_input, "output": example_output, "match_type": "exact"})
        elif output_sample:
            keywords = [ln.strip() for ln in output_sample.splitlines()[:3] if ln.strip()]
            test_cases.append({
                "input": "",
                "output": output_sample,
                "match_type": "compile_only" if not keywords else "contains_keywords",
                "expected_keywords": keywords
            })
        else:
            test_cases.append({"input": "", "output": "", "match_type": "compile_only"})
        payload = {
            "test_cases": test_cases,
            "title": title
        }
        questions.append({
            "question_text": f"{title}\n\n{statement}".strip(),
            "question_type": "coding",
            "options": None,
            "correct_answer": json.dumps(payload, ensure_ascii=False),
            "explanation": "Validated using testcase execution",
            "difficulty": level,
            "tags": ["assessment", "coding"]
        })
    return questions

def _extract_sections(full_text: str):
    level_matches = list(re.finditer(r'BEGINNER LEVEL|INTERMEDIATE LEVEL|ADVANCED LEVEL', full_text))
    sections = []
    for idx, match in enumerate(level_matches):
        level_label = match.group(0)
        start = match.end()
        end = level_matches[idx + 1].start() if idx + 1 < len(level_matches) else len(full_text)
        level_text = full_text[start:end]
        level = LEVEL_MAP[level_label]
        mcq_start = level_text.find("SECTION A")
        msq_start = level_text.find("SECTION B")
        coding_start = level_text.find("SECTION C")
        if mcq_start != -1 and msq_start != -1:
            sections.extend(_parse_mcq_msq(level_text[mcq_start:msq_start], level, "mcq"))
        if msq_start != -1 and coding_start != -1:
            sections.extend(_parse_mcq_msq(level_text[msq_start:coding_start], level, "msq"))
        if coding_start != -1:
            sections.extend(_parse_coding(level_text[coding_start:], level))
    return sections

def seed_questions():
    with app.app_context():
        if not os.path.exists(QUESTION_BANK_PATH):
            raise FileNotFoundError(f"Question bank not found: {QUESTION_BANK_PATH}")
        with open(QUESTION_BANK_PATH, "r", encoding="utf-8") as f:
            full_text = f.read()
        questions_data = _extract_sections(full_text)
        if not questions_data:
            raise RuntimeError("No questions parsed from question bank")
        Question.query.delete()
        for q_data in questions_data:
            db.session.add(Question(**q_data))
        db.session.commit()
        print(f"✓ Seeded {len(questions_data)} assessment questions from question bank")
        for level in ["beginner", "intermediate", "advanced"]:
            level_questions = [q for q in questions_data if q["difficulty"] == level]
            print(f"  - {level}: {len(level_questions)}")
            for q_type in ["mcq", "msq", "coding"]:
                count = len([q for q in level_questions if q["question_type"] == q_type])
                print(f"    * {q_type}: {count}")

if __name__ == '__main__':
    seed_questions()
