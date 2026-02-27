import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Trophy, Circle, AlertCircle, BookOpen, Search, CheckCircle2, Target, Play, ArrowRight, Lock, ExternalLink } from 'lucide-react';
import AppLayout from '@/components/layout/AppLayout';
import { practiceAPI } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { Link, useNavigate } from 'react-router-dom';

interface Problem {
  id: number;
  title: string;
  difficulty: 'Basic' | 'Medium' | 'Advanced';
  status: 'not-started' | 'attempted' | 'solved';
  tags: string[];
  description?: string;
  tutorialUrl?: string;
}

interface FeaturedCourse {
  id: string;
  title: string;
  description: string;
  modules: number;
  completed: number;
  topics: string[];
  language?: string;
}

interface LearningConcept {
  id: string;
  title: string;
  description: string;
  subtopics: string[];
  level: 'basic' | 'intermediate' | 'advanced';
  tutorialUrl?: string;
}

const learningPathConcepts: LearningConcept[] = [
  {
    id: 'java-introduction',
    title: 'Introduction to Java',
    description:
      'Get grounded in what Java is, why it was built, and how the Java toolchain translates your code into portable bytecode executed by the JVM.',
    subtopics: [
      'History & Features of Java',
      'Platform Independence',
      'JDK, JRE, JVM',
      'Bytecode Concept',
      'Compilation & Execution Process',
      'Java Program Structure',
      'main() Method Deep Concept',
    ],
    level: 'basic',
  },
  {
    id: 'jvm-architecture',
    title: 'JVM Architecture',
    description:
      'Understand how the JVM loads classes, manages memory, and executes bytecode so you can reason about performance and runtime behavior.',
    subtopics: [
      'Class Loader',
      'Method Area',
      'Heap Memory',
      'Stack Memory',
      'Program Counter Register',
      'Native Method Stack',
      'Execution Engine',
      'JIT Compiler',
    ],
    level: 'basic',
  },
  {
    id: 'data-types-variables',
    title: 'Data Types & Variables',
    description:
      'Master Java’s primitive types, wrappers, literals, and variable categories to write safe and predictable code.',
    subtopics: [
      'Primitive Data Types',
      'Wrapper Classes',
      'Literals',
      'Type Casting (Widening/Narrowing)',
      'Variables (Local, Instance, Static)',
      'Default Values',
      'final Keyword (Basic Usage)',
    ],
    level: 'basic',
  },
  {
    id: 'operators',
    title: 'Operators',
    description:
      'Apply Java operators correctly to build expressions, compare values, and manipulate data at the bit level.',
    subtopics: [
      'Arithmetic Operators',
      'Unary Operators',
      'Relational Operators',
      'Logical Operators',
      'Bitwise Operators',
      'Shift Operators',
      'Assignment Operators',
      'Ternary Operator',
      'instanceof Operator',
    ],
    level: 'basic',
  },
  {
    id: 'control-flow',
    title: 'Control Flow Statements',
    description:
      'Control program execution with conditionals, loops, and flow control keywords used in real-world logic.',
    subtopics: [
      'if / if-else / nested if',
      'switch (traditional & enhanced)',
      'for Loop',
      'while Loop',
      'do-while Loop',
      'for-each Loop',
      'break & continue',
      'Labeled break',
    ],
    level: 'basic',
  },
  {
    id: 'arrays',
    title: 'Arrays',
    description:
      'Learn how arrays are laid out in memory and how to model fixed-size collections in 1D, 2D, and jagged forms.',
    subtopics: [
      '1D Arrays',
      '2D Arrays',
      'Multidimensional Arrays',
      'Array Memory Representation',
      'Jagged Arrays',
      'Arrays Utility Class',
    ],
    level: 'basic',
  },
  {
    id: 'methods',
    title: 'Methods',
    description:
      'Design reusable logic with method declarations, parameters, overloading, recursion, and varargs.',
    subtopics: [
      'Method Declaration & Definition',
      'Parameter Passing (Call by Value Concept)',
      'Method Overloading',
      'Varargs',
      'Recursion',
      'Static vs Instance Methods',
    ],
    level: 'basic',
  },
  {
    id: 'basic-oop',
    title: 'Basic OOP Concepts',
    description:
      'Build your first object-oriented programs by mastering classes, objects, constructors, and encapsulation.',
    subtopics: [
      'Class & Object',
      'Object Creation Process',
      'Constructors (Default & Parameterized)',
      'this Keyword',
      'Static Keyword',
      'Encapsulation',
      'Access Modifiers (public, private, protected, default)',
      'Packages & import',
    ],
    level: 'basic',
  },
  {
    id: 'advanced-oop',
    title: 'Advanced OOP',
    description:
      'Go deeper into inheritance, polymorphism, abstraction, and the core Object class behavior.',
    subtopics: [
      'Inheritance (Single, Multilevel, Hierarchical)',
      'super Keyword',
      'Method Overriding',
      'Polymorphism (Compile-time & Runtime)',
      'Dynamic Method Dispatch',
      'Abstraction',
      'Abstract Classes',
      'Interfaces',
      'Multiple Inheritance via Interface',
      'final Keyword (Advanced Usage)',
      'Object Class Methods',
    ],
    level: 'intermediate',
  },
  {
    id: 'string-handling',
    title: 'String Handling',
    description:
      'Understand how strings are stored and manipulated, and when to use mutable string builders.',
    subtopics: [
      'String Class',
      'String Constant Pool',
      'Immutability Concept',
      'StringBuilder',
      'StringBuffer',
      'String Methods',
      'equals() vs ==',
    ],
    level: 'intermediate',
  },
  {
    id: 'exception-handling',
    title: 'Exception Handling',
    description:
      'Handle runtime failures gracefully with Java’s exception model, custom exceptions, and resource safety.',
    subtopics: [
      'Exception Hierarchy',
      'try-catch',
      'Multiple catch',
      'finally',
      'throw',
      'throws',
      'Custom Exceptions',
      'Checked vs Unchecked Exceptions',
      'try-with-resources',
    ],
    level: 'intermediate',
  },
  {
    id: 'inner-classes',
    title: 'Inner Classes',
    description:
      'Model nested class structures and understand scope using inner, local, and anonymous classes.',
    subtopics: [
      'Member Inner Class',
      'Static Nested Class',
      'Local Inner Class',
      'Anonymous Inner Class',
    ],
    level: 'intermediate',
  },
  {
    id: 'collections-framework',
    title: 'Collections Framework',
    description:
      'Choose the right collection for each use case, from lists and sets to maps and concurrent structures.',
    subtopics: [
      'Collection Interface',
      'List (ArrayList, LinkedList, Vector, Stack)',
      'Set (HashSet, LinkedHashSet, TreeSet)',
      'Map (HashMap, LinkedHashMap, TreeMap, Hashtable)',
      'Queue & Deque',
      'Iterator & ListIterator',
      'Comparable',
      'Comparator',
      'Sorting Collections',
      'Concurrent Collections',
    ],
    level: 'intermediate',
  },
  {
    id: 'generics',
    title: 'Generics',
    description:
      'Write type-safe APIs with generic classes and methods while understanding bounds and type erasure.',
    subtopics: [
      'Generic Classes',
      'Generic Methods',
      'Bounded Types',
      'Wildcards (?, extends, super)',
      'Type Erasure',
    ],
    level: 'advanced',
  },
  {
    id: 'file-handling-io',
    title: 'File Handling & I/O',
    description:
      'Read, write, buffer, and serialize data using Java’s core I/O and file system APIs.',
    subtopics: [
      'File Class',
      'Byte Streams',
      'Character Streams',
      'Buffered Streams',
      'Serialization',
      'Deserialization',
      'transient Keyword',
    ],
    level: 'intermediate',
  },
  {
    id: 'multithreading',
    title: 'Multithreading',
    description:
      'Create responsive programs with threads, synchronization, and inter-thread coordination.',
    subtopics: [
      'Thread Class',
      'Runnable Interface',
      'Thread Lifecycle',
      'Synchronization',
      'Inter-thread Communication',
      'wait(), notify(), notifyAll()',
      'Deadlock',
      'Thread Priority',
    ],
    level: 'intermediate',
  },
  {
    id: 'enums-annotations',
    title: 'Enums & Annotations',
    description:
      'Define fixed sets of values and annotate code for metadata and tooling support.',
    subtopics: [
      'Enum Types',
      'Built-in Annotations',
      'Custom Annotations',
      'Meta-Annotations',
    ],
    level: 'intermediate',
  },
  {
    id: 'java-8-features',
    title: 'Java 8+ Features',
    description:
      'Adopt modern Java capabilities such as lambdas, streams, records, and sealed classes.',
    subtopics: [
      'Lambda Expressions',
      'Functional Interfaces',
      'Method References',
      'Stream API',
      'Intermediate & Terminal Operations',
      'Optional Class',
      'Default & Static Methods in Interface',
      'Date & Time API',
      'var Keyword (Java 10)',
      'Switch Expressions',
      'Records (Java 14+)',
      'Sealed Classes',
    ],
    level: 'advanced',
  },
  {
    id: 'concurrency-advanced',
    title: 'Concurrency (Advanced)',
    description:
      'Scale concurrent workloads with executors, futures, parallel streams, and advanced locks.',
    subtopics: [
      'Executor Framework',
      'Callable & Future',
      'ForkJoin Framework',
      'CompletableFuture',
      'Thread Pools',
      'Parallel Streams',
      'Locks (ReentrantLock)',
      'Atomic Classes',
    ],
    level: 'advanced',
  },
  {
    id: 'jvm-memory-management',
    title: 'JVM & Memory Management',
    description:
      'Understand heap structure, garbage collection strategies, and class loading to tune performance.',
    subtopics: [
      'Heap Structure (Young/Old/Metaspace)',
      'Garbage Collection Algorithms',
      'GC Types (Serial, Parallel, G1, ZGC)',
      'Memory Leaks',
      'Reference Types (Strong, Weak, Soft, Phantom)',
      'Class Loading Mechanism',
    ],
    level: 'advanced',
  },
  {
    id: 'reflection-api',
    title: 'Reflection API',
    description:
      'Inspect and manipulate classes, fields, and methods at runtime for advanced tooling.',
    subtopics: [
      'Class Class',
      'Accessing Fields',
      'Accessing Methods',
      'Dynamic Object Creation',
    ],
    level: 'advanced',
  },
  {
    id: 'networking',
    title: 'Networking',
    description:
      'Build networked applications using sockets and HTTP connections in Java.',
    subtopics: [
      'Socket Programming',
      'ServerSocket',
      'DatagramSocket',
      'HTTP Connections',
    ],
    level: 'advanced',
  },
  {
    id: 'jdbc',
    title: 'JDBC',
    description:
      'Connect Java applications to databases, execute queries, and manage transactions.',
    subtopics: [
      'DriverManager',
      'Connection',
      'Statement',
      'PreparedStatement',
      'CallableStatement',
      'ResultSet',
      'Transactions',
      'Connection Pooling',
    ],
    level: 'advanced',
  },
  {
    id: 'gui-programming',
    title: 'GUI Programming',
    description:
      'Build desktop user interfaces using the Java GUI toolkits.',
    subtopics: [
      'AWT',
      'Swing',
      'JavaFX',
    ],
    level: 'advanced',
  },
  {
    id: 'security',
    title: 'Security',
    description:
      'Apply Java security fundamentals including cryptography and secure coding practices.',
    subtopics: [
      'Java Security Model',
      'Cryptography Basics',
      'Hashing',
      'KeyStore',
      'Secure Coding Practices',
    ],
    level: 'advanced',
  },
  {
    id: 'design-patterns',
    title: 'Design Patterns',
    description:
      'Use classic patterns to structure maintainable Java applications.',
    subtopics: [
      'Creational Patterns',
      'Structural Patterns',
      'Behavioral Patterns',
      'Singleton',
      'Factory',
      'Builder',
      'Observer',
      'MVC',
    ],
    level: 'advanced',
  },
  {
    id: 'enterprise-frameworks',
    title: 'Enterprise & Frameworks',
    description:
      'Ship production systems with the Java enterprise ecosystem and modern frameworks.',
    subtopics: [
      'Servlets',
      'JSP',
      'Spring Core',
      'Spring Boot',
      'Hibernate',
      'REST APIs',
      'Microservices',
      'Maven & Gradle',
      'Logging (Log4j, SLF4J)',
      'Testing (JUnit, Mockito)',
    ],
    level: 'advanced',
  },
];

const practiceProblemSets: Record<LearningConcept['level'], string[]> = {
  basic: [
    'Basic Calculator',
    'Even Odd Checker',
    'Largest of Three Numbers',
    'Leap Year Checker',
    'Factorial Calculator',
    'Prime Number Checker',
    'Fibonacci Series',
    'Reverse a Number',
    'Palindrome Number',
    'Armstrong Number',
    'GCD and LCM',
    'Multiplication Table',
    'Count Digits',
    'Sum of Digits',
    'Power Calculator',
    'Temperature Converter',
    'Grade System',
    'Pattern – Star Pyramid',
    'Pattern – Number Triangle',
    'Sum of N Natural Numbers',
    'Check Alphabet Type',
    'Simple Interest Calculator',
    'Swap Without Third Variable',
    'Count Vowel',
    'Character Frequency',
  ],
  intermediate: [
    'Find Largest in Array',
    'Find Second Largest',
    'Reverse Array',
    'Sort Array (Bubble Sort)',
    'Linear Search',
    'Binary Search',
    'Remove Duplicates (Array)',
    'Array Rotation',
    'Sum of Array Elements',
    'Count Even and Odd in Array',
    'String Reverse',
    'Palindrome String',
    'Anagram Checker',
    'Count Words in Sentence',
    'Remove Spaces',
    'String Compression',
    'Matrix Addition',
    'Matrix Multiplication',
    'Transpose Matrix',
    'Method Overloading Demo',
    'Student Result System',
    'Employee Salary System',
    'Custom Exception Demo',
    'Menu Driven Program',
    'Number Guessing Game',
  ],
  advanced: [
    'Student Management System',
    'Library System',
    'Contact Book',
    'ATM Simulator',
    'Shopping Cart System',
    'Quiz Application',
    'Voting System',
    'Parking Lot System',
    'Expense Tracker',
    'Bank Account System',
    'Inventory System',
    'Password Validator',
    'Ticket Booking System',
    'Restaurant Billing System',
    'Task Manager',
    'Employee Management System',
    'Stack Implementation',
    'Queue Implementation',
    'Simple Chat Simulation',
    'Mini Banking Transaction History',
    'Course Enrollment System',
    'Simple Login System',
    'Hotel Room Booking',
    'E-Voting with ID Validation',
    'Multi-User Scoreboard System',
  ],
};

const Practice = () => {
  const [activeTab, setActiveTab] = useState('learning-paths');
  const [searchTerm, setSearchTerm] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [problems, setProblems] = useState<Problem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [openLevels, setOpenLevels] = useState<string[]>([]);
  const [openPracticeLevels, setOpenPracticeLevels] = useState<string[]>([]);
  const { toast } = useToast();
  
  const normalizeLevel = (value?: string | null) => {
    const normalized = (value || '').toLowerCase();
    if (normalized === 'beginner' || normalized === 'intermediate' || normalized === 'advanced') {
      return normalized;
    }
    return 'beginner';
  };

  const getUserLevel = () => {
    try {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        const user = JSON.parse(userStr);
        return normalizeLevel(user.skill_level);
      }
    } catch (e) {
      console.error('Error reading user from localStorage:', e);
    }
    return 'beginner';
  };
  
  const userLevelLower = getUserLevel();
  const userLevel = userLevelLower.charAt(0).toUpperCase() + userLevelLower.slice(1);
  const navigate = useNavigate();

  const accessRank = userLevelLower === 'advanced' ? 2 : userLevelLower === 'intermediate' ? 1 : 0;
  const conceptRank: Record<LearningConcept['level'], number> = {
    basic: 0,
    intermediate: 1,
    advanced: 2,
  };
  const isConceptLocked = (level: LearningConcept['level']) => conceptRank[level] > accessRank;
  const levelLabel: Record<LearningConcept['level'], string> = {
    basic: 'Beginner',
    intermediate: 'Intermediate',
    advanced: 'Advanced',
  };
  const levelBulletClass: Record<LearningConcept['level'], string> = {
    basic: 'bg-success',
    intermediate: 'bg-warning',
    advanced: 'bg-destructive',
  };
  const levelOrder: LearningConcept['level'][] = ['basic', 'intermediate', 'advanced'];
  const groupedConcepts = {
    basic: learningPathConcepts.filter((concept) => concept.level === 'basic'),
    intermediate: learningPathConcepts.filter((concept) => concept.level === 'intermediate'),
    advanced: learningPathConcepts.filter((concept) => concept.level === 'advanced'),
  };
  
  const handleStartProblem = (problem: Problem) => {
    console.log('Starting problem:', problem.id);
    // Navigate to compiler with problem
  };

  const [featuredCourses, setFeaturedCourses] = useState<FeaturedCourse[]>([]);

  const readFeaturedCourses = (): FeaturedCourse[] => {
    try {
      const raw = localStorage.getItem('featured_courses');
      if (!raw) {
        return [];
      }
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) {
        return [];
      }
      return parsed
        .map((course) => ({
          id: String(course.id ?? ''),
          title: String(course.title ?? ''),
          description: String(course.description ?? ''),
          modules: Number(course.modules ?? 0),
          completed: Number(course.completed ?? 0),
          topics: Array.isArray(course.topics) ? course.topics.map((topic) => String(topic)) : [],
          language: course.language ? String(course.language) : undefined,
        }))
        .filter((course) => course.id && course.title);
    } catch {
      return [];
    }
  };

  const normalizeDifficulty = (value?: string | null): Problem['difficulty'] => {
    const normalized = (value || '').toLowerCase();
    if (['beginner', 'basic', 'easy'].includes(normalized)) return 'Basic';
    if (['intermediate', 'medium'].includes(normalized)) return 'Medium';
    if (['advanced', 'hard'].includes(normalized)) return 'Advanced';
    return 'Basic';
  };

  const normalizeStatus = (value?: string | null): Problem['status'] => {
    if (!value) return 'not-started';
    if (value === 'passed') return 'solved';
    if (value === 'failed' || value === 'started') return 'attempted';
    return 'not-started';
  };

  useEffect(() => {
    let isActive = true;
    const loadProblems = async () => {
      setIsLoading(true);
      try {
        const data = await practiceAPI.getProblems({ level: userLevelLower });
        if (!isActive) return;
        const normalized = data.map((problem) => ({
          id: problem.id,
          title: problem.title,
          difficulty: normalizeDifficulty(problem.difficulty),
          status: normalizeStatus(problem.attempt_status ?? null),
          tags: problem.tags || [],
        }));
        setProblems(normalized);
      } catch (error) {
        if (!isActive) return;
        setProblems([]);
        toast({
          title: 'Failed to load practice problems',
          description: error instanceof Error ? error.message : 'Please try again later.',
          variant: 'destructive',
        });
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    };
    loadProblems();
    return () => {
      isActive = false;
    };
  }, [toast, userLevelLower]);

  useEffect(() => {
    if (activeTab === 'learning-paths') {
      setOpenLevels([]);
    }
    if (activeTab === 'practice-arena') {
      setOpenPracticeLevels([]);
    }
  }, [activeTab]);

  useEffect(() => {
    const loadCourses = () => {
      const nextCourses = readFeaturedCourses().filter((course) => {
        if (!course.language) {
          return true;
        }
        return course.language.toLowerCase() === 'java';
      });
      setFeaturedCourses(nextCourses);
    };
    loadCourses();
    const handleStorage = (event: StorageEvent) => {
      if (event.key === 'featured_courses') {
        loadCourses();
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => {
      window.removeEventListener('storage', handleStorage);
    };
  }, []);

  const filteredProblems = useMemo(() => {
    return problems.filter((problem) => {
      const searchMatch =
        problem.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        problem.tags.some((tag) => tag.toLowerCase().includes(searchTerm.toLowerCase()));
      const difficultyMatch = difficultyFilter === 'All' || problem.difficulty === difficultyFilter;
      const statusMatch = statusFilter === 'All' || problem.status === statusFilter;
      return searchMatch && difficultyMatch && statusMatch;
    });
  }, [problems, searchTerm, difficultyFilter, statusFilter]);

  const statusCounts = useMemo(() => {
    return problems.reduce(
      (acc, problem) => {
        if (problem.status === 'solved') acc.solved += 1;
        if (problem.status === 'attempted') acc.attempted += 1;
        if (problem.status === 'not-started') acc.notStarted += 1;
        return acc;
      },
      { solved: 0, attempted: 0, notStarted: 0 }
    );
  }, [problems]);

  const totalProblems = statusCounts.solved + statusCounts.attempted + statusCounts.notStarted;
  const progressPercent = totalProblems > 0 ? Math.round((statusCounts.solved / totalProblems) * 100) : 0;

  return (
    <AppLayout>
      <div className="p-4">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
              Practice Arena
            </h1>
            
            <div className="flex items-center space-x-4">
              <Badge variant="outline" className="px-3 py-1">
                <Target className="w-4 h-4 mr-2" />
                {userLevel} Level
              </Badge>
              <Badge variant="secondary" className="px-3 py-1">
                <Trophy className="w-4 h-4 mr-2" />
                {statusCounts.solved} Solved
              </Badge>
            </div>
          </div>

          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full max-w-md grid-cols-2">
              <TabsTrigger value="learning-paths" className="text-base">Learning Paths</TabsTrigger>
              <TabsTrigger value="practice-arena" className="text-base">Practice Arena</TabsTrigger>
            </TabsList>

            {/* Learning Paths Tab */}
            <TabsContent value="learning-paths" className="space-y-6 mt-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold">Java Learning Path</h2>
                <Badge variant="outline">Java</Badge>
              </div>
              <Accordion
                type="multiple"
                value={openLevels}
                onValueChange={setOpenLevels}
                className="space-y-4"
              >
                {levelOrder.map((level) => {
                  const concepts = groupedConcepts[level];
                  const sectionLocked = isConceptLocked(level);
                  return (
                    <AccordionItem key={level} value={level} className="border border-border/30 rounded-xl bg-gradient-card group">
                      <AccordionTrigger className="px-6 py-4 hover:no-underline no-underline">
                        <div className="flex items-center justify-between w-full">
                          <div className="flex items-center gap-3">
                            <span className={`w-2.5 h-2.5 rounded-full ${levelBulletClass[level]}`} />
                            <span className="text-lg font-semibold">{levelLabel[level]}</span>
                            <Badge variant="outline">{concepts.length} concepts</Badge>
                          </div>
                          <div className="flex items-center gap-2 text-muted-foreground group-hover:text-primary">
                            {sectionLocked ? <Lock className="w-4 h-4" /> : null}
                            <span className="text-sm">{sectionLocked ? 'Locked' : 'Unlocked'}</span>
                          </div>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="px-6 pb-6">
                        <div className="space-y-4">
                          {concepts.map((concept, index) => {
                            const locked = isConceptLocked(concept.level);
                            return (
                              <Card key={concept.id} className="border-border/20 bg-background/40 hover:border-primary/30 transition-colors">
                                <CardContent className="p-6">
                                  <div className="flex items-center justify-between gap-6">
                                    <div className="flex items-start gap-4">
                                      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold">
                                        {String(index + 1).padStart(2, '0')}
                                      </div>
                                      <div>
                                        <div className="flex items-center gap-1 mb-1">
                                          <h3 className="text-lg font-semibold">{concept.title}</h3>
                                          <Badge variant="outline" className="capitalize">{concept.level}</Badge>
                                        </div>
                                        <p className="text-muted-foreground">{concept.description}</p>
                                      </div>
                                    </div>
                                    <Button
                                      variant="outline"
                                      className={`gap-2 ${locked ? 'cursor-not-allowed opacity-70' : ''}`}
                                      onClick={() => {
                                        if (locked) {
                                          toast({
                                            title: 'Locked learning path',
                                            description: `${concept.title} unlocks at the ${levelLabel[concept.level]} level.`,
                                            variant: 'destructive',
                                          });
                                          return;
                                        }
                                        navigate(`/learning-path/java/${concept.id}`);
                                      }}
                                    >
                                      {locked ? <Lock className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                                      {locked ? 'Locked' : 'Watch tutorial'}
                                    </Button>
                                  </div>
                                </CardContent>
                              </Card>
                            );
                          })}
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  );
                })}
              </Accordion>

              {/* Learning Paths/Courses Section */}
              <div className="mt-8">
                <h2 className="text-xl font-bold mb-4">Featured Courses</h2>
                <div className="grid gap-6">
                  {featuredCourses.length === 0 ? (
                    <Card className="border-border/20 bg-gradient-card">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <CardTitle className="text-xl">Java Course</CardTitle>
                              <Badge variant="outline">Java</Badge>
                            </div>
                            <p className="text-muted-foreground text-sm mb-4">
                              A theory-first Java course that takes learners from beginner fundamentals through advanced
                              concepts like OOP, collections, concurrency, JVM internals, and best practices.
                            </p>
                            <Button variant="link" className="h-auto px-0 text-primary" asChild>
                              <Link to="#" className="inline-flex items-center gap-2">
                                Open course
                                <ExternalLink className="h-4 w-4" />
                              </Link>
                            </Button>
                          </div>
                        </div>
                      </CardHeader>
                    </Card>
                  ) : (
                    featuredCourses.map((course) => (
                      <Card key={course.id} className="border-border/20 bg-gradient-card">
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <CardTitle className="text-xl">{course.title}</CardTitle>
                                <Badge variant="outline">Java</Badge>
                              </div>
                              <p className="text-muted-foreground text-sm mb-4">{course.description}</p>
                              {course.modules > 0 ? (
                                <>
                                  <div className="flex items-center space-x-4 mb-4">
                                    <div className="text-sm text-muted-foreground">
                                      {course.completed} / {course.modules} modules completed
                                    </div>
                                    <Trophy className="w-4 h-4 text-primary" />
                                  </div>
                                  <Progress value={(course.completed / course.modules) * 100} className="h-2 mb-4" />
                                </>
                              ) : null}
                              <div className="flex flex-wrap gap-2">
                                {course.topics.slice(0, 4).map((topic, idx) => (
                                  <Badge key={idx} variant="outline" className="text-xs">
                                    {topic}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                            <Button className="bg-primary hover:bg-primary/90 text-primary-foreground ml-4">
                              <Play className="w-4 h-4 mr-2" />
                              Start
                            </Button>
                          </div>
                        </CardHeader>
                      </Card>
                    ))
                  )}
                </div>
              </div>
            </TabsContent>

            {/* Practice Arena Tab */}
            <TabsContent value="practice-arena" className="space-y-4 mt-6">
              {/* Progress Overview */}
              <Card className="border-primary/20">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <BookOpen className="w-5 h-5 mr-2 text-primary" />
                    Your Progress
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center">
                    <div className="text-2xl font-bold text-success">{statusCounts.solved}</div>
                      <div className="text-sm text-muted-foreground">Problems Solved</div>
                    </div>
                    <div className="text-center">
                    <div className="text-2xl font-bold text-warning">{statusCounts.attempted}</div>
                      <div className="text-sm text-muted-foreground">Attempted</div>
                    </div>
                    <div className="text-center">
                    <div className="text-2xl font-bold text-muted-foreground">{statusCounts.notStarted}</div>
                      <div className="text-sm text-muted-foreground">Not Started</div>
                    </div>
                  </div>
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span>Overall Progress</span>
                    <span>{progressPercent}%</span>
                    </div>
                  <Progress value={progressPercent} className="h-2" />
                  {totalProblems === 0 ? (
                    <p className="text-sm text-muted-foreground mt-3">Practice stats will appear after your first attempt.</p>
                  ) : null}
                  </div>
                </CardContent>
              </Card>

              <Accordion
                type="multiple"
                value={openPracticeLevels}
                onValueChange={setOpenPracticeLevels}
                className="space-y-4"
              >
                {levelOrder.map((level) => {
                  const sectionLocked = isConceptLocked(level);
                  const problemsForLevel = practiceProblemSets[level];
                  return (
                    <AccordionItem key={level} value={level} className="border border-border/30 rounded-xl bg-gradient-card group">
                      <AccordionTrigger className="px-6 py-4 hover:no-underline no-underline">
                        <div className="flex items-center justify-between w-full">
                          <div className="flex items-center gap-3">
                            <span className={`w-2.5 h-2.5 rounded-full ${levelBulletClass[level]}`} />
                            <span className="text-lg font-semibold">{levelLabel[level]}</span>
                            <Badge variant="outline">{problemsForLevel.length} problems</Badge>
                          </div>
                          <div className="flex items-center gap-2 text-muted-foreground group-hover:text-primary">
                            {sectionLocked ? <Lock className="w-4 h-4" /> : null}
                            <span className="text-sm">{sectionLocked ? 'Locked' : 'Unlocked'}</span>
                          </div>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="px-6 pb-6">
                        {sectionLocked ? (
                          <Card className="border-muted">
                            <CardContent className="p-6 text-center">
                              <div className="flex items-center justify-center gap-2 text-muted-foreground mb-2">
                                <Lock className="w-4 h-4" />
                                <span>Locked</span>
                              </div>
                              <p className="text-sm text-muted-foreground">
                                Unlocks at the {levelLabel[level]} level.
                              </p>
                            </CardContent>
                          </Card>
                        ) : (
                          <div className="grid gap-3">
                            {problemsForLevel.map((title, index) => (
                              <Card key={`${level}-${title}`} className="border-border/20 bg-background/40">
                                <CardContent className="p-4">
                                  <div className="flex items-center justify-between gap-4">
                                    <div className="flex items-center gap-3">
                                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold text-sm">
                                        {String(index + 1).padStart(2, '0')}
                                      </div>
                                      <div className="text-sm font-medium">{title}</div>
                                    </div>
                                    <Button variant="outline" size="sm" className="gap-2">
                                      <Play className="w-4 h-4" />
                                      Solve
                                    </Button>
                                  </div>
                                </CardContent>
                              </Card>
                            ))}
                          </div>
                        )}
                      </AccordionContent>
                    </AccordionItem>
                  );
                })}
              </Accordion>

              {/* Filters */}
              <Card className="border-muted">
                <CardContent className="p-4">
                  <div className="flex flex-col sm:flex-row gap-4">
                    <div className="flex-1">
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                        <Input
                          placeholder="Search problems..."
                          className="pl-10"
                          value={searchTerm}
                          onChange={(e) => setSearchTerm(e.target.value)}
                        />
                      </div>
                    </div>
                    <Select value={difficultyFilter} onValueChange={setDifficultyFilter}>
                      <SelectTrigger className="w-full sm:w-40">
                        <SelectValue placeholder="Difficulty" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="All">All Difficulties</SelectItem>
                        <SelectItem value="Basic">Basic</SelectItem>
                        <SelectItem value="Medium">Medium</SelectItem>
                        <SelectItem value="Advanced">Advanced</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select value={statusFilter} onValueChange={setStatusFilter}>
                      <SelectTrigger className="w-full sm:w-40">
                        <SelectValue placeholder="Status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="All">All Status</SelectItem>
                        <SelectItem value="solved">Solved</SelectItem>
                        <SelectItem value="attempted">Attempted</SelectItem>
                        <SelectItem value="not-started">Not Started</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>

              {/* Problems List */}
              <div className="grid gap-4">
                {isLoading ? (
                  <Card className="border-muted">
                    <CardContent className="p-12 text-center">
                      <Target className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                      <h3 className="text-lg font-medium mb-2">Loading practice problems</h3>
                      <p className="text-muted-foreground">
                        Fetching the latest problems for your level.
                      </p>
                    </CardContent>
                  </Card>
                ) : (
                  filteredProblems.map((problem) => (
                    <Card key={problem.id} className="border-muted hover:border-primary/30 transition-colors">
                      <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4">
                            <div className="flex-shrink-0">
                              {problem.status === 'solved' ? (
                                <CheckCircle2 className="w-5 h-5 text-success" />
                              ) : problem.status === 'attempted' ? (
                                <AlertCircle className="w-5 h-5 text-warning" />
                              ) : (
                                <Circle className="w-5 h-5 text-muted-foreground" />
                              )}
                            </div>
                            
                            <div className="flex-1">
                              <div className="flex items-center space-x-3 mb-2">
                                <h3 className="text-lg font-semibold">{problem.title}</h3>
                                <Badge
                                  variant={
                                    problem.difficulty === 'Basic' ? 'default' :
                                    problem.difficulty === 'Medium' ? 'secondary' : 'destructive'
                                  }
                                  className="text-xs"
                                >
                                  {problem.difficulty}
                                </Badge>
                              </div>
                              
                              {problem.description ? (
                                <p className="text-muted-foreground text-sm mb-3">{problem.description}</p>
                              ) : null}
                              
                              <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                                <div className="flex flex-wrap gap-1">
                                  {problem.tags.map((tag, index) => (
                                    <Badge key={index} variant="outline" className="text-xs px-2 py-0">
                                      {tag}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            <Button
                              variant="outline"
                              onClick={() => handleStartProblem(problem)}
                            >
                              {problem.status === 'solved' ? 'Review' : 
                               problem.status === 'attempted' ? 'Continue' : 'Start'}
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>

              {!isLoading && filteredProblems.length === 0 && (
                <Card className="border-muted">
                  <CardContent className="p-12 text-center">
                    <Target className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                    <h3 className="text-lg font-medium mb-2">
                      {problems.length === 0 ? 'No practice problems yet' : 'No problems found'}
                    </h3>
                    <p className="text-muted-foreground">
                      {problems.length === 0
                        ? 'Problems will appear here once they are available.'
                        : 'Try adjusting your search criteria or filters.'}
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </AppLayout>
  );
};

export default Practice;
