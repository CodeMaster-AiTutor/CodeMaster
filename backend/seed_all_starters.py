from app import create_app
from app.models.practice import PracticeProblem
from app import db

app = create_app()
ctx = app.app_context()
ctx.push()

starters = {

# ─────────────────────────────────────────────────────────────────────────────
# BEGINNER (ID 1–25)
# ─────────────────────────────────────────────────────────────────────────────

1: """\
import java.util.Scanner;

public class EvenOddChecker {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        // TODO: print "Even" if n is even, "Odd" if n is odd
    }
}""",

2: """\
import java.util.Scanner;

public class LargestOfThree {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int a = sc.nextInt();
        int b = sc.nextInt();
        int c = sc.nextInt();
        // TODO: find and print the largest of a, b, c
    }
}""",

3: """\
import java.util.Scanner;

public class LeapYearChecker {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int year = sc.nextInt();
        // TODO: print "Leap Year" or "Not a Leap Year"
    }
}""",

4: """\
import java.util.Scanner;

public class TemperatureConverter {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        double temp = sc.nextDouble();
        String unit = sc.next().toUpperCase(); // "C" or "F"
        // TODO: if unit is C convert to F, if F convert to C, then print result
        // C to F: (temp * 9/5) + 32
        // F to C: (temp - 32) * 5/9
    }
}""",

5: """\
import java.util.Scanner;

public class GradeSystem {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int marks = sc.nextInt();
        // TODO: print grade based on marks
        // 90-100 -> Grade A+, 80-89 -> Grade A, 70-79 -> Grade B
        // 60-69 -> Grade C, 50-59 -> Grade D, below 50 -> Fail
    }
}""",

6: """\
import java.util.Scanner;

public class SimpleInterest {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        double principal = sc.nextDouble();
        double rate      = sc.nextDouble();
        double time      = sc.nextDouble();
        // TODO: calculate SI = (P * R * T) / 100 and print it
    }
}""",

7: """\
import java.util.Scanner;

public class SwapWithoutTemp {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int a = sc.nextInt();
        int b = sc.nextInt();
        // TODO: swap a and b WITHOUT a third variable, then print both
    }
}""",

8: """\
import java.util.Scanner;

public class CountVowels {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String text = sc.nextLine();
        // TODO: count and print the number of vowels (a,e,i,o,u) in text
    }
}""",

9: """\
import java.util.Scanner;

public class CharacterFrequency {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String text = sc.nextLine();         // e.g. "hello"
        char   ch   = sc.nextLine().charAt(0); // e.g. "l"
        // TODO: count and print how many times ch appears in text
    }
}""",

10: """\
import java.util.Scanner;

public class CheckAlphabetType {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        char ch = sc.next().charAt(0);
        // TODO: print "Uppercase", "Lowercase", "Digit", or "Special Character"
    }
}""",

11: """\
import java.util.Scanner;

public class SumNaturalNumbers {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        // TODO: compute and print the sum of first n natural numbers
    }
}""",

12: """\
import java.util.Scanner;

public class MultiplicationTable {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        // TODO: print multiplication table of n from 1 to 10
        // Suggested format: n x 1 = n
    }
}""",

13: """\
import java.util.Scanner;

public class CountDigits {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        // TODO: count and print the number of digits in n
    }
}""",

14: """\
import java.util.Scanner;

public class SumOfDigits {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        // TODO: compute and print the sum of digits of n
    }
}""",

15: """\
import java.util.Scanner;

public class BasicCalculator {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        double a  = sc.nextDouble();
        double b  = sc.nextDouble();
        String op = sc.next(); // "+", "-", "*", "/"
        // TODO: perform the operation and print the result
        // Handle division by zero gracefully
    }
}""",

16: """\
import java.util.Scanner;

public class FactorialCalculator {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        // TODO: compute and print n! (0! = 1)
    }
}""",

17: """\
import java.util.Scanner;

public class PrimeChecker {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        // TODO: print "Prime" or "Not Prime"
    }
}""",

18: """\
import java.util.Scanner;

public class FibonacciSeries {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        // TODO: print the first n Fibonacci numbers (starts 0 1 1 2 3 ...)
    }
}""",

19: """\
import java.util.Scanner;

public class ReverseNumber {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        // TODO: reverse the digits of n and print the result
    }
}""",

20: """\
import java.util.Scanner;

public class PalindromeNumber {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        // TODO: print "Palindrome" or "Not Palindrome"
    }
}""",

21: """\
import java.util.Scanner;

public class ArmstrongNumber {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        // TODO: print "Armstrong" or "Not Armstrong"
        // Armstrong: sum of each digit raised to the power of digit count equals n
    }
}""",

22: """\
import java.util.Scanner;

public class GcdLcm {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int a = sc.nextInt();
        int b = sc.nextInt();
        // TODO: compute and print GCD and LCM
        // LCM = (a * b) / GCD
    }
}""",

23: """\
import java.util.Scanner;

public class PowerCalculator {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int base = sc.nextInt();
        int exp  = sc.nextInt();
        // TODO: compute base^exp using a loop (no Math.pow), print the result
    }
}""",

24: """\
import java.util.Scanner;

public class StarPyramid {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        // TODO: print a left-aligned star pyramid with n rows
        // Row 1: *   Row 2: **   Row 3: ***  ...
    }
}""",

25: """\
import java.util.Scanner;

public class NumberTriangle {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        // TODO: print a number triangle with n rows
        // Row 1: 1   Row 2: 1 2   Row 3: 1 2 3  ...
    }
}""",

# ─────────────────────────────────────────────────────────────────────────────
# INTERMEDIATE (ID 26–50)
# ─────────────────────────────────────────────────────────────────────────────

26: """\
import java.util.Scanner;

public class FindLargest {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();
        // TODO: find and print the largest element
    }
}""",

27: """\
import java.util.Scanner;

public class ReverseArray {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();
        // TODO: reverse the array in-place and print the elements
    }
}""",

28: """\
import java.util.Scanner;

public class LinearSearch {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();
        int target = sc.nextInt();
        // TODO: print "Found at index X" or "Not Found"
    }
}""",

29: """\
import java.util.Scanner;

public class SumArray {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();
        // TODO: compute and print the sum of all elements
    }
}""",

30: """\
import java.util.Scanner;

public class CountEvenOdd {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();
        // TODO: count even and odd numbers, print both counts
        // Suggested format: Even: X  Odd: Y
    }
}""",

31: """\
import java.util.Scanner;

public class SecondLargest {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();
        // TODO: find and print the second largest element
    }
}""",

32: """\
import java.util.Scanner;

public class BubbleSort {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();
        // TODO: sort arr using bubble sort and print the sorted array
    }
}""",

33: """\
import java.util.Scanner;

public class BinarySearch {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt(); // already sorted
        int target = sc.nextInt();
        // TODO: binary search — print "Found at index X" or "Not Found"
    }
}""",

34: """\
import java.util.Scanner;

public class RemoveDuplicates {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();
        // TODO: print unique elements preserving order, no built-in Set
    }
}""",

35: """\
import java.util.Scanner;

public class ArrayRotation {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();
        int k = sc.nextInt();
        // TODO: left-rotate arr by k positions and print the result
    }
}""",

36: """\
import java.util.Scanner;

public class ReverseString {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine();
        // TODO: reverse s without built-in reverse() and print
    }
}""",

37: """\
import java.util.Scanner;

public class PalindromeString {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine();
        // TODO: print "Palindrome" or "Not Palindrome"
    }
}""",

38: """\
import java.util.Scanner;

public class CountWords {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String sentence = sc.nextLine();
        // TODO: count and print the number of words (no split() allowed)
    }
}""",

39: """\
import java.util.Scanner;

public class RemoveSpaces {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine();
        // TODO: remove all spaces from s and print (no replace() allowed)
    }
}""",

40: """\
import java.util.Scanner;

public class AnagramChecker {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s1 = sc.nextLine();
        String s2 = sc.nextLine();
        // TODO: print "Anagram" or "Not Anagram"
    }
}""",

41: """\
import java.util.Scanner;

public class StringCompression {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine();
        // TODO: compress using run-length encoding e.g. "aabccc" -> "a2b1c3"
        // If compressed string is NOT shorter than original, print original
    }
}""",

42: """\
import java.util.Scanner;

public class MatrixAddition {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[][] m1 = new int[n][n];
        int[][] m2 = new int[n][n];
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++) m1[i][j] = sc.nextInt();
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++) m2[i][j] = sc.nextInt();
        // TODO: add m1 and m2 element-wise and print the result matrix
    }
}""",

43: """\
import java.util.Scanner;

public class TransposeMatrix {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[][] mat = new int[n][n];
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++) mat[i][j] = sc.nextInt();
        // TODO: print the transpose of mat (swap rows and columns)
    }
}""",

44: """\
import java.util.Scanner;

public class MatrixMultiplication {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[][] m1 = new int[n][n];
        int[][] m2 = new int[n][n];
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++) m1[i][j] = sc.nextInt();
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++) m2[i][j] = sc.nextInt();
        // TODO: multiply m1 x m2 and print the result matrix
        // C[i][j] += A[i][k] * B[k][j]
    }
}""",

45: """\
import java.util.Scanner;

public class MethodOverloading {

    static int add(int a, int b)          { return a + b; }
    static int add(int a, int b, int c)   { return a + b + c; }
    static double add(double a, double b) { return a + b; }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int count = sc.nextInt(); // 2 or 3 values follow
        if (count == 2) {
            // TODO: read two numbers and call the right add() overload
            // If both are integers use add(int,int), if doubles use add(double,double)
            double a = sc.nextDouble();
            double b = sc.nextDouble();
            if (a == (int) a && b == (int) b)
                System.out.println(add((int) a, (int) b));
            else
                System.out.println(add(a, b));
        } else {
            // TODO: read three integers and call add(int,int,int)
            int a = sc.nextInt(), b = sc.nextInt(), c = sc.nextInt();
            System.out.println(add(a, b, c));
        }
    }
}""",

46: """\
import java.util.Scanner;

public class StudentResult {

    static int calcTotal(int[] marks) {
        int total = 0;
        for (int m : marks) total += m;
        return total;
    }

    static double calcAverage(int[] marks) {
        return (double) calcTotal(marks) / marks.length;
    }

    static String assignGrade(double avg) {
        if (avg >= 90) return "A+";
        else if (avg >= 80) return "A";
        else if (avg >= 70) return "B";
        else if (avg >= 60) return "C";
        else if (avg >= 50) return "D";
        else return "F";
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] marks = new int[n];
        for (int i = 0; i < n; i++) marks[i] = sc.nextInt();
        // TODO: compute total, average, grade and print them
        // Use the helper methods above
    }
}""",

47: """\
import java.util.Scanner;

public class EmployeeSalary {

    static double calcHRA(double basic)   { return basic * 0.20; }
    static double calcDA(double basic)    { return basic * 0.10; }
    static double calcGross(double basic) { return basic + calcHRA(basic) + calcDA(basic); }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        double basicSalary = sc.nextDouble();
        // TODO: compute and print HRA, DA, and Gross Salary
        // HRA = 20% of basic, DA = 10% of basic, Gross = Basic + HRA + DA
    }
}""",

48: """\
import java.util.Scanner;

public class MenuDrivenProgram {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Option A  2. Option B  3. Option C  4. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            switch (choice) {
                case 1: System.out.println("Option 1 executed"); break;
                case 2: System.out.println("Option 2 executed"); break;
                case 3: System.out.println("Option 3 executed"); break;
                case 4: System.out.println("Exit"); break;
                default: System.out.println("Invalid choice");
            }
        } while (choice != 4);
    }
}""",

49: """\
import java.util.Scanner;

class InvalidAgeException extends Exception {
    public InvalidAgeException(String message) { super(message); }
}

public class CustomExceptionDemo {

    static void validateAge(int age) throws InvalidAgeException {
        if (age < 18) throw new InvalidAgeException("Age must be 18 or above");
        // TODO: print "Access granted" for valid age
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int age = sc.nextInt();
        try {
            validateAge(age);
        } catch (InvalidAgeException e) {
            System.out.println("Exception: " + e.getMessage());
        }
    }
}""",

50: """\
import java.util.Scanner;
import java.util.Random;

public class NumberGuessingGame {
    public static void main(String[] args) {
        Scanner sc  = new Scanner(System.in);
        Random  rng = new Random();
        int secret  = rng.nextInt(100) + 1; // 1 to 100
        int attempts = 0;
        System.out.println("Guess a number between 1 and 100:");
        while (sc.hasNextInt()) {
            int guess = sc.nextInt();
            attempts++;
            if (guess == secret) {
                System.out.println("Correct! You got it in " + attempts + " attempt(s).");
                break;
            } else if (guess < secret) {
                System.out.println("Too Low! Try again.");
            } else {
                System.out.println("Too High! Try again.");
            }
        }
    }
}""",

# ─────────────────────────────────────────────────────────────────────────────
# ADVANCED (ID 51–75)
# ─────────────────────────────────────────────────────────────────────────────

51: """\
import java.util.ArrayList;
import java.util.Scanner;

public class StudentManagementSystem {

    static ArrayList<String[]> students = new ArrayList<>(); // {name, roll, marks}

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Add Student   2. View All   3. Search   4. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            sc.nextLine();
            switch (choice) {
                case 1:
                    String name  = sc.nextLine();
                    String roll  = sc.nextLine();
                    String marks = sc.nextLine();
                    students.add(new String[]{name, roll, marks});
                    System.out.println("Student added successfully.");
                    break;
                case 2:
                    // TODO: print all students
                    break;
                case 3:
                    String search = sc.nextLine();
                    // TODO: search by roll number, print details or "Not found"
                    break;
                case 4:
                    System.out.println("Goodbye.");
                    break;
            }
        } while (choice != 4);
    }
}""",

52: """\
import java.util.ArrayList;
import java.util.Scanner;

public class LibrarySystem {

    static ArrayList<String[]> books = new ArrayList<>(); // {title, author, isbn}

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Add Book   2. List All   3. Search   4. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            sc.nextLine();
            switch (choice) {
                case 1:
                    String title  = sc.nextLine();
                    String author = sc.nextLine();
                    String isbn   = sc.nextLine();
                    books.add(new String[]{title, author, isbn});
                    System.out.println("Book added.");
                    break;
                case 2:
                    // TODO: list all books
                    break;
                case 3:
                    String keyword = sc.nextLine();
                    // TODO: search by title keyword (case-insensitive), print matches or "Not found"
                    break;
                case 4:
                    System.out.println("Goodbye.");
                    break;
            }
        } while (choice != 4);
    }
}""",

53: """\
import java.util.HashMap;
import java.util.Scanner;

public class ContactBook {

    static HashMap<String, String> contacts = new HashMap<>();

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Add   2. View All   3. Search   4. Delete   5. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            sc.nextLine();
            switch (choice) {
                case 1:
                    String name  = sc.nextLine();
                    String phone = sc.nextLine();
                    contacts.put(name, phone);
                    System.out.println("Contact saved.");
                    break;
                case 2:
                    // TODO: print all contacts sorted by name
                    break;
                case 3:
                    String search = sc.nextLine();
                    // TODO: find and print contact or "Not found"
                    break;
                case 4:
                    String del = sc.nextLine();
                    // TODO: delete contact or print "Not found"
                    break;
                case 5:
                    System.out.println("Goodbye.");
                    break;
            }
        } while (choice != 5);
    }
}""",

54: """\
import java.util.Scanner;

public class ATMSimulator {

    static final int    CORRECT_PIN = 1234;
    static double balance = 10000.0;

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        System.out.print("Enter PIN: ");
        int pin = sc.nextInt();
        if (pin != CORRECT_PIN) {
            System.out.println("Access denied.");
            return;
        }
        System.out.println("PIN correct. Welcome!");
        int choice;
        do {
            System.out.println("1. Balance   2. Deposit   3. Withdraw   4. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            switch (choice) {
                case 1:
                    System.out.println("Balance: " + balance);
                    break;
                case 2:
                    double dep = sc.nextDouble();
                    balance += dep;
                    System.out.println("Deposit successful. Balance: " + balance);
                    break;
                case 3:
                    double amt = sc.nextDouble();
                    // TODO: withdraw amt if sufficient funds, else print "Insufficient funds"
                    break;
                case 4:
                    System.out.println("Thank you. Goodbye.");
                    break;
            }
        } while (choice != 4);
    }
}""",

55: """\
import java.util.ArrayList;
import java.util.Scanner;

public class ShoppingCartSystem {

    static ArrayList<String[]> cart = new ArrayList<>(); // {name, price, qty}

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Add Item   2. View Cart   3. Remove   4. Bill   5. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            sc.nextLine();
            switch (choice) {
                case 1:
                    String name  = sc.nextLine();
                    String price = sc.nextLine();
                    String qty   = sc.nextLine();
                    cart.add(new String[]{name, price, qty});
                    System.out.println(name + " added.");
                    break;
                case 2:
                    // TODO: print cart contents with subtotals
                    break;
                case 3:
                    String remove = sc.nextLine();
                    // TODO: remove item by name or print "Not found"
                    break;
                case 4:
                    // TODO: print bill with grand total, or "Cart is empty"
                    break;
                case 5:
                    System.out.println("Goodbye.");
                    break;
            }
        } while (choice != 5);
    }
}""",

56: """\
import java.util.ArrayList;
import java.util.Scanner;

public class ExpenseTracker {

    static ArrayList<String[]> expenses = new ArrayList<>(); // {category, desc, amount}

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Add   2. View All   3. By Category   4. Total   5. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            sc.nextLine();
            switch (choice) {
                case 1:
                    String cat    = sc.nextLine();
                    String desc   = sc.nextLine();
                    String amount = sc.nextLine();
                    expenses.add(new String[]{cat, desc, amount});
                    System.out.println("Expense added.");
                    break;
                case 2:
                    // TODO: print all expenses
                    break;
                case 3:
                    String filter = sc.nextLine();
                    // TODO: print expenses for category or "No expenses in this category"
                    break;
                case 4:
                    // TODO: print total of all expense amounts
                    break;
                case 5:
                    System.out.println("Goodbye.");
                    break;
            }
        } while (choice != 5);
    }
}""",

57: """\
import java.util.Scanner;

public class QuizApplication {

    static String[] questions = {
        "What is 2 + 2?",
        "What is the capital of France?",
        "Which language runs on JVM?",
        "What does CPU stand for?",
        "What is 5 * 6?"
    };
    static String[][] options = {
        {"A. 3", "B. 4", "C. 5", "D. 6"},
        {"A. Berlin", "B. Rome", "C. Paris", "D. Madrid"},
        {"A. Python", "B. Java", "C. C++", "D. Ruby"},
        {"A. Central Processing Unit", "B. Core Power Unit", "C. Computer Program Utility", "D. None"},
        {"A. 25", "B. 30", "C. 35", "D. 11"}
    };
    static char[] answers = {'B', 'C', 'B', 'A', 'B'};

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int score = 0;
        for (int i = 0; i < questions.length; i++) {
            System.out.println("Q" + (i + 1) + ": " + questions[i]);
            for (String opt : options[i]) System.out.println(opt);
            System.out.print("Your answer: ");
            if (!sc.hasNextLine()) break;
            String input = sc.nextLine().trim().toUpperCase();
            if (input.isEmpty() || input.charAt(0) < 'A' || input.charAt(0) > 'D') {
                System.out.println("Invalid option.");
                i--; // retry
                continue;
            }
            char ans = input.charAt(0);
            if (ans == answers[i]) { System.out.println("Correct!"); score++; }
            else System.out.println("Wrong! Correct: " + answers[i]);
        }
        System.out.println("Score: " + score + "/" + questions.length);
    }
}""",

58: """\
import java.util.HashMap;
import java.util.HashSet;
import java.util.Scanner;

public class VotingSystem {

    static HashSet<String> usedVoters  = new HashSet<>();
    static HashMap<String, Integer> tally = new HashMap<>();

    static {
        tally.put("Alice", 0);
        tally.put("Bob",   0);
        tally.put("Carol", 0);
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        while (sc.hasNextLine()) {
            String voterId   = sc.nextLine().trim();
            if (voterId.isEmpty()) break;
            String candidate = sc.hasNextLine() ? sc.nextLine().trim() : "";
            if (usedVoters.contains(voterId)) {
                System.out.println("Already voted.");
            } else if (!tally.containsKey(candidate)) {
                System.out.println("Invalid candidate.");
            } else {
                usedVoters.add(voterId);
                tally.put(candidate, tally.get(candidate) + 1);
                System.out.println("Vote recorded.");
            }
        }
    }
}""",

59: """\
import java.util.HashMap;
import java.util.Scanner;

public class ParkingLotSystem {

    static final int CAPACITY = 5;
    static HashMap<String, Integer> parked = new HashMap<>(); // plate -> slot
    static boolean[] slots = new boolean[CAPACITY + 1]; // true = occupied

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Park   2. Leave   3. Status   4. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            sc.nextLine();
            switch (choice) {
                case 1:
                    String plate = sc.nextLine();
                    // TODO: assign first free slot, print "Assigned slot X" or "Lot is full"
                    break;
                case 2:
                    String leave = sc.nextLine();
                    // TODO: remove vehicle by plate, print "Removed" or "Not found"
                    break;
                case 3:
                    // TODO: print status of all slots
                    break;
                case 4:
                    System.out.println("Goodbye.");
                    break;
            }
        } while (choice != 4);
    }
}""",

60: """\
import java.util.ArrayList;
import java.util.Scanner;

public class BankAccountSystem {

    static int nextId = 1001;
    static ArrayList<String[]> accounts = new ArrayList<>(); // {id, name, balance}

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. New Account   2. Deposit   3. Withdraw   4. All Accounts   5. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            sc.nextLine();
            switch (choice) {
                case 1:
                    String name = sc.nextLine();
                    accounts.add(new String[]{String.valueOf(nextId++), name, "0"});
                    System.out.println("Account created. ID: " + (nextId - 1));
                    break;
                case 2:
                    int depId  = sc.nextInt();
                    double dep = sc.nextDouble(); sc.nextLine();
                    // TODO: find account by id, add dep to balance, print "Deposit successful"
                    // or "Account not found"
                    break;
                case 3:
                    int witId  = sc.nextInt();
                    double wit = sc.nextDouble(); sc.nextLine();
                    // TODO: find account, withdraw if sufficient, else "Insufficient funds"
                    // or "Account not found"
                    break;
                case 4:
                    // TODO: print all accounts
                    break;
                case 5:
                    System.out.println("Goodbye.");
                    break;
            }
        } while (choice != 5);
    }
}""",

61: """\
import java.util.Scanner;

public class PasswordValidator {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String password = sc.nextLine();
        int score = 0;
        if (password.length() >= 8)                                       score++;
        if (password.chars().anyMatch(Character::isUpperCase))            score++;
        if (password.chars().anyMatch(Character::isDigit))                score++;
        if (password.chars().anyMatch(c -> "!@#$%".indexOf(c) >= 0))     score++;
        if (!password.contains(" "))                                       score++;
        // TODO: print "Strong" (score==5), "Moderate" (score>=3), or "Weak"
    }
}""",

62: """\
import java.util.ArrayList;
import java.util.Scanner;

public class TaskManager {

    static ArrayList<String[]> tasks = new ArrayList<>(); // {name, priority, status}

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Add   2. Complete   3. Delete   4. View Pending   5. View All   6. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            sc.nextLine();
            switch (choice) {
                case 1:
                    String name     = sc.nextLine();
                    String priority = sc.nextLine();
                    tasks.add(new String[]{name, priority, "Pending"});
                    System.out.println("Task added.");
                    break;
                case 2:
                    String comp = sc.nextLine();
                    // TODO: mark task as complete or print "Not found"
                    break;
                case 3:
                    String del = sc.nextLine();
                    // TODO: delete task or print "Not found"
                    break;
                case 4:
                    // TODO: print pending tasks
                    break;
                case 5:
                    // TODO: print all tasks
                    break;
                case 6:
                    System.out.println("Goodbye.");
                    break;
            }
        } while (choice != 6);
    }
}""",

63: """\
import java.util.ArrayList;
import java.util.Scanner;

public class InventorySystem {

    static ArrayList<String[]> products = new ArrayList<>(); // {id, name, qty, price}

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Add Product   2. Restock   3. Sell   4. View   5. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            sc.nextLine();
            switch (choice) {
                case 1:
                    String id    = sc.nextLine();
                    String name  = sc.nextLine();
                    String qty   = sc.nextLine();
                    String price = sc.nextLine();
                    products.add(new String[]{id, name, qty, price});
                    System.out.println("Product added.");
                    break;
                case 2:
                    String rid = sc.nextLine();
                    int    radd = sc.nextInt(); sc.nextLine();
                    // TODO: find product by id and increase qty
                    break;
                case 3:
                    String sid  = sc.nextLine();
                    int    sell = sc.nextInt(); sc.nextLine();
                    // TODO: sell if sufficient stock, else "Insufficient stock"
                    break;
                case 4:
                    // TODO: print all products with stock levels
                    break;
                case 5:
                    System.out.println("Goodbye.");
                    break;
            }
        } while (choice != 5);
    }
}""",

64: """\
import java.util.HashMap;
import java.util.Scanner;

public class TicketBookingSystem {

    static final int TOTAL_SEATS = 10;
    static HashMap<Integer, String> booked = new HashMap<>(); // seat -> "booked"

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Book Seat   2. Cancel   3. View Seats   4. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            switch (choice) {
                case 1:
                    int seat = sc.nextInt();
                    if (booked.containsKey(seat)) System.out.println("Seat already booked.");
                    else { booked.put(seat, "booked"); System.out.println("Seat " + seat + " booked."); }
                    break;
                case 2:
                    int cancel = sc.nextInt();
                    // TODO: cancel seat or print "Seat not booked"
                    break;
                case 3:
                    // TODO: print all seats and their status
                    break;
                case 4:
                    System.out.println("Goodbye.");
                    break;
            }
        } while (choice != 4);
    }
}""",

65: """\
import java.util.ArrayList;
import java.util.Scanner;

public class RestaurantBillingSystem {

    // Pre-defined menu
    static String[] menuNames  = {"Burger", "Pizza", "Pasta", "Salad", "Drink"};
    static double[] menuPrices = {  120.0,   250.0,  180.0,   90.0,   50.0 };
    static ArrayList<String[]> order = new ArrayList<>(); // {name, price}

    static int findMenuItem(String name) {
        for (int i = 0; i < menuNames.length; i++)
            if (menuNames[i].equalsIgnoreCase(name)) return i;
        return -1;
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Add Item   2. Remove Item   3. View Order   4. Bill   5. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            sc.nextLine();
            switch (choice) {
                case 1:
                    String item = sc.nextLine();
                    int idx = findMenuItem(item);
                    if (idx == -1) System.out.println("Item not found in menu.");
                    else { order.add(new String[]{menuNames[idx], String.valueOf(menuPrices[idx])}); System.out.println(item + " added."); }
                    break;
                case 2:
                    String rem = sc.nextLine();
                    // TODO: remove item from order or print "Not found"
                    break;
                case 3:
                    // TODO: print current order
                    break;
                case 4:
                    if (order.isEmpty()) { System.out.println("Order is empty."); break; }
                    double total = 0;
                    for (String[] o : order) total += Double.parseDouble(o[1]);
                    System.out.println("Total: " + total);
                    break;
                case 5:
                    System.out.println("Goodbye.");
                    break;
            }
        } while (choice != 5);
    }
}""",

66: """\
import java.util.ArrayList;
import java.util.Scanner;

public class SimpleChatSimulation {

    static ArrayList<String> messages = new ArrayList<>();

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        while (sc.hasNextLine()) {
            String msg = sc.nextLine().trim();
            if (msg.equalsIgnoreCase("exit")) break;
            if (!msg.isEmpty()) {
                messages.add(msg);
                System.out.println("You: " + msg);
            }
        }
        if (messages.isEmpty()) System.out.println("No messages.");
        else System.out.println(messages.size() + " message(s) sent.");
    }
}""",

67: """\
import java.util.HashMap;
import java.util.Scanner;

public class SimpleLoginSystem {

    static HashMap<String, String> users      = new HashMap<>();
    static HashMap<String, Integer> attempts  = new HashMap<>();

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Register   2. Login   3. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            sc.nextLine();
            switch (choice) {
                case 1:
                    String uname = sc.nextLine();
                    String pass  = sc.nextLine();
                    users.put(uname, pass);
                    attempts.put(uname, 0);
                    System.out.println("Registered successfully.");
                    break;
                case 2:
                    String lu = sc.nextLine();
                    String lp = sc.nextLine();
                    if (!users.containsKey(lu)) { System.out.println("User not found."); break; }
                    if (attempts.getOrDefault(lu, 0) >= 3) { System.out.println("Account locked."); break; }
                    if (users.get(lu).equals(lp)) {
                        attempts.put(lu, 0);
                        System.out.println("Welcome, " + lu + "!");
                    } else {
                        attempts.put(lu, attempts.getOrDefault(lu, 0) + 1);
                        int left = 3 - attempts.get(lu);
                        if (left <= 0) System.out.println("Account locked after 3 failed attempts.");
                        else System.out.println("Incorrect password. " + left + " attempt(s) left.");
                    }
                    break;
                case 3:
                    System.out.println("Goodbye.");
                    break;
            }
        } while (choice != 3);
    }
}""",

68: """\
import java.util.ArrayList;
import java.util.Scanner;

public class EmployeeManager {

    static ArrayList<String[]> employees = new ArrayList<>(); // {name, dept, salary}

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Add   2. View   3. Sort   4. Search Dept   5. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            sc.nextLine();
            switch (choice) {
                case 1:
                    String name   = sc.nextLine();
                    String dept   = sc.nextLine();
                    String salary = sc.nextLine();
                    employees.add(new String[]{name, dept, salary});
                    System.out.println("Employee added.");
                    break;
                case 2:
                    // TODO: print all employees
                    break;
                case 3:
                    int sortChoice = sc.nextInt(); sc.nextLine();
                    // TODO: sort by salary ascending (1) or descending (2) and print
                    break;
                case 4:
                    String searchDept = sc.nextLine();
                    // TODO: print all employees in dept or "No employees found"
                    break;
                case 5:
                    System.out.println("Goodbye.");
                    break;
            }
        } while (choice != 5);
    }
}""",

69: """\
import java.util.ArrayList;
import java.util.Scanner;

public class MiniBanking {

    static double balance = 0;
    static ArrayList<String> history = new ArrayList<>();

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Deposit   2. Withdraw   3. History   4. Balance   5. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            switch (choice) {
                case 1:
                    double dep = sc.nextDouble();
                    balance += dep;
                    history.add("Deposit: " + dep);
                    System.out.println("Deposit successful. Balance: " + balance);
                    break;
                case 2:
                    double wit = sc.nextDouble();
                    if (wit > balance) System.out.println("Insufficient balance.");
                    else { balance -= wit; history.add("Withdraw: " + wit); System.out.println("Withdrawal successful. Balance: " + balance); }
                    break;
                case 3:
                    if (history.isEmpty()) System.out.println("No transaction history.");
                    else history.forEach(System.out::println);
                    break;
                case 4:
                    System.out.println("Balance: " + balance);
                    break;
                case 5:
                    System.out.println("Goodbye.");
                    break;
            }
        } while (choice != 5);
    }
}""",

70: """\
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Scanner;

public class CourseEnrollmentSystem {

    static HashMap<String, Integer> courses  = new HashMap<>(); // courseId -> capacity
    static HashMap<String, ArrayList<String>> enrolled = new HashMap<>(); // courseId -> studentIds

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Add Course   2. Enroll   3. Drop   4. My Courses   5. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            sc.nextLine();
            switch (choice) {
                case 1:
                    String cid  = sc.nextLine();
                    int    cap  = sc.nextInt(); sc.nextLine();
                    courses.put(cid, cap);
                    enrolled.put(cid, new ArrayList<>());
                    System.out.println("Course added.");
                    break;
                case 2:
                    String sid = sc.nextLine();
                    String eid = sc.nextLine();
                    // TODO: enroll student if capacity allows, prevent duplicates
                    break;
                case 3:
                    String dsid = sc.nextLine();
                    String dcid = sc.nextLine();
                    // TODO: drop student from course or print "Not enrolled"
                    break;
                case 4:
                    String qsid = sc.nextLine();
                    // TODO: print courses student is enrolled in or "Not enrolled in any course"
                    break;
                case 5:
                    System.out.println("Goodbye.");
                    break;
            }
        } while (choice != 5);
    }
}""",

71: """\
import java.util.HashMap;
import java.util.Scanner;

public class HotelRoomBooking {

    // Room number -> {guestName, nights} (null = available)
    static HashMap<Integer, String[]> rooms = new HashMap<>();
    static double[] rates = {2000, 3500, 6000}; // Single, Double, Suite
    static String[] types = {"Single", "Double", "Suite"};

    static {
        // Pre-load rooms: 101-103 Single, 201-202 Double, 301 Suite
        int[] roomNums = {101, 102, 103, 201, 202, 301};
        for (int r : roomNums) rooms.put(r, null);
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Available   2. Book   3. Checkout   4. All Bookings   5. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            sc.nextLine();
            switch (choice) {
                case 1:
                    // TODO: print available rooms
                    break;
                case 2:
                    int    roomNo = sc.nextInt(); sc.nextLine();
                    String guest  = sc.nextLine();
                    int    nights = sc.nextInt(); sc.nextLine();
                    // TODO: book room if available, print confirmation or "Not available"
                    break;
                case 3:
                    int checkout = sc.nextInt(); sc.nextLine();
                    // TODO: print invoice and free the room, or "Room not booked"
                    break;
                case 4:
                    // TODO: print all current bookings or "No current bookings"
                    break;
                case 5:
                    System.out.println("Goodbye.");
                    break;
            }
        } while (choice != 5);
    }
}""",

72: """\
import java.util.Scanner;

public class StackManual {

    static final int CAPACITY = 5;
    static int[] stack = new int[CAPACITY];
    static int   top   = -1;

    static void push(int val) {
        if (top == CAPACITY - 1) { System.out.println("Stack Overflow."); return; }
        stack[++top] = val;
        System.out.println("Pushed: " + val);
    }

    static void pop() {
        if (top == -1) { System.out.println("Stack Underflow."); return; }
        System.out.println("Popped: " + stack[top--]);
    }

    static void peek() {
        if (top == -1) System.out.println("Stack is empty.");
        else System.out.println("Top: " + stack[top]);
    }

    static void checkBrackets(String expr) {
        int t = -1;
        char[] s = new char[expr.length()];
        for (char c : expr.toCharArray()) {
            if (c == '(' || c == '{' || c == '[') s[++t] = c;
            else if (c == ')' || c == '}' || c == ']') {
                if (t == -1) { System.out.println("Unbalanced"); return; }
                char open = s[t--];
                if ((c == ')' && open != '(') || (c == '}' && open != '{') || (c == ']' && open != '['))
                { System.out.println("Unbalanced"); return; }
            }
        }
        System.out.println(t == -1 ? "Balanced" : "Unbalanced");
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Push   2. Pop   3. Peek   4. Check Brackets   5. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            sc.nextLine();
            switch (choice) {
                case 1: push(sc.nextInt()); sc.nextLine(); break;
                case 2: pop();  break;
                case 3: peek(); break;
                case 4: checkBrackets(sc.nextLine()); break;
                case 5: System.out.println("Goodbye."); break;
            }
        } while (choice != 5);
    }
}""",

73: """\
import java.util.Scanner;

public class QueueManual {

    static final int CAPACITY = 4;
    static String[] queue = new String[CAPACITY];
    static int front = -1, rear = -1;

    static boolean isFull()  { return (rear + 1) % CAPACITY == front; }
    static boolean isEmpty() { return front == -1; }

    static void enqueue(String job) {
        if (isFull()) { System.out.println("Queue Full."); return; }
        if (isEmpty()) front = 0;
        rear = (rear + 1) % CAPACITY;
        queue[rear] = job;
        System.out.println(job + " queued.");
    }

    static void dequeue() {
        if (isEmpty()) { System.out.println("Queue Empty."); return; }
        System.out.println("Processing: " + queue[front]);
        if (front == rear) { front = rear = -1; }
        else front = (front + 1) % CAPACITY;
    }

    static void printerDemo() {
        System.out.println("--- Printer Queue ---");
        if (isEmpty()) { System.out.println("No jobs."); return; }
        int i = front;
        while (true) {
            System.out.println("Job: " + queue[i]);
            if (i == rear) break;
            i = (i + 1) % CAPACITY;
        }
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Enqueue   2. Dequeue   3. Peek   4. Printer Demo   5. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            sc.nextLine();
            switch (choice) {
                case 1: enqueue(sc.nextLine()); break;
                case 2: dequeue(); break;
                case 3:
                    if (isEmpty()) System.out.println("Queue is empty.");
                    else System.out.println("Next: " + queue[front]);
                    break;
                case 4: printerDemo(); break;
                case 5: System.out.println("Goodbye."); break;
            }
        } while (choice != 5);
    }
}""",

74: """\
import java.util.HashMap;
import java.util.HashSet;
import java.util.Scanner;

public class EVoting {

    // Pre-registered voter IDs
    static HashSet<String> validIds = new HashSet<>();
    static HashSet<String> usedIds  = new HashSet<>();
    static HashMap<String, Integer> tally = new HashMap<>();

    static {
        validIds.add("VID-001"); validIds.add("VID-002"); validIds.add("VID-003");
        validIds.add("VID-004"); validIds.add("VID-005");
        tally.put("Alice", 0); tally.put("Bob", 0); tally.put("Carol", 0);
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        while (sc.hasNextLine()) {
            String voterId = sc.nextLine().trim();
            if (voterId.isEmpty()) break;
            String candidate = sc.hasNextLine() ? sc.nextLine().trim() : "";
            if (!validIds.contains(voterId)) {
                System.out.println("Invalid voter ID.");
            } else if (usedIds.contains(voterId)) {
                System.out.println("Already voted.");
            } else if (!tally.containsKey(candidate)) {
                System.out.println("Invalid candidate.");
            } else {
                usedIds.add(voterId);
                tally.put(candidate, tally.get(candidate) + 1);
                System.out.println("Vote recorded.");
            }
        }
    }
}""",

75: """\
import java.util.ArrayList;
import java.util.Scanner;

public class Scoreboard {

    static ArrayList<String[]> players = new ArrayList<>(); // {name, score}

    static void sortDesc() {
        for (int i = 0; i < players.size() - 1; i++)
            for (int j = 0; j < players.size() - i - 1; j++)
                if (Integer.parseInt(players.get(j)[1]) < Integer.parseInt(players.get(j+1)[1])) {
                    String[] tmp = players.get(j);
                    players.set(j, players.get(j+1));
                    players.set(j+1, tmp);
                }
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int choice;
        do {
            System.out.println("1. Add Player   2. Add Score   3. Leaderboard   4. Top N   5. Bonus   6. Exit");
            System.out.print("> ");
            choice = sc.nextInt();
            sc.nextLine();
            switch (choice) {
                case 1:
                    String name  = sc.nextLine();
                    String score = sc.nextLine();
                    players.add(new String[]{name, score});
                    sortDesc();
                    System.out.println(name + " added.");
                    break;
                case 2:
                    String pname = sc.nextLine();
                    int    pts   = sc.nextInt(); sc.nextLine();
                    // TODO: find player and add pts to score, re-sort
                    break;
                case 3:
                    sortDesc();
                    for (int i = 0; i < players.size(); i++)
                        System.out.println((i+1) + ". " + players.get(i)[0] + "  " + players.get(i)[1]);
                    break;
                case 4:
                    int n = sc.nextInt(); sc.nextLine();
                    sortDesc();
                    for (int i = 0; i < Math.min(n, players.size()); i++)
                        System.out.println((i+1) + ". " + players.get(i)[0] + "  " + players.get(i)[1]);
                    break;
                case 5:
                    int threshold = sc.nextInt(); sc.nextLine();
                    int bonus     = sc.nextInt(); sc.nextLine();
                    // TODO: add bonus to all players with score > threshold
                    break;
                case 6:
                    System.out.println("Goodbye.");
                    break;
            }
        } while (choice != 6);
    }
}""",

}

updated = 0
for pid, code in starters.items():
    p = PracticeProblem.query.get(pid)
    if p:
        p.starter_code = code.strip()
        updated += 1
        print(f"Updated ID:{pid} | {p.title}")
    else:
        print(f"NOT FOUND: ID:{pid}")

db.session.commit()
print(f"\nDone. Updated {updated} starter codes.")
ctx.pop()
