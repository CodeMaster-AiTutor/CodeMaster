from app import create_app
from app.services.java_executor import get_java_executor

app = create_app()
ctx = app.app_context()
ctx.push()

code = """
import java.util.Scanner;
public class CharFrequencyBug {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        System.out.print("Enter string: ");
        String str = sc.nextLine();
        System.out.print("Enter character: ");
        char target = sc.next().charAt(0);
        int count = 0;
        for (int i = 0; i < str.length() - 1; i++) {
            if (str.charAt(i) == target) count++;
        }
        System.out.println("Frequency: " + count);
        sc.close();
    }
}
"""

executor = get_java_executor()

# Test all three test case inputs
test_inputs = [
    'hello\nl',
    'mississippi\ns',
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
