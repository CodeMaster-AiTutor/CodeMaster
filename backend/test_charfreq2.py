from app import create_app
from app.services.java_executor import get_java_executor

app = create_app()
ctx = app.app_context()
ctx.push()

executor = get_java_executor()

code = (
    'import java.util.Scanner;\n'
    'public class CharFrequencyBug {\n'
    '    public static void main(String[] args) {\n'
    '        Scanner sc = new Scanner(System.in);\n'
    '        System.out.print("Enter string: ");\n'
    '        String str = sc.nextLine();\n'
    '        System.out.print("Enter character: ");\n'
    '        char target = sc.next().charAt(0);\n'
    '        int count = 0;\n'
    '        for (int i = 0; i < str.length() - 1; i++) {\n'
    '            if (str.charAt(i) == target) {\n'
    '                count++;\n'
    '            }\n'
    '        }\n'
    '        System.out.println("Frequency: " + count);\n'
    '        sc.close();\n'
    '    }\n'
    '}\n'
)

print('=== _validate_structure check ===')
errors = executor._validate_structure(code)
print('Validation errors:', errors)
print()

print('=== compile_and_execute check ===')
test_inputs = [
    'hello\no',
    'mississippi\ni',
    'java\na',
]

for inp in test_inputs:
    result = executor.compile_and_execute(code, input_data=inp + '\n')
    print('Input:   %r' % inp)
    print('Success: %s' % result.get('success'))
    print('Output:  %r' % result.get('output'))
    print('Errors:  %s' % result.get('errors'))
    print()

ctx.pop()
