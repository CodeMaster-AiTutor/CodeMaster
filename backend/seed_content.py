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
        "description": "Get grounded in what Java is, why it was built, and how the Java toolchain translates your code into portable bytecode executed by the JVM.",
        "level": "basic",
        "tutorial_url": "https://youtu.be/0XWb1PX9akw",
        "order_index": 1,
        "subtopics": ["History & Features of Java", "Platform Independence", "JDK, JRE, JVM", "Bytecode Concept", "Compilation & Execution Process", "Java Program Structure", "main() Method Deep Concept"],
    },
    {
        "slug": "jvm-architecture",
        "title": "JVM Architecture",
        "description": "Understand how the JVM loads classes, manages memory, and executes bytecode so you can reason about performance and runtime behavior.",
        "level": "basic",
        "tutorial_url": "https://youtu.be/V95XIvDJtdQ",
        "order_index": 2,
        "subtopics": ["Class Loader", "Method Area", "Heap Memory", "Stack Memory", "Program Counter Register", "Native Method Stack", "Execution Engine", "JIT Compiler"],
    },
    {
        "slug": "data-types-variables",
        "title": "Data Types & Variables",
        "description": "Master Java's primitive types, wrappers, literals, and variable categories to write safe and predictable code.",
        "level": "basic",
        "tutorial_url": "https://youtu.be/zc6q5dxJb7g",
        "order_index": 3,
        "subtopics": ["Primitive Data Types", "Wrapper Classes", "Literals", "Type Casting (Widening/Narrowing)", "Variables (Local, Instance, Static)", "Default Values", "final Keyword (Basic Usage)"],
    },
    {
        "slug": "operators",
        "title": "Operators",
        "description": "Apply Java operators correctly to build expressions, compare values, and manipulate data at the bit level.",
        "level": "basic",
        "tutorial_url": "https://youtu.be/o4HPvkSEPwg",
        "order_index": 4,
        "subtopics": ["Arithmetic Operators", "Unary Operators", "Relational Operators", "Logical Operators", "Bitwise Operators", "Shift Operators", "Assignment Operators", "Ternary Operator", "instanceof Operator"],
    },
    {
        "slug": "control-flow",
        "title": "Control Flow Statements",
        "description": "Control program execution with conditionals, loops, and flow control keywords used in real-world logic.",
        "level": "basic",
        "tutorial_url": "https://youtu.be/RNupSIbIbMw",
        "order_index": 5,
        "subtopics": ["if / if-else / nested if", "switch (traditional & enhanced)", "for Loop", "while Loop", "do-while Loop", "for-each Loop", "break & continue", "Labeled break"],
    },
    {
        "slug": "arrays",
        "title": "Arrays",
        "description": "Learn how arrays are laid out in memory and how to model fixed-size collections in 1D, 2D, and jagged forms.",
        "level": "basic",
        "tutorial_url": "https://youtu.be/avEm9LttA1I",
        "order_index": 6,
        "subtopics": ["1D Arrays", "2D Arrays", "Multidimensional Arrays", "Array Memory Representation", "Jagged Arrays", "Arrays Utility Class"],
    },
    {
        "slug": "methods",
        "title": "Methods",
        "description": "Design reusable logic with method declarations, parameters, overloading, recursion, and varargs.",
        "level": "basic",
        "tutorial_url": "https://youtu.be/upk0wiowp54",
        "order_index": 7,
        "subtopics": ["Method Declaration & Definition", "Parameter Passing (Call by Value Concept)", "Method Overloading", "Varargs", "Recursion", "Static vs Instance Methods"],
    },
    {
        "slug": "basic-oop",
        "title": "Basic OOP Concepts",
        "description": "Build your first object-oriented programs by mastering classes, objects, constructors, and encapsulation.",
        "level": "basic",
        "tutorial_url": "https://youtu.be/jMuE-aq5_oM",
        "order_index": 8,
        "subtopics": ["Class & Object", "Object Creation Process", "Constructors (Default & Parameterized)", "this Keyword", "Static Keyword", "Encapsulation", "Access Modifiers (public, private, protected, default)", "Packages & import"],
    },
    {
        "slug": "advanced-oop",
        "title": "Advanced OOP",
        "description": "Go deeper into inheritance, polymorphism, abstraction, and the core Object class behavior.",
        "level": "intermediate",
        "tutorial_url": "https://youtu.be/OPvC1hz-qSo",
        "order_index": 9,
        "subtopics": ["Inheritance (Single, Multilevel, Hierarchical)", "super Keyword", "Method Overriding", "Polymorphism (Compile-time & Runtime)", "Dynamic Method Dispatch", "Abstraction", "Abstract Classes", "Interfaces", "Multiple Inheritance via Interface", "final Keyword (Advanced Usage)", "Object Class Methods"],
    },
    {
        "slug": "string-handling",
        "title": "String Handling",
        "description": "Understand how strings are stored and manipulated, and when to use mutable string builders.",
        "level": "intermediate",
        "tutorial_url": "https://youtu.be/qeuTH5PntVc",
        "order_index": 10,
        "subtopics": ["String Class", "String Constant Pool", "Immutability Concept", "StringBuilder", "StringBuffer", "String Methods", "equals() vs =="],
    },
    {
        "slug": "exception-handling",
        "title": "Exception Handling",
        "description": "Handle runtime failures gracefully with Java's exception model, custom exceptions, and resource safety.",
        "level": "intermediate",
        "tutorial_url": "https://youtu.be/Tkpgi4g8zjM",
        "order_index": 11,
        "subtopics": ["Exception Hierarchy", "try-catch", "Multiple catch", "finally", "throw", "throws", "Custom Exceptions", "Checked vs Unchecked Exceptions", "try-with-resources"],
    },
    {
        "slug": "inner-classes",
        "title": "Inner Classes",
        "description": "Model nested class structures and understand scope using inner, local, and anonymous classes.",
        "level": "intermediate",
        "tutorial_url": "https://youtu.be/U8oX8eolEUk",
        "order_index": 12,
        "subtopics": ["Member Inner Class", "Static Nested Class", "Local Inner Class", "Anonymous Inner Class"],
    },
    {
        "slug": "collections-framework",
        "title": "Collections Framework",
        "description": "Choose the right collection for each use case, from lists and sets to maps and concurrent structures.",
        "level": "intermediate",
        "tutorial_url": "https://youtu.be/GJLHkQVMGjY",
        "order_index": 13,
        "subtopics": ["Collection Interface", "List (ArrayList, LinkedList, Vector, Stack)", "Set (HashSet, LinkedHashSet, TreeSet)", "Map (HashMap, LinkedHashMap, TreeMap, Hashtable)", "Queue & Deque", "Iterator & ListIterator", "Comparable", "Comparator", "Sorting Collections", "Concurrent Collections"],
    },
    {
        "slug": "file-handling-io",
        "title": "File Handling & I/O",
        "description": "Read, write, buffer, and serialize data using Java's core I/O and file system APIs.",
        "level": "intermediate",
        "tutorial_url": "https://youtu.be/zN00FDR-9PE",
        "order_index": 14,
        "subtopics": ["File Class", "Byte Streams", "Character Streams", "Buffered Streams", "Serialization", "Deserialization", "transient Keyword"],
    },
    {
        "slug": "multithreading",
        "title": "Multithreading",
        "description": "Create responsive programs with threads, synchronization, and inter-thread coordination.",
        "level": "intermediate",
        "tutorial_url": "https://youtu.be/ZWAjYep6k1c",
        "order_index": 15,
        "subtopics": ["Thread Class", "Runnable Interface", "Thread Lifecycle", "Synchronization", "Inter-thread Communication", "wait(), notify(), notifyAll()", "Deadlock", "Thread Priority"],
    },
    {
        "slug": "enums-annotations",
        "title": "Enums & Annotations",
        "description": "Define fixed sets of values and annotate code for metadata and tooling support.",
        "level": "intermediate",
        "tutorial_url": "https://youtu.be/RfMA8ELlT0I",
        "order_index": 16,
        "subtopics": ["Enum Types", "Built-in Annotations", "Custom Annotations", "Meta-Annotations"],
    },
    {
        "slug": "generics",
        "title": "Generics",
        "description": "Write type-safe APIs with generic classes and methods while understanding bounds and type erasure.",
        "level": "advanced",
        "tutorial_url": "https://youtu.be/zinLRbsnmT8",
        "order_index": 17,
        "subtopics": ["Generic Classes", "Generic Methods", "Bounded Types", "Wildcards (?, extends, super)", "Type Erasure"],
    },
    {
        "slug": "java-8-features",
        "title": "Java 8+ Features",
        "description": "Adopt modern Java capabilities such as lambdas, streams, records, and sealed classes.",
        "level": "advanced",
        "tutorial_url": "https://youtu.be/pM19quJEpRE",
        "order_index": 18,
        "subtopics": ["Lambda Expressions", "Functional Interfaces", "Method References", "Stream API", "Intermediate & Terminal Operations", "Optional Class", "Default & Static Methods in Interface", "Date & Time API", "var Keyword (Java 10)", "Switch Expressions", "Records (Java 14+)", "Sealed Classes"],
    },
    {
        "slug": "concurrency-advanced",
        "title": "Concurrency (Advanced)",
        "description": "Scale concurrent workloads with executors, futures, parallel streams, and advanced locks.",
        "level": "advanced",
        "tutorial_url": "https://youtu.be/ziYLsp7-sM0",
        "order_index": 19,
        "subtopics": ["Executor Framework", "Callable & Future", "ForkJoin Framework", "CompletableFuture", "Thread Pools", "Parallel Streams", "Locks (ReentrantLock)", "Atomic Classes"],
    },
    {
        "slug": "jvm-memory-management",
        "title": "JVM & Memory Management",
        "description": "Understand heap structure, garbage collection strategies, and class loading to tune performance.",
        "level": "advanced",
        "tutorial_url": "https://youtu.be/DiBTybBwM2Q",
        "order_index": 20,
        "subtopics": ["Heap Structure (Young/Old/Metaspace)", "Garbage Collection Algorithms", "GC Types (Serial, Parallel, G1, ZGC)", "Memory Leaks", "Reference Types (Strong, Weak, Soft, Phantom)", "Class Loading Mechanism"],
    },
    {
        "slug": "reflection-api",
        "title": "Reflection API",
        "description": "Inspect and manipulate classes, fields, and methods at runtime for advanced tooling.",
        "level": "advanced",
        "tutorial_url": "https://youtu.be/fF3Vhm8rDIU",
        "order_index": 21,
        "subtopics": ["Class Class", "Accessing Fields", "Accessing Methods", "Dynamic Object Creation"],
    },
    {
        "slug": "networking",
        "title": "Networking",
        "description": "Build networked applications using sockets and HTTP connections in Java.",
        "level": "advanced",
        "tutorial_url": "https://youtu.be/BXXW1ori3Dc",
        "order_index": 22,
        "subtopics": ["Socket Programming", "ServerSocket", "DatagramSocket", "HTTP Connections"],
    },
    {
        "slug": "jdbc",
        "title": "JDBC",
        "description": "Connect Java applications to databases, execute queries, and manage transactions.",
        "level": "advanced",
        "tutorial_url": "https://youtu.be/W7ZTBQcsyo4",
        "order_index": 23,
        "subtopics": ["DriverManager", "Connection", "Statement", "PreparedStatement", "CallableStatement", "ResultSet", "Transactions", "Connection Pooling"],
    },
    {
        "slug": "gui-programming",
        "title": "GUI Programming",
        "description": "Build desktop user interfaces using the Java GUI toolkits.",
        "level": "advanced",
        "tutorial_url": "https://youtu.be/7F06XNNo-cQ",
        "order_index": 24,
        "subtopics": ["AWT", "Swing", "JavaFX"],
    },
    {
        "slug": "security",
        "title": "Security",
        "description": "Apply Java security fundamentals including cryptography and secure coding practices.",
        "level": "advanced",
        "tutorial_url": "https://youtu.be/cLvgm7nOFzo",
        "order_index": 25,
        "subtopics": ["Java Security Model", "Cryptography Basics", "Hashing", "KeyStore", "Secure Coding Practices"],
    },
    {
        "slug": "design-patterns",
        "title": "Design Patterns",
        "description": "Use classic patterns to structure maintainable Java applications.",
        "level": "advanced",
        "tutorial_url": "https://youtu.be/JHeUnZ6dEVY",
        "order_index": 26,
        "subtopics": ["Creational Patterns", "Structural Patterns", "Behavioral Patterns", "Singleton", "Factory", "Builder", "Observer", "MVC"],
    },
    {
        "slug": "enterprise-frameworks",
        "title": "Enterprise & Frameworks",
        "description": "Ship production systems with the Java enterprise ecosystem and modern frameworks.",
        "level": "advanced",
        "tutorial_url": "https://youtu.be/-ifhgYLxirY",
        "order_index": 27,
        "subtopics": ["Servlets", "JSP", "Spring Core", "Spring Boot", "Hibernate", "REST APIs", "Microservices", "Maven & Gradle", "Logging (Log4j, SLF4J)", "Testing (JUnit, Mockito)"],
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
        end_index = len(raw_lines)
        for i in range(title_raw_index, len(raw_lines)):
            marker = (raw_lines[i] or "").strip().lower()
            if marker in {"test cases", "test scenarios", "test results"}:
                end_index = i
                break
        description_lines = [line.rstrip() for line in raw_lines[title_raw_index:end_index]]
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
    base_dir = os.path.dirname(__file__)
    candidate_dirs = [
        os.path.abspath(os.path.join(base_dir, "..", "problems")),
        os.path.abspath(os.path.join(base_dir, "problems")),
    ]
    problems_dir = next((d for d in candidate_dirs if os.path.isdir(d)), candidate_dirs[0])
    level_files = {
        "beginner": os.path.join(problems_dir, "Beginner Problems.txt"),
        "intermediate": os.path.join(problems_dir, "Intemediate Problems.txt"),
        "advanced": os.path.join(problems_dir, "Advanced Problems.txt"),
    }
    by_level = {}
    for level, file_path in level_files.items():
        by_level[level] = parse_problem_descriptions_from_file(file_path)
    return by_level


def load_all_problem_test_cases(parsed_descriptions):
    parsed = {}
    for level, level_descriptions in parsed_descriptions.items():
        parsed[level] = {}
        for key, description in level_descriptions.items():
            cases = extract_test_cases_from_description(description)
            parsed[level][key] = cases
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
        # TC3 changed from identity matrix (trivial) to a real non-trivial case
        # [[2,3],[1,4]] x [[1,2],[3,4]] = [[11,16],[13,18]]
        return [{"input": "2\n1 2\n3 4\n5 6\n7 8", "output": "19 22\n43 50"}, {"input": "1\n3\n4", "output": "12"}, {"input": "2\n2 3\n1 4\n1 2\n3 4", "output": "11 16\n13 18"}]
    if "method overloading" in normalized:
        # TC3 changed from 1+2+3=6 (same as product, ambiguous) to 2+3+4=9
        return [{"input": "2\n5\n3", "output": "8"}, {"input": "2\n2.5\n1.5", "output": "4.0"}, {"input": "3\n2\n3\n4", "output": "9"}]
    if "student result system" in normalized:
        # TC1: avg=70 → B, TC2: avg=97 → A+, TC3: avg=30 → F
        return [{"input": "5\n70\n70\n70\n70\n70", "output": "B"},
        {"input": "5\n95\n97\n98\n96\n99", "output": "A+"},
        {"input": "5\n20\n25\n30\n35\n40", "output": "F"}]
    if "employee salary system" in normalized:
        # Input: single basic salary. HRA=20%, DA=10%, Gross=Basic+HRA+DA
        return [{"input": "50000", "output": "65000"}, {"input": "30000", "output": "39000"}, {"input": "100000", "output": "130000"}]
    if "menu-driven program" in normalized:
        # TC1: valid choice 1 then exit, TC2: invalid choice then exit, TC3: exit directly
        return [{"input": "1\n4", "output": "Option 1 executed"}, {"input": "5\n4", "output": "Invalid"}, {"input": "4", "output": "Exit"}]
    if "custom exception demo" in normalized:
        # age<18 → exception, age>=18 → access granted
        return [{"input": "-1", "output": "Exception"}, {"input": "0", "output": "Exception"}, {"input": "25", "output": "Access granted"}]
    if "number guessing game" in normalized:
        return [{"input": "50\n0", "output": "Correct"}, {"input": "10\n0", "output": "Try Again"}, {"input": "90\n0", "output": "Try Again"}]
    if "student management system" in normalized:
        return [
            {"input": "1\nAsha\n1\n90\n4", "output": "added"},
            {"input": "1\nAsha\n1\n90\n2\n4", "output": "Asha"},
            {"input": "1\nAsha\n1\n90\n3\n1\n4", "output": "Asha"}
        ]
    if "library system" in normalized:
        return [
            {"input": "1\nJava Basics\nJohn\n001\n4", "output": "added"},
            {"input": "1\nJava Basics\nJohn\n001\n2\n4", "output": "Java Basics"},
            {"input": "1\nJava Basics\nJohn\n001\n3\nJava\n4", "output": "Java"}
        ]
    if "contact book" in normalized:
        return [{"input": "1\nRavi\n9876543210\n5", "output": "saved"}, {"input": "1\nRavi\n9876543210\n3\nRavi\n5", "output": "Ravi"}, {"input": "1\nRavi\n9876543210\n4\nRavi\n5", "output": "deleted"}]
    if "atm simulator" in normalized:
        return [{"input": "1234\n1\n4", "output": "Balance"}, {"input": "1234\n2\n1000\n4", "output": "Deposit successful"}, {"input": "0000", "output": "denied"}]
    if "shopping cart system" in normalized:
        return [{"input": "1\nApple\n50\n1\n5", "output": "added"}, {"input": "1\nApple\n50\n1\n3\nApple\n5", "output": "removed"}, {"input": "1\nApple\n50\n1\n4\n5", "output": "total"}]
    if "expense tracker" in normalized:
        return [{"input": "1\nFood\nLunch\n100\n5", "output": "added"}, {"input": "1\nFood\nLunch\n100\n2\n5", "output": "Food"}, {"input": "1\nFood\nLunch\n100\n4\n5", "output": "100"}]
    if "quiz application" in normalized:
        return [{"input": "B\nC\nB\nA\nB", "output": "Score: 5/5"}, {"input": "A\nA\nA\nA\nA", "output": "Score: 1/5"}, {"input": "B\nC\nB\nA\nA", "output": "Score: 4/5"}]
    if "voting system" in normalized:
        return [{"input": "V101\nAlice\n", "output": "recorded"}, {"input": "V101\nAlice\nV101\nBob\n", "output": "already"}, {"input": "V101\nNobody\n", "output": "Invalid candidate"}]
    if "parking lot system" in normalized:
        return [
            {"input": "1\n1\nMH01AB1234\n4", "output": "Assigned"},
            {"input": "1\n1\nMH01AB1234\n2\nMH01AB1234\n4", "output": "Removed"},
            {"input": "1\n3\n4", "output": "Slot"}
        ]
    if "bank account system" in normalized:
        return [{"input": "1\nRaj\n5", "output": "Account created"}, {"input": "1\nRaj\n2\n1001\n500\n5", "output": "Deposit successful"}, {"input": "1\nRaj\n3\n1001\n999999\n5", "output": "Insufficient"}]
    if "password validator" in normalized:
        return [{"input": "Strong@123", "output": "Strong"}, {"input": "Medium12", "output": "Moderate"}, {"input": "abc", "output": "Weak"}]
    if "task manager" in normalized:
        return [{"input": "1\nStudy\nHigh\n6", "output": "added"}, {"input": "1\nStudy\nHigh\n2\nStudy\n6", "output": "complete"}, {"input": "1\nStudy\nHigh\n3\nStudy\n6", "output": "removed"}]
    if "inventory system" in normalized:
        return [{"input": "1\nP001\nLaptop\n10\n50000\n5", "output": "added"}, {"input": "1\nP001\nLaptop\n10\n50000\n2\nP001\n5\n5", "output": "restocked"}, {"input": "1\nP001\nLaptop\n10\n50000\n3\nP001\n15\n5", "output": "Insufficient"}]
    if "ticket booking system" in normalized:
        return [{"input": "1\n3\n4", "output": "booked"}, {"input": "1\n3\n1\n3\n4", "output": "already booked"}, {"input": "1\n3\n2\n3\n4", "output": "cancelled"}]
    if "restaurant billing system" in normalized:
        return [{"input": "1\nPizza\n5", "output": "added"}, {"input": "1\nPizza\n2\nPizza\n5", "output": "removed"}, {"input": "1\nPizza\n4\n5", "output": "Total"}]
    if "simple chat simulation" in normalized:
        return [{"input": "Hello everyone\nexit", "output": "Hello everyone"}, {"input": "Hi team\nGoodbye\nexit", "output": "2 message(s) sent"}, {"input": "exit", "output": "No messages"}]
    if "simple login system" in normalized:
        return [{"input": "1\nalice\nSecure@1\n2\nalice\nSecure@1\n3", "output": "Welcome"}, {"input": "1\nbob\nPass@1\n2\nbob\nwrong\n2\nbob\nwrong\n2\nbob\nwrong\n3", "output": "locked"}, {"input": "2\nunknown\nPass@1\n3", "output": "not found"}]
    if "employee management + sort by salary" in normalized:
        return [{"input": "1\nAlice\nIT\n72000\n1\nBob\nHR\n45000\n3\n1\n5", "output": "45000"}, {"input": "1\nCarol\nHR\n50000\n4\nHR\n5", "output": "Carol"}, {"input": "1\nDan\nSales\n90000\n1\nEve\nSales\n60000\n3\n2\n5", "output": "90000"}]
    if "mini banking transaction history" in normalized:
        return [{"input": "1\n10000\n2\n3000\n4\n5", "output": "7000"}, {"input": "2\n500\n5", "output": "Insufficient"}, {"input": "1\n500\n3\n5", "output": "Deposit"}]
    if "course enrollment system" in normalized:
        return [{"input": "1\nCS101\n30\n2\nS001\nCS101\n5", "output": "enrolled"}, {"input": "1\nCS101\n1\n2\nS001\nCS101\n2\nS002\nCS101\n5", "output": "full"}, {"input": "1\nCS101\n30\n2\nS001\nCS101\n2\nS001\nCS101\n5", "output": "already"}]
    if "hotel room booking" in normalized:
        return [{"input": "2\n101\nAsha\n2\n5", "output": "booked"}, {"input": "2\n101\nAsha\n2\n2\n101\nRavi\n1\n5", "output": "Not available"}, {"input": "2\n101\nAsha\n2\n3\n101\n5", "output": "checkout"}]
    if "stack implementation (manual)" in normalized:
        return [{"input": "1\n10\n1\n20\n2\n5", "output": "Popped: 20"}, {"input": "2\n5", "output": "Underflow"}, {"input": "4\n((a+b)\n5", "output": "Unbalanced"}]
    if "queue implementation (manual)" in normalized:
        return [{"input": "1\nReport.pdf\n1\nInvoice.pdf\n2\n5", "output": "Processing: Report.pdf"}, {"input": "2\n5", "output": "Queue Empty"}, {"input": "1\nDoc1\n1\nDoc2\n4\n5", "output": "Job: Doc1"}]
    if "e-voting with id validation" in normalized:
        return [
            {"input": "1\nVID-2024-001\nAlice\n3", "output": "recorded"},
            {"input": "1\nVID-2024-001\nAlice\n1\nVID-2024-001\nBob\n3", "output": "already"},
            {"input": "1\nVID-999\nAlice\n3", "output": "invalid"},
        ]
    if "multi-user scoreboard system" in normalized:
        return [{"input": "1\nPriya\n4500\n1\nRaj\n3200\n3\n6", "output": "4500"}, {"input": "1\nPriya\n4500\n2\nPriya\n500\n3\n6", "output": "5000"}, {"input": "1\nPriya\n4500\n1\nRaj\n3200\n4\n1\n6", "output": "Priya"}]
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
    desired_slugs = {item["slug"] for item in LEARNING_PATHS}
    stale_rows = LearningPathConcept.query.filter(~LearningPathConcept.slug.in_(desired_slugs)).all()
    for row in stale_rows:
        db.session.delete(row)
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
        level_descriptions = parsed_descriptions.get(level, {})
        db_description = level_descriptions.get(problem_key, fallback_description)
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
            parsed_cases = parsed_test_cases.get(level, {}).get(problem_key, [])
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
