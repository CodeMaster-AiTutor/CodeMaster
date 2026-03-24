from app import create_app
from app.models.practice import PracticeProblem
from app import db

app = create_app()
ctx = app.app_context()
ctx.push()

updates = {

    'Grade System': {
        'test_cases': [
            {'input': '95',  'output': 'Grade A+'},
            {'input': '70',  'output': 'Grade B'},
            {'input': '45',  'output': 'Fail'},
            {'input': '150', 'output': 'Invalid'},
            {'input': '-5',  'output': 'Invalid'},
        ],
        'starter_code': """\
import java.util.Scanner;

public class GradeSystem {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int marks = sc.nextInt();

        if (marks < 0 || marks > 100) {
            System.out.println("Invalid");
        } else if (marks >= 90) {
            System.out.println("Grade A+");
        } else if (marks >= 80) {
            System.out.println("Grade A");
        } else if (marks >= 70) {
            System.out.println("Grade B");
        } else if (marks >= 60) {
            System.out.println("Grade C");
        } else if (marks >= 50) {
            System.out.println("Grade D");
        } else {
            System.out.println("Fail");
        }
        sc.close();
    }
}"""
    },

    'Temperature Converter': {
        'test_cases': [
            {'input': '100\nC', 'output': '212.0'},
            {'input': '25\nC',  'output': '77.0'},
            {'input': '37\nC',  'output': '98.6'},
            {'input': '32\nF',  'output': '0.0'},
            {'input': '100\nX', 'output': 'Invalid'},
        ],
        'starter_code': """\
import java.util.Scanner;

public class TemperatureConverter {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        double temp = sc.nextDouble();
        char unit = sc.next().charAt(0);

        if (unit == 'C' || unit == 'c') {
            double f = (temp * 9 / 5) + 32;
            System.out.println(f + " F");
        } else if (unit == 'F' || unit == 'f') {
            double c = (temp - 32) * 5 / 9;
            System.out.println(c + " C");
        } else {
            System.out.println("Invalid unit");
        }
        sc.close();
    }
}"""
    },

    'Factorial Calculator': {
        'test_cases': [
            {'input': '5',  'output': '120'},
            {'input': '0',  'output': '1'},
            {'input': '10', 'output': '3628800'},
            {'input': '-3', 'output': 'Invalid'},
        ],
        'starter_code': """\
import java.util.Scanner;

public class FactorialCalculator {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();

        if (n < 0) {
            System.out.println("Invalid");
        } else {
            long result = 1;
            for (int i = 2; i <= n; i++) {
                result *= i;
            }
            System.out.println(result);
        }
        sc.close();
    }
}"""
    },

    'Prime Number Checker': {
        'test_cases': [
            {'input': '7',  'output': 'Prime'},
            {'input': '4',  'output': 'Not Prime'},
            {'input': '2',  'output': 'Prime'},
            {'input': '1',  'output': 'Not Prime'},
            {'input': '-5', 'output': 'Invalid'},
        ],
        'starter_code': """\
import java.util.Scanner;

public class PrimeChecker {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();

        if (n < 0) {
            System.out.println("Invalid");
        } else if (n < 2) {
            System.out.println("Not Prime");
        } else {
            boolean isPrime = true;
            for (int i = 2; i <= Math.sqrt(n); i++) {
                if (n % i == 0) {
                    isPrime = false;
                    break;
                }
            }
            System.out.println(isPrime ? "Prime" : "Not Prime");
        }
        sc.close();
    }
}"""
    },

    'Leap Year Checker': {
        'test_cases': [
            {'input': '2000', 'output': 'Leap Year'},
            {'input': '1900', 'output': 'Not a Leap Year'},
            {'input': '2024', 'output': 'Leap Year'},
            {'input': '0',    'output': 'Invalid'},
            {'input': '-100', 'output': 'Invalid'},
        ],
        'starter_code': """\
import java.util.Scanner;

public class LeapYearChecker {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int year = sc.nextInt();

        if (year <= 0) {
            System.out.println("Invalid");
        } else if ((year % 4 == 0 && year % 100 != 0) || (year % 400 == 0)) {
            System.out.println("Leap Year");
        } else {
            System.out.println("Not a Leap Year");
        }
        sc.close();
    }
}"""
    },

    'Basic Calculator': {
        'test_cases': [
            {'input': '10\n5\n+', 'output': '15'},
            {'input': '10\n5\n-', 'output': '5'},
            {'input': '10\n5\n*', 'output': '50'},
            {'input': '10\n0\n/', 'output': 'Cannot divide by zero'},
            {'input': '9\n3\n/',  'output': '3'},
        ],
        'starter_code': """\
import java.util.Scanner;

public class BasicCalculator {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        double a = sc.nextDouble();
        double b = sc.nextDouble();
        char op = sc.next().charAt(0);

        if (op == '+') System.out.println(a + b);
        else if (op == '-') System.out.println(a - b);
        else if (op == '*') System.out.println(a * b);
        else if (op == '/') {
            if (b == 0) System.out.println("Cannot divide by zero");
            else System.out.println(a / b);
        } else {
            System.out.println("Invalid operator");
        }
        sc.close();
    }
}"""
    },

    'Power Calculator': {
        'test_cases': [
            {'input': '2\n10', 'output': '1024'},
            {'input': '3\n3',  'output': '27'},
            {'input': '5\n0',  'output': '1'},
            {'input': '2\n-1', 'output': 'Invalid'},
        ],
        'starter_code': """\
import java.util.Scanner;

public class PowerCalculator {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int base = sc.nextInt();
        int exp = sc.nextInt();

        if (exp < 0) {
            System.out.println("Invalid");
        } else {
            long result = 1;
            for (int i = 0; i < exp; i++) {
                result *= base;
            }
            System.out.println(result);
        }
        sc.close();
    }
}"""
    },

    'Palindrome Number': {
        'test_cases': [
            {'input': '121', 'output': 'Palindrome'},
            {'input': '123', 'output': 'Not Palindrome'},
            {'input': '0',   'output': 'Palindrome'},
            {'input': '-121','output': 'Invalid'},
        ],
        'starter_code': """\
import java.util.Scanner;

public class PalindromeNumber {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();

        if (n < 0) {
            System.out.println("Invalid");
        } else {
            int original = n, reversed = 0;
            while (n != 0) {
                reversed = reversed * 10 + n % 10;
                n /= 10;
            }
            System.out.println(original == reversed ? "Palindrome" : "Not Palindrome");
        }
        sc.close();
    }
}"""
    },

    'Armstrong Number': {
        'test_cases': [
            {'input': '153', 'output': 'Armstrong'},
            {'input': '123', 'output': 'Not Armstrong'},
            {'input': '370', 'output': 'Armstrong'},
            {'input': '-5',  'output': 'Invalid'},
        ],
        'starter_code': """\
import java.util.Scanner;

public class ArmstrongNumber {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();

        if (n < 0) {
            System.out.println("Invalid");
        } else {
            int original = n, sum = 0, digits = String.valueOf(n).length();
            while (n != 0) {
                int d = n % 10;
                sum += (int) Math.pow(d, digits);
                n /= 10;
            }
            System.out.println(original == sum ? "Armstrong" : "Not Armstrong");
        }
        sc.close();
    }
}"""
    },

    'Fibonacci Series': {
        'test_cases': [
            {'input': '5', 'output': '0 1 1 2 3'},
            {'input': '1', 'output': '0'},
            {'input': '7', 'output': '0 1 1 2 3 5 8'},
            {'input': '0', 'output': 'Invalid'},
            {'input': '-3','output': 'Invalid'},
        ],
        'starter_code': """\
import java.util.Scanner;

public class FibonacciSeries {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();

        if (n <= 0) {
            System.out.println("Invalid");
        } else {
            int a = 0, b = 1;
            for (int i = 0; i < n; i++) {
                System.out.print(a);
                if (i < n - 1) System.out.print(" ");
                int temp = a + b;
                a = b;
                b = temp;
            }
            System.out.println();
        }
        sc.close();
    }
}"""
    },

    'GCD and LCM': {
        'test_cases': [
            {'input': '12\n18', 'output': 'GCD: 6\nLCM: 36'},
            {'input': '5\n7',   'output': 'GCD: 1\nLCM: 35'},
            {'input': '8\n12',  'output': 'GCD: 4\nLCM: 24'},
            {'input': '0\n5',   'output': 'Invalid'},
            {'input': '-4\n6',  'output': 'Invalid'},
        ],
        'starter_code': """\
import java.util.Scanner;

public class GcdLcm {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int a = sc.nextInt();
        int b = sc.nextInt();

        if (a <= 0 || b <= 0) {
            System.out.println("Invalid");
        } else {
            int gcd = a, temp = b;
            while (temp != 0) {
                int r = gcd % temp;
                gcd = temp;
                temp = r;
            }
            int lcm = (a * b) / gcd;
            System.out.println("GCD: " + gcd);
            System.out.println("LCM: " + lcm);
        }
        sc.close();
    }
}"""
    },

    'Count Vowels': {
        'test_cases': [
            {'input': 'hello',     'output': '2'},
            {'input': 'java',      'output': '2'},
            {'input': 'rhythm',    'output': '0'},
            {'input': 'EDUCATION', 'output': '5'},
        ],
        'starter_code': """\
import java.util.Scanner;

public class CountVowels {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine();
        int count = 0;
        for (char c : s.toLowerCase().toCharArray()) {
            if ("aeiou".indexOf(c) >= 0) count++;
        }
        System.out.println(count);
        sc.close();
    }
}"""
    },

    'Reverse a Number': {
        'test_cases': [
            {'input': '1234', 'output': '4321'},
            {'input': '100',  'output': '1'},
            {'input': '9',    'output': '9'},
            {'input': '-567', 'output': 'Invalid'},
        ],
        'starter_code': """\
import java.util.Scanner;

public class ReverseNumber {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();

        if (n < 0) {
            System.out.println("Invalid");
        } else {
            int reversed = 0;
            while (n != 0) {
                reversed = reversed * 10 + n % 10;
                n /= 10;
            }
            System.out.println(reversed);
        }
        sc.close();
    }
}"""
    },

}

for title, data in updates.items():
    p = PracticeProblem.query.filter_by(title=title).first()
    if not p:
        print('NOT FOUND: %s' % title)
        continue
    if 'test_cases' in data:
        p.test_cases = data['test_cases']
    if 'starter_code' in data:
        p.starter_code = data['starter_code']
    print('Updated: %s (%d test cases)' % (title, len(data.get('test_cases', []))))

db.session.commit()
print('\nAll done.')
ctx.pop()
