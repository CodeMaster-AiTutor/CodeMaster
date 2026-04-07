import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import AppLayout from '@/components/layout/AppLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';
import { ArrowLeft, Lock } from 'lucide-react';
import { contentAPI } from '@/lib/api';
import { toast } from '@/hooks/use-toast';

type LearningConcept = {
  id: string;
  title: string;
  description: string;
  subtopics: string[];
  level: 'basic' | 'intermediate' | 'advanced';
  tutorialUrl?: string;
};

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
    tutorialUrl: '/videos/v1_exp_video.mp4',
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

const LearningPathTutorial = () => {
  const { conceptId } = useParams();
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
    } catch {
      return 'beginner';
    }
    return 'beginner';
  };
  const userLevelLower = getUserLevel();
  const accessRank = userLevelLower === 'advanced' ? 2 : userLevelLower === 'intermediate' ? 1 : 0;
  const conceptRank: Record<LearningConcept['level'], number> = {
    basic: 0,
    intermediate: 1,
    advanced: 2,
  };
  const concept = useMemo(
    () => learningPathConcepts.find((item) => item.id === conceptId),
    [conceptId]
  );
  const locked = concept ? conceptRank[concept.level] > accessRank : false;
  const earnablePoints = concept ? (concept.level === 'basic' ? 10 : concept.level === 'intermediate' ? 15 : 20) : 0;
  const [videoPointsAwarded, setVideoPointsAwarded] = useState<number>(0);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const watchedSecondsRef = useRef(0);
  const lastMediaTimeRef = useRef(0);
  const lastWallTimeRef = useRef(0);
  const invalidPlaybackRef = useRef(false);
  const completionRequestRef = useRef(false);
  const warningShownRef = useRef(false);

  useEffect(() => {
    watchedSecondsRef.current = 0;
    lastMediaTimeRef.current = 0;
    lastWallTimeRef.current = 0;
    invalidPlaybackRef.current = false;
    completionRequestRef.current = false;
    warningShownRef.current = false;
    setVideoPointsAwarded(0);
  }, [concept, locked]);

  const markVideoComplete = useCallback(async () => {
    if (!concept || locked || completionRequestRef.current) {
      return;
    }
    completionRequestRef.current = true;
    try {
      await contentAPI.trackCourseOpen(`learning-path:${concept.id}`, concept.level, concept.title, 'learning_path_tutorial');
    } catch {
      void 0;
    }
    try {
      const response = await contentAPI.completeVideo(concept.id, concept.level);
      if (response.awarded) {
        setVideoPointsAwarded(response.points_awarded || 0);
        try {
          const raw = localStorage.getItem('user');
          if (raw) {
            const user = JSON.parse(raw) as Record<string, unknown>;
            user.total_points = response.current_points;
            localStorage.setItem('user', JSON.stringify(user));
          }
        } catch {
          void 0;
        }
        toast({
          title: "Skill points earned",
          description: `+${response.points_awarded} points for watching this video.`,
        });
      }
    } catch {
      completionRequestRef.current = false;
    }
  }, [concept, locked]);

  const handleVideoPlay = useCallback(() => {
    lastWallTimeRef.current = performance.now() / 1000;
    lastMediaTimeRef.current = videoRef.current?.currentTime || 0;
  }, []);

  const handleVideoRateChange = useCallback(() => {
    const video = videoRef.current;
    if (!video) {
      return;
    }
    if (Math.abs(video.playbackRate - 1) > 0.01) {
      invalidPlaybackRef.current = true;
      if (!warningShownRef.current) {
        warningShownRef.current = true;
        toast({
          title: "Normal playback required",
          description: "Watch at 1x speed without skipping to mark this video as completed.",
          variant: "destructive",
        });
      }
    }
  }, []);

  const handleVideoSeeking = useCallback(() => {
    const video = videoRef.current;
    if (!video) {
      return;
    }
    const forwardJump = video.currentTime - lastMediaTimeRef.current;
    if (forwardJump > 0.25) {
      invalidPlaybackRef.current = true;
      if (!warningShownRef.current) {
        warningShownRef.current = true;
        toast({
          title: "Skipping detected",
          description: "Please watch the full video continuously to complete it.",
          variant: "destructive",
        });
      }
    }
    lastMediaTimeRef.current = video.currentTime;
    lastWallTimeRef.current = performance.now() / 1000;
  }, []);

  const handleVideoTimeUpdate = useCallback(() => {
    const video = videoRef.current;
    if (!video || video.paused || video.ended) {
      return;
    }
    const now = performance.now() / 1000;
    const currentMedia = video.currentTime;
    const prevMedia = lastMediaTimeRef.current;
    const prevWall = lastWallTimeRef.current;
    if (prevWall > 0) {
      const mediaDelta = currentMedia - prevMedia;
      const wallDelta = now - prevWall;
      if (mediaDelta > 0) {
        if (mediaDelta > wallDelta * 1.25 + 0.2) {
          invalidPlaybackRef.current = true;
        } else {
          watchedSecondsRef.current += Math.min(mediaDelta, wallDelta + 0.2);
        }
      }
    }
    lastMediaTimeRef.current = currentMedia;
    lastWallTimeRef.current = now;
  }, []);

  const handleVideoEnded = useCallback(async () => {
    const video = videoRef.current;
    if (!video || !concept || locked) {
      return;
    }
    const duration = Number.isFinite(video.duration) && video.duration > 0 ? video.duration : 0;
    const watchedEnough = duration > 0 ? watchedSecondsRef.current >= duration * 0.98 : false;
    const validPlayback = !invalidPlaybackRef.current && Math.abs(video.playbackRate - 1) <= 0.01;
    if (!watchedEnough || !validPlayback) {
      toast({
        title: "Video not marked as completed",
        description: "Watch the full video at 1x without skipping to complete it.",
        variant: "destructive",
      });
      return;
    }
    await markVideoComplete();
  }, [concept, locked, markVideoComplete]);

  return (
    <AppLayout>
      <div className="p-4">
        <div className="max-w-6xl mx-auto space-y-5">
          <div className="flex items-center justify-between">
            {concept ? (
              <div className="flex items-center gap-2 -mt-1">
                <HoverCard>
                  <HoverCardTrigger asChild>
                    <h1 className="text-2xl font-bold cursor-default">
                      {concept.title}
                    </h1>
                  </HoverCardTrigger>
                  <HoverCardContent className="w-96">
                    <div className="grid gap-3">
                      <p className="text-sm text-muted-foreground">
                        {concept.description}
                      </p>
                      <ul className="grid gap-2 text-sm text-muted-foreground">
                        {concept.subtopics.map((topic) => (
                          <li key={topic} className="flex items-start gap-2">
                            <span className="mt-2 h-1.5 w-1.5 rounded-full bg-primary/60" />
                            <span>{topic}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </HoverCardContent>
                </HoverCard>
                <Badge variant="outline" className="capitalize">{concept.level}</Badge>
                <Badge variant="secondary">Earnable +{earnablePoints} pts</Badge>
                {videoPointsAwarded > 0 ? <Badge className="bg-emerald-600">+{videoPointsAwarded} earned</Badge> : null}
              </div>
            ) : (
              <div className="space-y-1">
                <h1 className="text-2xl font-bold -mt-1">Java Learning Path</h1>
                <p className="text-muted-foreground">Watch the tutorial and practice along.</p>
              </div>
            )}
            <Link to="/practice">
              <Button variant="outline" className="gap-2">
                <ArrowLeft className="w-4 h-4" />
                Back to Learning Paths
              </Button>
            </Link>
          </div>

          {!concept ? (
            <Card className="border-muted">
              <CardContent className="p-12 text-center">
                <h3 className="text-lg font-medium mb-2">Tutorial not found</h3>
                <p className="text-muted-foreground">Select a concept from the learning path list.</p>
              </CardContent>
            </Card>
          ) : locked ? (
            <Card className="border-muted">
              <CardContent className="p-12 text-center">
                <div className="flex items-center justify-center gap-2 text-muted-foreground mb-3">
                  <Lock className="w-5 h-5" />
                  <span>Locked concept</span>
                </div>
                <h3 className="text-lg font-medium mb-2">{concept.title}</h3>
                <p className="text-muted-foreground">
                  Upgrade your level to unlock this tutorial.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid items-stretch gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)] lg:gap-10">
              {concept.tutorialUrl ? (
                <div className="aspect-[16/9] w-full max-w-3xl mx-auto overflow-hidden rounded-xl border border-border/60 bg-black">
                  <video
                    ref={videoRef}
                    className="h-full w-full"
                    controls
                    preload="metadata"
                    playsInline
                    src={concept.tutorialUrl}
                    onPlay={handleVideoPlay}
                    onRateChange={handleVideoRateChange}
                    onSeeking={handleVideoSeeking}
                    onTimeUpdate={handleVideoTimeUpdate}
                    onEnded={handleVideoEnded}
                  >
                    Your browser does not support the video tag.
                  </video>
                </div>
              ) : (
                <div
                  className="aspect-[16/9] w-full max-w-3xl mx-auto overflow-hidden rounded-xl border border-dashed border-border/60 bg-muted/20 flex items-center justify-center text-sm text-muted-foreground"
                >
                  Video player will appear here
                </div>
              )}
              <Card className="border-border/20 bg-gradient-card">
                <CardContent className="p-6 h-full flex flex-col space-y-4">
                  <h3 className="text-xl font-semibold">What is covered</h3>
                  <div className="max-h-80 overflow-auto pr-1">
                    <ul className="grid gap-3 text-base lg:text-lg text-foreground">
                    {concept.subtopics.map((topic) => (
                      <li key={topic} className="flex items-start gap-2">
                        <span className="mt-3 h-2 w-2 rounded-full bg-primary/70" />
                        <span>{topic}</span>
                      </li>
                    ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
};

export default LearningPathTutorial;
