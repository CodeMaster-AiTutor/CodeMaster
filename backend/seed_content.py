import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.featured_course import FeaturedCourse
from app.models.learning_path import LearningPathConcept, LearningPathSubtopic
from app.models.practice import PracticeProblem
from app.models.theory_course import TheoryCoursePage


FEATURED_COURSES = [
    {
        "slug": "java-theory-course",
        "title": "Java Course",
        "description": "A theory-first Java course from beginner to advanced with structured chapters.",
        "language": "Java",
        "kind": "theory",
        "route_path": "/theory-course",
        "external_url": None,
        "order_index": 1,
    }
]

LEARNING_PATHS = [
    {
        "slug": "java-introduction",
        "title": "Introduction to Java",
        "description": "Java fundamentals, JVM basics, and program execution flow.",
        "level": "basic",
        "tutorial_url": "/theory-course/hello-world.html",
        "order_index": 1,
        "subtopics": ["History & Features of Java", "JDK, JRE, JVM", "Program Structure", "main() Method"],
    },
    {
        "slug": "operators-control-flow",
        "title": "Operators & Control Flow",
        "description": "Core operators, conditionals, loops, and control statements.",
        "level": "basic",
        "tutorial_url": "/theory-course/operators.html",
        "order_index": 2,
        "subtopics": ["Operators", "if/else", "switch", "for/while/do-while"],
    },
    {
        "slug": "oop-core",
        "title": "OOP Core",
        "description": "Object-oriented design in Java from classes to polymorphism.",
        "level": "intermediate",
        "tutorial_url": "/theory-course/oop-intro.html",
        "order_index": 3,
        "subtopics": ["Classes & Objects", "Inheritance", "Encapsulation", "Polymorphism", "Abstraction"],
    },
    {
        "slug": "exception-file-handling",
        "title": "Exception & File Handling",
        "description": "Robust error handling and file operations in Java.",
        "level": "intermediate",
        "tutorial_url": "/theory-course/exception-handling.html",
        "order_index": 4,
        "subtopics": ["try-catch-finally", "Custom Exceptions", "File I/O"],
    },
    {
        "slug": "collections-generics",
        "title": "Collections & Generics",
        "description": "Data structures and type-safe abstractions for scalable Java apps.",
        "level": "advanced",
        "tutorial_url": "/theory-course/collections.html",
        "order_index": 5,
        "subtopics": ["Collections Framework", "ArrayList", "Generics", "Streams"],
    },
    {
        "slug": "advanced-java-systems",
        "title": "Advanced Java Systems",
        "description": "Concurrency, JDBC, serialization, and real-world mini projects.",
        "level": "advanced",
        "tutorial_url": "/theory-course/multithreading.html",
        "order_index": 6,
        "subtopics": ["Multithreading", "JDBC", "Serialization", "Mini Projects"],
    },
]

THEORY_PAGES = [
    ("hello-world", "Hello World", "beginner", "hello-world.html"),
    ("variables", "Variables", "beginner", "variable.html"),
    ("input-output", "Input Output", "beginner", "input-output.html"),
    ("operators", "Operators", "beginner", "operators.html"),
    ("conditionals", "Conditionals", "beginner", "conditionals.html"),
    ("loops", "Loops", "beginner", "loops.html"),
    ("methods", "Methods", "beginner", "methods.html"),
    ("arrays", "Arrays", "beginner", "arrays.html"),
    ("strings", "Strings", "beginner", "strings.html"),
    ("oop-intro", "OOP Intro", "intermediate", "oop-intro.html"),
    ("constructors", "Constructors", "intermediate", "constructors.html"),
    ("encapsulation", "Encapsulation", "intermediate", "encapsulation.html"),
    ("inheritance", "Inheritance", "intermediate", "inheritance.html"),
    ("polymorphism", "Polymorphism", "intermediate", "polymorphism.html"),
    ("abstraction", "Abstraction", "intermediate", "abstraction.html"),
    ("arraylist", "ArrayList", "intermediate", "arraylist.html"),
    ("exception-handling", "Exception Handling", "intermediate", "exception-handling.html"),
    ("file-handling", "File Handling", "intermediate", "file-handling.html"),
    ("packages", "Packages", "advanced", "packages.html"),
    ("collections", "Collections", "advanced", "collections.html"),
    ("generics", "Generics", "advanced", "generics.html"),
    ("lambda", "Lambda", "advanced", "lambda.html"),
    ("streams", "Streams", "advanced", "streams.html"),
    ("multithreading", "Multithreading", "advanced", "multithreading.html"),
    ("jdbc", "JDBC", "advanced", "jdbc.html"),
    ("serialization", "Serialization", "advanced", "serialization.html"),
    ("mini-projects", "Mini Projects", "advanced", "mini-projects.html"),
]

PRACTICE_PROBLEMS = [
    ("beginner", None, "Even / Odd Checker", "Easy"),
    ("beginner", None, "Largest of Three Numbers", "Easy"),
    ("beginner", None, "Leap Year Checker", "Easy"),
    ("beginner", None, "Temperature Converter", "Easy"),
    ("beginner", None, "Grade System", "Easy"),
    ("beginner", None, "Simple Interest Calculator", "Easy"),
    ("beginner", None, "Swap Without Third Variable", "Easy"),
    ("beginner", None, "Count Vowels", "Easy"),
    ("beginner", None, "Character Frequency", "Easy"),
    ("beginner", None, "Check Alphabet Type", "Easy"),
    ("beginner", None, "Sum of N Natural Numbers", "Easy"),
    ("beginner", None, "Multiplication Table", "Easy"),
    ("beginner", None, "Count Digits", "Easy"),
    ("beginner", None, "Sum of Digits", "Easy"),
    ("beginner", None, "Basic Calculator", "Medium"),
    ("beginner", None, "Factorial Calculator", "Medium"),
    ("beginner", None, "Prime Number Checker", "Medium"),
    ("beginner", None, "Fibonacci Series", "Medium"),
    ("beginner", None, "Reverse a Number", "Medium"),
    ("beginner", None, "Palindrome Number", "Medium"),
    ("beginner", None, "Armstrong Number", "Medium"),
    ("beginner", None, "GCD and LCM", "Medium"),
    ("beginner", None, "Power Calculator", "Medium"),
    ("beginner", None, "Pattern - Star Pyramid", "Hard"),
    ("beginner", None, "Pattern - Number Triangle", "Hard"),
    ("intermediate", "Arrays", "Find Largest in Array", "Easy"),
    ("intermediate", "Arrays", "Reverse an Array", "Easy"),
    ("intermediate", "Arrays", "Linear Search", "Easy"),
    ("intermediate", "Arrays", "Sum of Array Elements", "Easy"),
    ("intermediate", "Arrays", "Count Even and Odd", "Easy"),
    ("intermediate", "Arrays", "Find Second Largest", "Medium"),
    ("intermediate", "Arrays", "Bubble Sort", "Medium"),
    ("intermediate", "Arrays", "Binary Search", "Medium"),
    ("intermediate", "Arrays", "Remove Duplicates", "Medium"),
    ("intermediate", "Arrays", "Array Rotation (Left by K)", "Hard"),
    ("intermediate", "Strings", "Reverse a String", "Easy"),
    ("intermediate", "Strings", "Palindrome String", "Easy"),
    ("intermediate", "Strings", "Count Words in a Sentence", "Easy"),
    ("intermediate", "Strings", "Remove Spaces", "Easy"),
    ("intermediate", "Strings", "Anagram Checker", "Medium"),
    ("intermediate", "Strings", "String Compression", "Hard"),
    ("intermediate", "Matrices", "Matrix Addition", "Easy"),
    ("intermediate", "Matrices", "Transpose a Matrix", "Medium"),
    ("intermediate", "Matrices", "Matrix Multiplication", "Hard"),
    ("intermediate", "Methods & OOP", "Method Overloading Demo", "Medium"),
    ("intermediate", "Methods & OOP", "Student Result System", "Medium"),
    ("intermediate", "Methods & OOP", "Employee Salary System", "Medium"),
    ("intermediate", "Methods & OOP", "Menu-Driven Program", "Medium"),
    ("intermediate", "Methods & OOP", "Custom Exception Demo", "Hard"),
    ("intermediate", "Methods & OOP", "Number Guessing Game", "Hard"),
    ("advanced", "Data Systems", "Student Management System", "Easy"),
    ("advanced", "Data Systems", "Library System", "Easy"),
    ("advanced", "Data Systems", "Contact Book", "Easy"),
    ("advanced", "Data Systems", "ATM Simulator", "Medium"),
    ("advanced", "Data Systems", "Shopping Cart System", "Medium"),
    ("advanced", "Interactive Apps", "Expense Tracker", "Easy"),
    ("advanced", "Interactive Apps", "Quiz Application", "Medium"),
    ("advanced", "Interactive Apps", "Voting System", "Medium"),
    ("advanced", "Interactive Apps", "Parking Lot System", "Medium"),
    ("advanced", "Interactive Apps", "Bank Account System", "Medium"),
    ("advanced", "Management Tools", "Password Validator", "Easy"),
    ("advanced", "Management Tools", "Task Manager", "Easy"),
    ("advanced", "Management Tools", "Inventory System", "Medium"),
    ("advanced", "Management Tools", "Ticket Booking System", "Medium"),
    ("advanced", "Management Tools", "Restaurant Billing System", "Medium"),
    ("advanced", "Advanced Systems", "Simple Chat Simulation", "Easy"),
    ("advanced", "Advanced Systems", "Simple Login System", "Easy"),
    ("advanced", "Advanced Systems", "Employee Management + Sort by Salary", "Medium"),
    ("advanced", "Advanced Systems", "Mini Banking Transaction History", "Medium"),
    ("advanced", "Advanced Systems", "Course Enrollment System", "Medium"),
    ("advanced", "Advanced Systems", "Hotel Room Booking", "Medium"),
    ("advanced", "Advanced Systems", "Stack Implementation (Manual)", "Hard"),
    ("advanced", "Advanced Systems", "Queue Implementation (Manual)", "Hard"),
    ("advanced", "Advanced Systems", "E-Voting with ID Validation", "Hard"),
    ("advanced", "Advanced Systems", "Multi-User Scoreboard System", "Hard"),
]


def normalize_problem_key(text):
    normalized = (text or "").lower().strip()
    normalized = normalized.replace("—", "-")
    normalized = re.sub(r"[^a-z0-9]+", "", normalized)
    return normalized


def extract_problem_title(raw_line):
    line = (raw_line or "").strip().replace("—", "-")
    line = re.sub(r"^\d{1,2}\s*[\.\-)]?\s*", "", line)
    line = re.sub(r"\s+(easy|medium|hard+)\s*$", "", line, flags=re.IGNORECASE)
    line = re.sub(r"\s{2,}", " ", line).strip()
    return line


def parse_problem_descriptions_from_file(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read().replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n[-=]{20,}\n", content)
    result = {}
    non_title_labels = {
        "beginner",
        "intermediate",
        "advanced",
        "arrays",
        "strings",
        "matrices",
        "methods & oop",
        "data systems",
        "interactive apps",
        "management tools",
        "advanced systems",
    }
    for block in blocks:
        if "Problem Statement" not in block:
            continue
        raw_lines = [line.rstrip() for line in block.split("\n")]
        if not raw_lines:
            continue
        ps_raw_index = next((i for i, line in enumerate(raw_lines) if "Problem Statement" in line), -1)
        if ps_raw_index == -1:
            continue
        title_raw_index = -1
        for i in range(ps_raw_index - 1, -1, -1):
            candidate = (raw_lines[i] or "").strip()
            if not candidate:
                continue
            if candidate.lower() in non_title_labels:
                continue
            if candidate.lower() in {"problem statement", "concepts", "concepts covered", "test cases"}:
                continue
            title_raw_index = i
            break
        if title_raw_index == -1:
            for i in range(0, ps_raw_index):
                candidate = (raw_lines[i] or "").strip()
                if candidate and candidate.lower() not in non_title_labels:
                    title_raw_index = i
                    break
        if title_raw_index == -1:
            continue
        title = extract_problem_title(raw_lines[title_raw_index])
        if not title:
            continue
        description_lines = [line.rstrip() for line in raw_lines[title_raw_index:]]
        description = "\n".join(description_lines).strip()
        key = normalize_problem_key(title)
        result[key] = description
    return result


def extract_test_cases_from_description(description):
    lines = [line.rstrip() for line in (description or "").replace("\t", "    ").split("\n")]
    normalized = [line.strip().lower() for line in lines]
    start_index = -1
    for index, line in enumerate(normalized):
        if line in {"test cases", "test scenarios"}:
            start_index = index + 1
            break
    if start_index == -1:
        return []
    rows = []
    for raw in lines[start_index:]:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if not re.match(r"^\d+\s+", line):
            continue
        row = re.sub(r"^\d+\s+", "", line).strip()
        parts = re.split(r"\s{2,}", row)
        if len(parts) >= 2:
            case_input = " ".join(part.strip() for part in parts[:-1] if part.strip())
            expected = parts[-1].strip()
            rows.append({"input": case_input, "output": expected})
    return rows[:3]


def load_all_problem_descriptions():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    problems_dir = os.path.join(project_root, "problems")
    files = [
        os.path.join(problems_dir, "Beginner Problems.txt"),
        os.path.join(problems_dir, "Intemediate Problems.txt"),
        os.path.join(problems_dir, "Advanced Problems.txt"),
    ]
    merged = {}
    for file_path in files:
        merged.update(parse_problem_descriptions_from_file(file_path))
    return merged


def load_all_problem_test_cases(parsed_descriptions):
    parsed = {}
    for key, description in parsed_descriptions.items():
        cases = extract_test_cases_from_description(description)
        parsed[key] = cases
    return parsed


def build_problem_description(level, section, title, difficulty):
    heading = section if section else f"{level.capitalize()} Fundamentals"
    return (
        f"Problem: {title}\n\n"
        f"Category: {heading}\n"
        f"Difficulty: {difficulty}\n\n"
        "Task:\n"
        f"Implement a Java program to solve '{title}'. The solution should handle normal inputs, "
        "edge cases, and invalid data safely.\n\n"
        "Requirements:\n"
        "1. Read input from standard input.\n"
        "2. Compute the expected result using a clear, efficient approach.\n"
        "3. Print only the required output format.\n"
        "4. Keep code modular and readable.\n\n"
        "Evaluation:\n"
        "Your solution is validated against hidden and visible test cases. Output must match exactly."
    )


def build_problem_test_cases(title):
    normalized = title.lower()
    if "even / odd checker" in normalized:
        return [{"input": "7\n", "output": "Odd"}, {"input": "0\n", "output": "Even"}, {"input": "-4\n", "output": "Even"}]
    if "largest of three numbers" in normalized:
        return [{"input": "5 9 3\n", "output": "9"}, {"input": "12 12 8\n", "output": "12"}, {"input": "-1 -5 -3\n", "output": "-1"}]
    if "count digits" in normalized:
        return [{"input": "9\n", "output": "1"}, {"input": "100\n", "output": "3"}, {"input": "56789\n", "output": "5"}]
    if "sum of digits" in normalized:
        return [{"input": "999\n", "output": "27"}, {"input": "10\n", "output": "1"}, {"input": "45\n", "output": "9"}]
    if "prime number checker" in normalized:
        return [{"input": "4\n", "output": "Not Prime"}, {"input": "2\n", "output": "Prime"}, {"input": "15\n", "output": "Not Prime"}]
    return [
        {"input": "", "output": "IMPLEMENTATION_PENDING"},
        {"input": "", "output": "IMPLEMENTATION_PENDING"},
        {"input": "", "output": "IMPLEMENTATION_PENDING"},
    ]


def upsert_featured_courses():
    for item in FEATURED_COURSES:
        row = FeaturedCourse.query.filter_by(slug=item["slug"]).first()
        if not row:
            row = FeaturedCourse(slug=item["slug"])
            db.session.add(row)
        for key, value in item.items():
            setattr(row, key, value)


def upsert_learning_paths():
    for item in LEARNING_PATHS:
        row = LearningPathConcept.query.filter_by(slug=item["slug"]).first()
        if not row:
            row = LearningPathConcept(slug=item["slug"])
            db.session.add(row)
        row.title = item["title"]
        row.description = item["description"]
        row.level = item["level"]
        row.tutorial_url = item["tutorial_url"]
        row.order_index = item["order_index"]
        row.subtopics.clear()
        for idx, title in enumerate(item["subtopics"], start=1):
            row.subtopics.append(LearningPathSubtopic(title=title, order_index=idx))


def upsert_theory_pages():
    for idx, (slug, title, level, html_path) in enumerate(THEORY_PAGES, start=1):
        row = TheoryCoursePage.query.filter_by(slug=slug).first()
        if not row:
            row = TheoryCoursePage(slug=slug)
            db.session.add(row)
        row.title = title
        row.level = level
        row.html_path = html_path
        row.order_index = idx


def upsert_practice_problems():
    parsed_descriptions = load_all_problem_descriptions()
    parsed_test_cases = load_all_problem_test_cases(parsed_descriptions)
    for idx, (level, section, title, difficulty) in enumerate(PRACTICE_PROBLEMS, start=1):
        row = PracticeProblem.query.filter_by(title=title).first()
        fallback_description = build_problem_description(level, section, title, difficulty)
        problem_key = normalize_problem_key(title)
        db_description = parsed_descriptions.get(problem_key, fallback_description)
        if not row:
            row = PracticeProblem(title=title, description=db_description)
            db.session.add(row)
        row.description = db_description
        row.level = level
        row.section = section
        row.title = title
        row.difficulty = difficulty
        row.order_index = idx
        row.tags = row.tags or []
        row.starter_code = row.starter_code or ""
        parsed_cases = parsed_test_cases.get(problem_key, [])
        if len(parsed_cases) >= 3:
            row.test_cases = parsed_cases[:3]
        else:
            row.test_cases = build_problem_test_cases(title)


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()
        upsert_featured_courses()
        upsert_learning_paths()
        upsert_theory_pages()
        upsert_practice_problems()
        db.session.commit()
        print("Seeded content catalog successfully.")


if __name__ == "__main__":
    seed()
