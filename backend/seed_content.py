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
        return [{"input": "7", "output": "Odd"}, {"input": "0", "output": "Even"}, {"input": "-4", "output": "Even"}]
    if "largest of three numbers" in normalized:
        return [{"input": "5\n9\n3", "output": "9"}, {"input": "12\n12\n8", "output": "12"}, {"input": "-1\n-5\n-3", "output": "-1"}]
    if "leap year checker" in normalized:
        return [{"input": "2000", "output": "Leap Year"}, {"input": "1900", "output": "Not a Leap Year"}, {"input": "2024", "output": "Leap Year"}]
    if "temperature converter" in normalized:
        return [{"input": "100\nC", "output": "212.0"}, {"input": "25\nC", "output": "77.0"}, {"input": "37\nC", "output": "98.6"}]
    if "grade system" in normalized:
        return [{"input": "95", "output": "Grade A+"}, {"input": "70", "output": "Grade B"}, {"input": "45", "output": "Fail"}]
    if "simple interest calculator" in normalized:
        return [{"input": "1000\n5\n2", "output": "100.0"}, {"input": "5000\n10\n3", "output": "1500.0"}, {"input": "2000\n8\n1", "output": "160.0"}]
    if "swap without third variable" in normalized:
        return [{"input": "5\n10", "output": "10\n5"}, {"input": "0\n7", "output": "7\n0"}, {"input": "-3\n9", "output": "9\n-3"}]
    if "count vowels" in normalized:
        return [{"input": "hello", "output": "2"}, {"input": "java", "output": "2"}, {"input": "rhythm", "output": "0"}]
    if "character frequency" in normalized:
        return [{"input": "mississippi\ns", "output": "4"}, {"input": "hello\nz", "output": "0"}, {"input": "java\na", "output": "2"}]
    if "check alphabet type" in normalized:
        return [{"input": "A", "output": "Uppercase"}, {"input": "z", "output": "Lowercase"}, {"input": "3", "output": "Not an Alphabet"}]
    if "sum of n natural numbers" in normalized:
        return [{"input": "5", "output": "15"}, {"input": "10", "output": "55"}, {"input": "1", "output": "1"}]
    if "multiplication table" in normalized:
        return [{"input": "2", "output": "2 x 1 = 2"}, {"input": "5", "output": "5 x 1 = 5"}, {"input": "10", "output": "10 x 1 = 10"}]
    if "count digits" in normalized:
        return [{"input": "9", "output": "1"}, {"input": "100", "output": "3"}, {"input": "56789", "output": "5"}, {"input": "0", "output": "1"}]
    if "sum of digits" in normalized:
        return [{"input": "999", "output": "27"}, {"input": "10", "output": "1"}, {"input": "45", "output": "9"}]
    if "basic calculator" in normalized:
        return [{"input": "10\n5\n+", "output": "15"}, {"input": "10\n5\n-", "output": "5"}, {"input": "10\n5\n*", "output": "50"}]
    if "factorial calculator" in normalized:
        return [{"input": "5", "output": "120"}, {"input": "0", "output": "1"}, {"input": "10", "output": "3628800"}]
    if "prime number checker" in normalized:
        return [{"input": "4", "output": "Not Prime"}, {"input": "2", "output": "Prime"}, {"input": "17", "output": "Prime"}]
    if "fibonacci series" in normalized:
        return [{"input": "5", "output": "0 1 1 2 3"}, {"input": "1", "output": "0"}, {"input": "7", "output": "0 1 1 2 3 5 8"}]
    if "reverse a number" in normalized:
        return [{"input": "1234", "output": "4321"}, {"input": "100", "output": "1"}, {"input": "-567", "output": "-765"}]
    if "palindrome number" in normalized:
        return [{"input": "121", "output": "Palindrome"}, {"input": "123", "output": "Not Palindrome"}, {"input": "0", "output": "Palindrome"}]
    if "armstrong number" in normalized:
        return [{"input": "153", "output": "Armstrong"}, {"input": "123", "output": "Not Armstrong"}, {"input": "370", "output": "Armstrong"}]
    if "gcd and lcm" in normalized:
        return [{"input": "12\n18", "output": "GCD: 6\nLCM: 36"}, {"input": "5\n7", "output": "GCD: 1\nLCM: 35"}, {"input": "8\n12", "output": "GCD: 4\nLCM: 24"}]
    if "power calculator" in normalized:
        return [{"input": "2\n10", "output": "1024"}, {"input": "3\n3", "output": "27"}, {"input": "5\n0", "output": "1"}]
    if "pattern - star pyramid" in normalized:
        return [{"input": "3", "output": "*\n**\n***"}, {"input": "1", "output": "*"}, {"input": "4", "output": "*\n**\n***\n****"}]
    if "pattern - number triangle" in normalized:
        return [{"input": "3", "output": "1\n1 2\n1 2 3"}, {"input": "1", "output": "1"}, {"input": "4", "output": "1\n1 2\n1 2 3\n1 2 3 4"}]
    if "find largest in array" in normalized:
        return [{"input": "5\n3 7 1 9 2", "output": "9"}, {"input": "3\n-1 -5 -3", "output": "-1"}, {"input": "4\n4 4 4 4", "output": "4"}, {"input": "3\n1 2 3", "output": "3"}, {"input": "1\n42", "output": "42"}]
    if "reverse an array" in normalized:
        return [{"input": "4\n1 2 3 4", "output": "4 3 2 1"}, {"input": "1\n5", "output": "5"}, {"input": "3\n7 8 9", "output": "9 8 7"}]
    if "linear search" in normalized:
        return [{"input": "5\n3 7 1 9 2\n7", "output": "Found at index 1"}, {"input": "3\n1 2 3\n5", "output": "Not Found"}, {"input": "4\n4 8 12 16\n12", "output": "Found at index 2"}]
    if "sum of array elements" in normalized:
        return [{"input": "4\n1 2 3 4", "output": "10"}, {"input": "3\n-1 0 1", "output": "0"}, {"input": "5\n5 5 5 5 5", "output": "25"}]
    if "count even and odd" in normalized:
        return [{"input": "5\n1 2 3 4 5", "output": "Even: 2\nOdd: 3"}, {"input": "3\n2 4 6", "output": "Even: 3\nOdd: 0"}, {"input": "2\n1 3", "output": "Even: 0\nOdd: 2"}]
    if "find second largest" in normalized:
        return [{"input": "5\n3 7 1 9 2", "output": "7"}, {"input": "3\n5 5 5", "output": "5"}, {"input": "4\n1 2 3 4", "output": "3"}]
    if "bubble sort" in normalized:
        return [{"input": "4\n4 2 7 1", "output": "1 2 4 7"}, {"input": "3\n3 1 2", "output": "1 2 3"}, {"input": "5\n5 4 3 2 1", "output": "1 2 3 4 5"}]
    if "binary search" in normalized:
        return [{"input": "5\n1 3 5 7 9\n7", "output": "Found at index 3"}, {"input": "4\n2 4 6 8\n5", "output": "Not Found"}, {"input": "3\n10 20 30\n10", "output": "Found at index 0"}]
    if "remove duplicates" in normalized:
        return [{"input": "5\n1 2 2 3 3", "output": "1 2 3"}, {"input": "4\n4 4 4 4", "output": "4"}, {"input": "3\n1 2 3", "output": "1 2 3"}]
    if "array rotation" in normalized:
        return [{"input": "5\n1 2 3 4 5\n2", "output": "3 4 5 1 2"}, {"input": "3\n1 2 3\n1", "output": "2 3 1"}, {"input": "4\n1 2 3 4\n4", "output": "1 2 3 4"}]
    if "reverse a string" in normalized:
        return [{"input": "hello", "output": "olleh"}, {"input": "java", "output": "avaj"}, {"input": "abcd", "output": "dcba"}]
    if "palindrome string" in normalized:
        return [{"input": "racecar", "output": "Palindrome"}, {"input": "hello", "output": "Not Palindrome"}, {"input": "madam", "output": "Palindrome"}]
    if "count words in a sentence" in normalized:
        return [{"input": "hello world", "output": "2"}, {"input": "java is fun", "output": "3"}, {"input": "one", "output": "1"}]
    if "remove spaces" in normalized:
        return [{"input": "hello world", "output": "helloworld"}, {"input": "a b c", "output": "abc"}, {"input": "no spaces", "output": "nospaces"}]
    if "anagram checker" in normalized:
        return [{"input": "listen\nsilent", "output": "Anagram"}, {"input": "hello\nworld", "output": "Not Anagram"}, {"input": "triangle\nintegral", "output": "Anagram"}]
    if "string compression" in normalized:
        return [{"input": "aabcccdd", "output": "a2b1c3d2"}, {"input": "abcd", "output": "a1b1c1d1"}, {"input": "aaaa", "output": "a4"}]
    if "matrix addition" in normalized:
        return [{"input": "2\n1 2\n3 4\n5 6\n7 8", "output": "6 8\n10 12"}, {"input": "1\n5\n3", "output": "8"}, {"input": "2\n0 0\n0 0\n1 1\n1 1", "output": "1 1\n1 1"}]
    if "transpose a matrix" in normalized:
        return [{"input": "2\n1 2\n3 4", "output": "1 3\n2 4"}, {"input": "1\n5", "output": "5"}, {"input": "3\n1 2 3\n4 5 6\n7 8 9", "output": "1 4 7\n2 5 8\n3 6 9"}]
    if "matrix multiplication" in normalized:
        return [{"input": "2\n1 2\n3 4\n5 6\n7 8", "output": "19 22\n43 50"}, {"input": "1\n3\n4", "output": "12"}, {"input": "2\n1 0\n0 1\n1 2\n3 4", "output": "1 2\n3 4"}]
    if "method overloading" in normalized:
        return [{"input": "2\n5\n3", "output": "8"}, {"input": "2\n2.5\n1.5", "output": "4.0"}, {"input": "3\n1\n2\n3", "output": "6"}]
    if "student result system" in normalized:
        return [{"input": "5\n70\n75\n80\n85\n90", "output": "B"},
        {"input": "5\n95\n97\n98\n96\n99", "output": "A+"},
        {"input": "5\n20\n25\n30\n35\n40", "output": "F"}]
    if "employee salary system" in normalized:
        return [{"input": "50000\n5000\n2000", "output": "53000"}, {"input": "30000\n3000\n1000", "output": "32000"}, {"input": "100000\n10000\n5000", "output": "105000"}]
    if "menu-driven program" in normalized:
        return [{"input": "1\n5\n0", "output": "Invalid Choice"}, {"input": "2\n0", "output": "Invalid Choice"}, {"input": "0", "output": "Exit"}]
    if "custom exception demo" in normalized:
        return [{"input": "-1", "output": "Exception"}, {"input": "0", "output": "Exception"}, {"input": "10", "output": "Valid"}]
    if "number guessing game" in normalized:
        return [{"input": "50\n0", "output": "Correct"}, {"input": "10\n0", "output": "Try Again"}, {"input": "90\n0", "output": "Try Again"}]
    if "student management system" in normalized:
        return [{"input": "1\nAsha\n2\n5", "output": "added"}, {"input": "2\n5", "output": "list"}, {"input": "3\nAsha\n5", "output": "Asha"}]
    if "library system" in normalized:
        return [{"input": "1\nJava Basics\n2\n5", "output": "added"}, {"input": "2\n5", "output": "list"}, {"input": "3\nJava\n5", "output": "Java"}]
    if "contact book" in normalized:
        return [{"input": "1\nRavi\n9876543210\n2\n5", "output": "saved"}, {"input": "3\nRavi\n5", "output": "Ravi"}, {"input": "4\nRavi\n5", "output": "deleted"}]
    if "atm simulator" in normalized:
        return [{"input": "1234\n1\n4", "output": "balance"}, {"input": "1234\n2\n1000\n4", "output": "deposit"}, {"input": "0000\n4", "output": "denied"}]
    if "shopping cart system" in normalized:
        return [{"input": "1\nApple\n50\n2\n4\n5", "output": "added"}, {"input": "3\nApple\n5", "output": "removed"}, {"input": "4\n5", "output": "total"}]
    if "expense tracker" in normalized:
        return [{"input": "1\nFood\nLunch\n100\n4\n5", "output": "total"}, {"input": "2\n5", "output": "list"}, {"input": "3\nFood\n5", "output": "Food"}]
    if "quiz application" in normalized:
        return [{"input": "A\nB\nC\nD", "output": "score"}, {"input": "A\nA\nA\nA", "output": "score"}, {"input": "Z\nZ\nZ\nZ", "output": "invalid"}]
    if "voting system" in normalized:
        return [{"input": "V101\nAlice\n5", "output": "recorded"}, {"input": "V101\nBob\n5", "output": "already"}, {"input": "V999\nAlice\n5", "output": "invalid"}]
    if "parking lot system" in normalized:
        return [{"input": "1\nMH01AB1234\n3\n4", "output": "parked"}, {"input": "2\nMH01AB1234\n4", "output": "removed"}, {"input": "3\n4", "output": "slot"}]
    if "bank account system" in normalized:
        return [{"input": "1\nRaj\n2\n1001\n500\n4\n5", "output": "account"}, {"input": "2\n1001\n5000\n5", "output": "deposit"}, {"input": "3\n1001\n999999\n5", "output": "insufficient"}]
    if "password validator" in normalized:
        return [{"input": "Strong@123", "output": "strong"}, {"input": "Medium12", "output": "moderate"}, {"input": "abc", "output": "weak"}]
    if "task manager" in normalized:
        return [{"input": "1\nStudy\nHigh\n4\n6", "output": "added"}, {"input": "2\nStudy\n6", "output": "complete"}, {"input": "3\nStudy\n6", "output": "removed"}]
    if "inventory system" in normalized:
        return [{"input": "1\nP001\nLaptop\n10\n50000\n4\n5", "output": "product"}, {"input": "3\nP001\n15\n5", "output": "insufficient"}, {"input": "2\nP001\n5\n5", "output": "restocked"}]
    if "ticket booking system" in normalized:
        return [{"input": "1\n3\n4", "output": "booked"}, {"input": "1\n3\n1\n3\n4", "output": "already"}, {"input": "2\n3\n4", "output": "cancelled"}]
    if "restaurant billing system" in normalized:
        return [{"input": "1\nPizza\n2\n200\n4\n5", "output": "total"}, {"input": "2\nPizza\n5", "output": "removed"}, {"input": "4\n5", "output": "bill"}]
    if "simple chat simulation" in normalized:
        return [{"input": "Hello everyone", "output": "message"}, {"input": "Hi team", "output": "chat"}, {"input": "Welcome", "output": "user"}]
    if "simple login system" in normalized:
        return [{"input": "1\nalice\nSecure@1\n2\nalice\nSecure@1\n3", "output": "welcome"}, {"input": "1\nbob\nPass@1\n2\nbob\nwrong\n2\nbob\nwrong\n2\nbob\nwrong\n3", "output": "locked"}, {"input": "2\nunknown\nPass@1\n3", "output": "invalid"}]
    if "employee management + sort by salary" in normalized:
        return [{"input": "1\n101\nAlice\nIT\n72000\n1\n102\nBob\nHR\n45000\n3\n1\n6\n5\n0", "output": "45000"}, {"input": "1\n201\nCarol\nHR\n50000\n4\nHR\n6\n5\n0", "output": "HR"}, {"input": "1\n301\nDan\nSales\n90000\n5\n6\n5\n0", "output": "90000"}]
    if "mini banking transaction history" in normalized:
        return [{"input": "1\n10000\n2\n3000\n3\n5", "output": "7000"}, {"input": "2\n500\n5", "output": "insufficient"}, {"input": "3\n5", "output": "transaction"}]
    if "course enrollment system" in normalized:
        return [{"input": "1\nCS101\n30\n2\nS001\nCS101\n5", "output": "enrolled"}, {"input": "1\nCS101\n1\n2\nS001\nCS101\n2\nS002\nCS101\n5", "output": "full"}, {"input": "2\nS001\nCS101\n2\nS001\nCS101\n5", "output": "already"}]
    if "hotel room booking" in normalized:
        return [{"input": "2\n101\nAsha\n4", "output": "booked"}, {"input": "2\n101\nAsha\n2\n101\nRavi\n4", "output": "not available"}, {"input": "3\n101\n4", "output": "checkout"}]
    if "stack implementation (manual)" in normalized:
        return [{"input": "1\n10\n1\n20\n2\n5", "output": "20"}, {"input": "2\n5", "output": "empty"}, {"input": "4\n((a+b)\n5", "output": "unbalanced"}]
    if "queue implementation (manual)" in normalized:
        return [{"input": "1\nReport.pdf\n1\nInvoice.pdf\n2\n5", "output": "report"}, {"input": "2\n5", "output": "empty"}, {"input": "1\nDoc1\n1\nDoc2\n4\n5", "output": "queue"}]
    if "e-voting with id validation" in normalized:
        return [{"input": "VID-001\nAlice\n5", "output": "recorded"}, {"input": "VID-001\nAlice\nVID-001\nBob\n5", "output": "already"}, {"input": "VID-999\nAlice\n5", "output": "invalid"}]
    if "multi-user scoreboard system" in normalized:
        return [{"input": "1\nPriya\n4500\n1\nRaj\n3200\n3\n6", "output": "4500"}, {"input": "2\nPriya\n500\n3\n6", "output": "updated"}, {"input": "4\n1\n6", "output": "top"}]
    return [
        {"input": "", "output": "IMPLEMENTATION_PENDING"},
        {"input": "", "output": "IMPLEMENTATION_PENDING"},
        {"input": "", "output": "IMPLEMENTATION_PENDING"},
    ]


def build_problem_starter_code(title):
    if title.lower() == "grade system":
        return (
            "import java.util.Scanner;\n\n"
            "public class GradeSystem {\n"
            "    public static void main(String[] args) {\n"
            "        Scanner sc = new Scanner(System.in);\n"
            "        int marks = sc.nextInt();\n\n"
            "        if (marks >= 90 && marks <= 100) {\n"
            "            System.out.println(\"Grade A+\");\n"
            "        } else if (marks >= 80) {\n"
            "            System.out.println(\"Grade A\");\n"
            "        } else if (marks >= 70) {\n"
            "            System.out.println(\"Grade B\");\n"
            "        } else if (marks >= 60) {\n"
            "            System.out.println(\"Grade C\");\n"
            "        } else if (marks >= 50) {\n"
            "            System.out.println(\"Grade D\");\n"
            "        } else {\n"
            "            System.out.println(\"Fail\");\n"
            "        }\n"
            "    }\n"
            "}\n"
        )
    return ""


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
        starter_code = build_problem_starter_code(title)
        row.starter_code = starter_code if starter_code else (row.starter_code or "")
        curated_cases = build_problem_test_cases(title)
        is_curated_pending = all(case.get("output") == "IMPLEMENTATION_PENDING" for case in curated_cases)
        if not is_curated_pending:
            row.test_cases = curated_cases
        else:
            parsed_cases = parsed_test_cases.get(problem_key, [])
            if len(parsed_cases) >= 3:
                row.test_cases = parsed_cases[:3]
            else:
                row.test_cases = curated_cases


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
