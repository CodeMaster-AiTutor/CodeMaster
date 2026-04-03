import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import Compiler from '@/pages/Compiler';
import { 
  Trophy, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Brain, 
  Target,
  ArrowLeft,
  ArrowRight,
  RotateCcw,
  Award,
  Zap,
  Loader2
} from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import { assessmentAPI } from '@/lib/api';

interface Question {
  id: number;
  type: 'mcq' | 'msq' | 'coding';
  question: string;
  options?: string[] | null;
  test_cases?: Array<{ input: string; output: string; match_type?: string }> | null;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
}

interface ActiveAssessmentSnapshot {
  assessmentId: number;
  level: 'beginner' | 'intermediate' | 'advanced';
  currentQuestionIndex: number;
  answers: Record<number, string | string[]>;
  assessmentEndAt: number;
  isAssessmentActive: boolean;
  assessmentPhase?: 'rules' | 'active';
  tabSwitchCount?: number;
  fullscreenExitCount?: number;
}

const STORAGE_KEY = 'assessment_active_state_v1';

const readStoredSnapshot = (): ActiveAssessmentSnapshot | null => {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as ActiveAssessmentSnapshot;
    if (!parsed?.isAssessmentActive || !parsed.assessmentId || !parsed.assessmentEndAt) return null;
    if (parsed.assessmentEndAt <= Date.now()) return null;
    return parsed;
  } catch {
    return null;
  }
};

const Assessment = () => {
  const initialSnapshotRef = useRef<ActiveAssessmentSnapshot | null>(readStoredSnapshot());
  const initialSnapshot = initialSnapshotRef.current;
  const [currentLevel, setCurrentLevel] = useState<'beginner' | 'intermediate' | 'advanced'>(initialSnapshot?.level || 'beginner');
  const [isAssessmentActive, setIsAssessmentActive] = useState(Boolean(initialSnapshot?.isAssessmentActive));
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(initialSnapshot?.currentQuestionIndex || 0);
  const [answers, setAnswers] = useState<Record<number, string | string[]>>(initialSnapshot?.answers || {});
  const [timeLeft, setTimeLeft] = useState(initialSnapshot ? Math.max(0, Math.floor((initialSnapshot.assessmentEndAt - Date.now()) / 1000)) : 1800);
  const [isCompleted, setIsCompleted] = useState(false);
  const [score, setScore] = useState(0);
  const [showResults, setShowResults] = useState(false);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [assessmentId, setAssessmentId] = useState<number | null>(initialSnapshot?.assessmentId || null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [canAdvanceLevel, setCanAdvanceLevel] = useState(false);
  const [proposedNextLevel, setProposedNextLevel] = useState<'intermediate' | 'advanced' | null>(null);
  const [isAcceptingLevelUp, setIsAcceptingLevelUp] = useState(false);
  const [assessmentEndAt, setAssessmentEndAt] = useState<number | null>(initialSnapshot?.assessmentEndAt || null);
  const [isRestoringActiveAssessment, setIsRestoringActiveAssessment] = useState(Boolean(initialSnapshot?.isAssessmentActive));
  const [tabSwitchCount, setTabSwitchCount] = useState(initialSnapshot?.tabSwitchCount || 0);
  const [isRulesScreenVisible, setIsRulesScreenVisible] = useState(false);
  const [fullscreenExitDeadline, setFullscreenExitDeadline] = useState<number | null>(null);
  const [fullscreenExitCount, setFullscreenExitCount] = useState(initialSnapshot?.fullscreenExitCount || 0);
  const fullscreenGraceTimeoutRef = useRef<number | null>(null);
  const fullscreenExitDeadlineRef = useRef<number | null>(null);
  const lastFocusViolationAtRef = useRef<number>(0);
  const fullscreenExitCountRef = useRef<number>(initialSnapshot?.fullscreenExitCount || 0);
  const codingInitialCodeRef = useRef<Record<number, string>>({});
  const codingDraftsRef = useRef<Record<number, string>>({});
  const navigatorRef = useRef<HTMLDivElement | null>(null);
  const hoverCloseTimerRef = useRef<number | null>(null);
  const [activeNavigator, setActiveNavigator] = useState<'mcq' | 'msq' | 'coding' | null>(null);
  const [hoverNavigator, setHoverNavigator] = useState<'mcq' | 'msq' | 'coding' | null>(null);
  const [fullscreenCountdownSeconds, setFullscreenCountdownSeconds] = useState(0);
  const [codingTestState, setCodingTestState] = useState<Record<number, {
    isRunning: boolean;
    data?: {
      all_passed: boolean;
      passed: number;
      total: number;
      results: Array<{
        index: number;
        input: string;
        expected_output: string;
        actual_output: string;
        match_type: string;
        success: boolean;
      }>;
    };
    error?: string;
  }>>({});

  // Get current question
  const currentQuestion = questions[currentQuestionIndex];
  const currentCodingQuestionId = currentQuestion?.type === 'coding' ? currentQuestion.id : null;
  const questionIndicesByType = useMemo(() => {
    const grouped: Record<'mcq' | 'msq' | 'coding', number[]> = { mcq: [], msq: [], coding: [] };
    questions.forEach((question, index) => {
      if (question.type === 'mcq' || question.type === 'msq' || question.type === 'coding') {
        grouped[question.type].push(index);
      }
    });
    return grouped;
  }, [questions]);
  const isQuestionAnswered = useCallback((question: Question): boolean => {
    const answer = answers[question.id];
    if (question.type === 'mcq') {
      return typeof answer === 'string' && answer.trim().length > 0;
    }
    if (question.type === 'msq') {
      return Array.isArray(answer) && answer.length > 0;
    }
    const draft = codingDraftsRef.current[question.id];
    if (typeof draft === 'string') {
      return draft.trim().length > 0;
    }
    return typeof answer === 'string' && answer.trim().length > 0;
  }, [answers]);
  const visibleNavigator = activeNavigator || hoverNavigator;
  const getStableCodingInitialCode = (questionId: number) => {
    if (!(questionId in codingInitialCodeRef.current)) {
      const draft = codingDraftsRef.current[questionId];
      const existing = answers[questionId];
      codingInitialCodeRef.current[questionId] = typeof draft === 'string'
        ? draft
        : (typeof existing === 'string' ? existing : '');
    }
    return codingInitialCodeRef.current[questionId];
  };
  const handleCurrentCodingCodeChange = useCallback((nextCode: string) => {
    if (currentCodingQuestionId == null) return;
    codingDraftsRef.current[currentCodingQuestionId] = nextCode;
  }, [currentCodingQuestionId]);

  useEffect(() => {
    codingInitialCodeRef.current = {};
  }, [currentQuestionIndex]);

  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (!navigatorRef.current) return;
      if (!navigatorRef.current.contains(event.target as Node)) {
        setActiveNavigator(null);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      if (hoverCloseTimerRef.current) {
        window.clearTimeout(hoverCloseTimerRef.current);
        hoverCloseTimerRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    fullscreenExitCountRef.current = fullscreenExitCount;
  }, [fullscreenExitCount]);

  useEffect(() => {
    fullscreenExitDeadlineRef.current = fullscreenExitDeadline;
  }, [fullscreenExitDeadline]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem('user');
      if (!raw) return;
      const user = JSON.parse(raw) as { skill_level?: string };
      const level = (user.skill_level || '').toLowerCase();
      if (level === 'beginner' || level === 'intermediate' || level === 'advanced') {
        setCurrentLevel(level);
      }
    } catch {
      void 0;
    }
  }, []);

  useEffect(() => {
    const restore = async () => {
      const snapshot = initialSnapshotRef.current;
      if (!snapshot?.isAssessmentActive) {
        setIsRestoringActiveAssessment(false);
        return;
      }
      try {
        const questionsResponse = await assessmentAPI.getQuestions(snapshot.level, snapshot.assessmentId);
        setQuestions(questionsResponse.questions);
        setCurrentQuestionIndex((prev) => Math.max(0, Math.min(prev, Math.max(questionsResponse.questions.length - 1, 0))));
        setIsRulesScreenVisible(snapshot.assessmentPhase === 'rules');
        setIsAssessmentActive(snapshot.assessmentPhase !== 'rules');
      } catch {
        localStorage.removeItem(STORAGE_KEY);
        setIsAssessmentActive(false);
        setAssessmentId(null);
      } finally {
        setIsRestoringActiveAssessment(false);
      }
    };
    void restore();
  }, []);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const startAssessment = async () => {
    setIsLoading(true);
    try {
      // Start assessment and get questions
      const startResponse = await assessmentAPI.startAssessment(currentLevel);
      const questionsResponse = await assessmentAPI.getQuestions(currentLevel, startResponse.assessment_id);

      setAssessmentId(startResponse.assessment_id);
      setQuestions(questionsResponse.questions);
      setIsAssessmentActive(false);
      setIsRulesScreenVisible(true);
      setCurrentQuestionIndex(0);
      setAnswers({});
      setTimeLeft(1800);
      setIsCompleted(false);
      setShowResults(false);
      setScore(0);
      setCanAdvanceLevel(false);
      setProposedNextLevel(null);
      setCodingTestState({});
      setAssessmentEndAt(null);
      setTabSwitchCount(0);
      setFullscreenExitCount(0);
      setFullscreenExitDeadline(null);
      setFullscreenCountdownSeconds(0);
      codingInitialCodeRef.current = {};
      
      toast({
        title: "Assessment started!",
        description: `Good luck with your ${currentLevel} level assessment!`,
      });
    } catch (error) {
      console.error('Failed to start assessment:', error);
      toast({
        title: "Failed to start assessment",
        description: error instanceof Error ? error.message : 'Please try again later.',
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnswerChange = (value: string) => {
    setAnswers(prev => ({
      ...prev,
      [currentQuestion.id]: value
    }));
  };

  const handleMsqChange = (option: string, checked: boolean) => {
    setAnswers((prev) => {
      const current = Array.isArray(prev[currentQuestion.id]) ? [...(prev[currentQuestion.id] as string[])] : [];
      const next = checked ? Array.from(new Set([...current, option])) : current.filter((item) => item !== option);
      return { ...prev, [currentQuestion.id]: next };
    });
  };

  const runCodingTests = async () => {
    if (!currentQuestion || currentQuestion.type !== 'coding') return;
    const answerCode = typeof answers[currentQuestion.id] === 'string' ? (answers[currentQuestion.id] as string) : '';
    const code = codingDraftsRef.current[currentQuestion.id] ?? answerCode;
    if (!code.trim()) {
      toast({
        title: 'Code required',
        description: 'Please write code before running testcases.',
        variant: 'destructive',
      });
      return;
    }
    setCodingTestState((prev) => ({
      ...prev,
      [currentQuestion.id]: { isRunning: true, data: prev[currentQuestion.id]?.data },
    }));
    try {
      const result = await assessmentAPI.runCodingTestcases(currentQuestion.id, code);
      setCodingTestState((prev) => ({
        ...prev,
        [currentQuestion.id]: { isRunning: false, data: result },
      }));
    } catch (error) {
      setCodingTestState((prev) => ({
        ...prev,
        [currentQuestion.id]: {
          isRunning: false,
          data: prev[currentQuestion.id]?.data,
          error: error instanceof Error ? error.message : 'Failed to run testcases'
        },
      }));
    }
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      handleCompleteAssessment();
    }
  };

  const previousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const backToAssessmentHome = useCallback(() => {
    setIsAssessmentActive(false);
    setIsRulesScreenVisible(false);
    setCurrentQuestionIndex(0);
    setAssessmentId(null);
    setQuestions([]);
    setAnswers({});
    setTimeLeft(1800);
    setCodingTestState({});
    setAssessmentEndAt(null);
    setTabSwitchCount(0);
    setFullscreenExitCount(0);
    setFullscreenExitDeadline(null);
    setFullscreenCountdownSeconds(0);
    codingInitialCodeRef.current = {};
    codingDraftsRef.current = {};
    localStorage.removeItem(STORAGE_KEY);
    if (fullscreenGraceTimeoutRef.current) {
      window.clearTimeout(fullscreenGraceTimeoutRef.current);
      fullscreenGraceTimeoutRef.current = null;
    }
    if (document.fullscreenElement) {
      void document.exitFullscreen();
    }
  }, []);

  const proceedToAssessment = () => {
    setIsRulesScreenVisible(false);
    setIsAssessmentActive(true);
    const endAt = Date.now() + (1800 * 1000);
    setAssessmentEndAt(endAt);
    setTimeLeft(1800);
  };

  const handleCompleteAssessment = useCallback(async () => {
    if (!assessmentId) {
      toast({
        title: "Error",
        description: "Assessment ID not found. Please start a new assessment.",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const mergedAnswers: Record<number, string | string[]> = { ...answers };
      Object.entries(codingDraftsRef.current).forEach(([questionId, code]) => {
        const id = Number(questionId);
        if (Number.isFinite(id)) {
          mergedAnswers[id] = code;
        }
      });
      const response = await assessmentAPI.submitAssessment({
        assessment_id: assessmentId,
        answers: mergedAnswers,
        level: currentLevel,
      });

      setIsCompleted(true);
      setIsAssessmentActive(false);
      setIsRulesScreenVisible(false);
      setScore(response.score);
      setShowResults(true);
      setCanAdvanceLevel(Boolean(response.can_advance));
      setProposedNextLevel(response.proposed_next_level ?? null);
      setAssessmentEndAt(null);
      setTabSwitchCount(0);
      setFullscreenExitCount(0);
      setFullscreenExitDeadline(null);
      setFullscreenCountdownSeconds(0);
      codingInitialCodeRef.current = {};
      codingDraftsRef.current = {};
      codingDraftsRef.current = {};
      localStorage.removeItem(STORAGE_KEY);
      if (fullscreenGraceTimeoutRef.current) {
        window.clearTimeout(fullscreenGraceTimeoutRef.current);
        fullscreenGraceTimeoutRef.current = null;
      }
      if (document.fullscreenElement) {
        void document.exitFullscreen();
      }

      // Check if user passed (80% or higher)
      if (response.passed) {
        toast({
          title: "Congratulations! 🎉",
          description: `You passed with ${response.score}%.`,
        });
      } else {
        toast({
          title: "Keep practicing! 📚",
          description: `You scored ${response.score}%. You need 80% to advance to the next level.`,
        });
      }
    } catch (error) {
      console.error('Failed to submit assessment:', error);
      toast({
        title: "Failed to submit assessment",
        description: error instanceof Error ? error.message : 'Please try again later.',
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  }, [assessmentId, answers, currentLevel]);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isAssessmentActive && assessmentEndAt && !isCompleted) {
      const tick = () => {
        const remaining = Math.max(0, Math.floor((assessmentEndAt - Date.now()) / 1000));
        setTimeLeft(remaining);
      };
      tick();
      timer = setInterval(tick, 1000) as unknown as NodeJS.Timeout;
    } else if (timeLeft === 0 && !isCompleted && isAssessmentActive) {
      handleCompleteAssessment();
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isAssessmentActive, assessmentEndAt, timeLeft, isCompleted, handleCompleteAssessment]);

  useEffect(() => {
    if ((!isAssessmentActive && !isRulesScreenVisible) || !assessmentId) return;
    const snapshot = {
      assessmentId,
      level: currentLevel,
      currentQuestionIndex,
      answers,
      assessmentEndAt: assessmentEndAt || (Date.now() + (timeLeft * 1000)),
      isAssessmentActive: isAssessmentActive || isRulesScreenVisible,
      assessmentPhase: isRulesScreenVisible ? 'rules' : 'active',
      tabSwitchCount,
      fullscreenExitCount,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
  }, [isAssessmentActive, isRulesScreenVisible, assessmentId, assessmentEndAt, timeLeft, currentLevel, currentQuestionIndex, answers, tabSwitchCount, fullscreenExitCount]);

  useEffect(() => {
    if (!fullscreenExitDeadline) {
      setFullscreenCountdownSeconds(0);
      return;
    }
    const tick = () => {
      const secs = Math.max(0, Math.ceil((fullscreenExitDeadline - Date.now()) / 1000));
      setFullscreenCountdownSeconds(secs);
    };
    tick();
    const timer = window.setInterval(tick, 250);
    return () => window.clearInterval(timer);
  }, [fullscreenExitDeadline]);

  useEffect(() => {
    if (!isAssessmentActive) return;
    const isFullscreenLike = () => {
      if (document.fullscreenElement) return true;
      const widthMatch = window.innerWidth >= (window.screen.width - 2);
      const heightMatch = window.innerHeight >= (window.screen.height - 2);
      return widthMatch && heightMatch;
    };
    const clearFullscreenDeadline = () => {
      setFullscreenExitDeadline(null);
      fullscreenExitDeadlineRef.current = null;
      setFullscreenCountdownSeconds(0);
      if (fullscreenGraceTimeoutRef.current) {
        window.clearTimeout(fullscreenGraceTimeoutRef.current);
        fullscreenGraceTimeoutRef.current = null;
      }
    };
    const triggerFullscreenViolation = () => {
      if (fullscreenExitDeadlineRef.current) return;
      const nextCount = fullscreenExitCountRef.current + 1;
      if (nextCount > 2) {
        setFullscreenExitCount(0);
        fullscreenExitCountRef.current = 0;
        backToAssessmentHome();
        toast({
          title: 'Assessment terminated',
          description: 'Fullscreen exited too many times. Assessment ended.',
          variant: 'destructive',
        });
        return;
      }
      setFullscreenExitCount(nextCount);
      fullscreenExitCountRef.current = nextCount;
      toast({
        title: 'Fullscreen required',
        description: `Return to fullscreen within 8 seconds. Use F11. Violation ${nextCount}/2.`,
        variant: 'destructive',
      });
      const deadline = Date.now() + 8000;
      setFullscreenExitDeadline(deadline);
      fullscreenExitDeadlineRef.current = deadline;
      if (fullscreenGraceTimeoutRef.current) {
        window.clearTimeout(fullscreenGraceTimeoutRef.current);
      }
      fullscreenGraceTimeoutRef.current = window.setTimeout(() => {
        if (!isFullscreenLike()) {
          backToAssessmentHome();
          toast({
            title: 'Assessment terminated',
            description: 'Fullscreen rule violated.',
            variant: 'destructive',
          });
        }
      }, 8000);
    };
    const requestFull = async () => {
      if (!isFullscreenLike()) {
        try {
          await document.documentElement.requestFullscreen();
        } catch {
          void 0;
        }
      }
    };
    void requestFull();
    const onFullscreenChange = () => {
      if (!isAssessmentActive) return;
      if (isFullscreenLike()) {
        clearFullscreenDeadline();
        return;
      }
      triggerFullscreenViolation();
    };
    const onResize = () => {
      if (isFullscreenLike()) {
        clearFullscreenDeadline();
      } else {
        triggerFullscreenViolation();
      }
    };
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = '';
    };
    const registerFocusViolation = () => {
      const now = Date.now();
      if (now - lastFocusViolationAtRef.current < 800) return;
      lastFocusViolationAtRef.current = now;
      setTabSwitchCount((prev) => {
        const next = prev + 1;
        if (next > 2) {
          backToAssessmentHome();
          toast({
            title: 'Assessment terminated',
            description: 'Tab/window switched too many times. Assessment ended.',
            variant: 'destructive',
          });
          return 0;
        }
        return next;
      });
      toast({
        title: 'Exam mode active',
        description: 'Do not switch tabs or windows during assessment.',
        variant: 'destructive',
      });
    };

    const onVisibilityChange = () => {
      if (document.visibilityState !== 'visible') {
        registerFocusViolation();
      } else {
        void requestFull();
      }
    };
    const onBlur = () => {
      registerFocusViolation();
    };
    const onKeyDown = (event: KeyboardEvent) => {
      const blocked = event.key === 'F5'
        || ((event.ctrlKey || event.metaKey) && ['r', 'w', 't', 'l'].includes(event.key.toLowerCase()));
      if (blocked) {
        event.preventDefault();
      }
    };
    history.pushState(null, '', window.location.href);
    const onPopState = () => {
      history.pushState(null, '', window.location.href);
      toast({
        title: 'Exam mode active',
        description: 'Navigation is disabled during assessment.',
        variant: 'destructive',
      });
    };
    document.addEventListener('fullscreenchange', onFullscreenChange);
    window.addEventListener('beforeunload', onBeforeUnload);
    document.addEventListener('visibilitychange', onVisibilityChange);
    window.addEventListener('blur', onBlur);
    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('popstate', onPopState);
    window.addEventListener('resize', onResize);
    return () => {
      document.removeEventListener('fullscreenchange', onFullscreenChange);
      window.removeEventListener('beforeunload', onBeforeUnload);
      document.removeEventListener('visibilitychange', onVisibilityChange);
      window.removeEventListener('blur', onBlur);
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('popstate', onPopState);
      window.removeEventListener('resize', onResize);
      if (fullscreenGraceTimeoutRef.current) {
        window.clearTimeout(fullscreenGraceTimeoutRef.current);
        fullscreenGraceTimeoutRef.current = null;
      }
    };
  }, [isAssessmentActive, backToAssessmentHome]);

  const retakeAssessment = () => {
    setShowResults(false);
    setIsCompleted(false);
    setCanAdvanceLevel(false);
    setProposedNextLevel(null);
    startAssessment();
  };

  const advanceLevel = async () => {
    if (!assessmentId || !canAdvanceLevel || !proposedNextLevel) {
      return;
    }
    setIsAcceptingLevelUp(true);
    try {
      const response = await assessmentAPI.acceptLevelUp(assessmentId);
      const nextLevel = response.new_skill_level;
      setCurrentLevel(nextLevel);
      setCanAdvanceLevel(false);
      setProposedNextLevel(null);
      try {
        const raw = localStorage.getItem('user');
        if (raw) {
          const user = JSON.parse(raw) as Record<string, unknown>;
          user.skill_level = nextLevel;
          localStorage.setItem('user', JSON.stringify(user));
        }
      } catch {
        void 0;
      }
      toast({
        title: "Level Up! 🚀",
        description: `Welcome to ${nextLevel === 'intermediate' ? 'Intermediate' : 'Advanced'} level!`,
      });
      setShowResults(false);
      setIsCompleted(false);
    } catch (error) {
      toast({
        title: "Unable to update level",
        description: error instanceof Error ? error.message : 'Please try again later.',
        variant: 'destructive',
      });
    } finally {
      setIsAcceptingLevelUp(false);
    }
  };

  if (isRestoringActiveAssessment) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-background/95 flex items-center justify-center">
        <div className="text-center space-y-2">
          <Loader2 className="w-8 h-8 animate-spin mx-auto" />
          <div className="text-sm text-muted-foreground">Restoring assessment...</div>
        </div>
      </div>
    );
  }

  if (showResults) {
    return (
      <AppLayout>
        <div className="p-4">
          <div className="max-w-4xl mx-auto space-y-4">
            <div className="text-center">
              <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                Assessment Results
              </h1>
            </div>

            <Card className="border-border/20 bg-gradient-card">
              <CardContent className="p-8 text-center">
                <div className="mb-6">
                  {score >= 80 ? (
                    <Trophy className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
                  ) : (
                    <Target className="w-16 h-16 text-blue-500 mx-auto mb-4" />
                  )}
                  <h2 className="text-2xl font-bold mb-2">
                    {score >= 80 ? 'Congratulations!' : 'Keep Practicing!'}
                  </h2>
                  <p className="text-4xl font-bold text-primary mb-2">{score}%</p>
                  <p className="text-muted-foreground">
                    You answered {Math.round((score / 100) * questions.length)} out of {questions.length} questions correctly
                  </p>
                </div>

                <div className="space-y-4">
                  {canAdvanceLevel && proposedNextLevel && (
                    <Button onClick={advanceLevel} className="bg-gradient-primary" disabled={isAcceptingLevelUp}>
                      <Award className="w-4 h-4 mr-2" />
                      {isAcceptingLevelUp ? 'Updating...' : `Advance to ${proposedNextLevel === 'intermediate' ? 'Intermediate' : 'Advanced'} Level`}
                    </Button>
                  )}
                  
                  {score >= 80 && !canAdvanceLevel && currentLevel === 'advanced' && (
                    <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                      <p className="text-yellow-600 font-medium">
                        🏆 Congratulations! You've mastered all levels!
                      </p>
                    </div>
                  )}

                  <div className="flex gap-4 justify-center">
                    <Button variant="outline" onClick={retakeAssessment}>
                      <RotateCcw className="w-4 h-4 mr-2" />
                      Retake Assessment
                    </Button>
                    <Button variant="outline" onClick={() => setShowResults(false)}>
                      Back to Overview
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </AppLayout>
    );
  }

  if (isRulesScreenVisible) {
    const remainingFullscreenGrace = fullscreenExitDeadline ? Math.max(0, Math.ceil((fullscreenExitDeadline - Date.now()) / 1000)) : 0;
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-background/95 p-4 md:p-6">
        <div className="max-w-4xl mx-auto space-y-4">
          <Card className="border-border/20 bg-gradient-card">
            <CardHeader>
              <CardTitle>Assessment Format</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div><span className="font-medium">MCQ:</span> 10 questions, choose exactly one correct option in each question.</div>
              <div><span className="font-medium">MCQ Weightage:</span> 2 marks each (total 20 marks).</div>
              <div><span className="font-medium">MSQ:</span> 10 questions, one or more options can be correct. Select all correct options to score.</div>
              <div><span className="font-medium">MSQ Weightage:</span> 8 questions carry 3 marks each and 2 questions carry 4 marks each (total 32 marks).</div>
              <div><span className="font-medium">Coding:</span> 5 questions, solve in compiler and run testcase execution for verification.</div>
              <div><span className="font-medium">Coding Weightage:</span> 16 marks per question, but only best 3 correct coding answers are counted (max 48 marks).</div>
              <div><span className="font-medium">Total:</span> 25 questions in 30 minutes.</div>
              <div><span className="font-medium">Passing Criteria:</span> Minimum 80% score.</div>
            </CardContent>
          </Card>
          <Card className="border-border/20 bg-gradient-card">
            <CardHeader>
              <CardTitle>Assessment Rules</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div>Stay in fullscreen for the entire assessment.</div>
              <div>Do not switch tabs or windows.</div>
              <div>Do not use refresh/navigation keys.</div>
              <div>More than 2 tab/window switches will auto-terminate the assessment.</div>
              <div>More than 2 fullscreen exits will auto-terminate the assessment.</div>
              <div>If fullscreen is exited, return within 8 seconds or the assessment will auto-close. Press F11 to restore fullscreen quickly.</div>
              {remainingFullscreenGrace > 0 ? (
                <div className="text-destructive">Return to fullscreen in {remainingFullscreenGrace}s</div>
              ) : null}
            </CardContent>
          </Card>
          <div className="flex gap-3">
            <Button variant="outline" onClick={backToAssessmentHome}>
              Exit Assessment
            </Button>
            <Button className="bg-gradient-primary" onClick={proceedToAssessment}>
              Proceed to Assessment
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (isAssessmentActive) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-background/95 p-4 md:p-6">
          <div className="max-w-[1700px] mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold">
                  {currentLevel.charAt(0).toUpperCase() + currentLevel.slice(1)} Assessment
                </h1>
                  <p className="text-muted-foreground">
                    Question {currentQuestionIndex + 1} of {questions.length}
                  </p>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4" />
                  <span className="font-mono">{formatTime(timeLeft)}</span>
                </div>
                <Badge variant="outline">
                  {questions.length > 0 ? Math.round(((currentQuestionIndex + 1) / questions.length) * 100) : 0}% Complete
                </Badge>
              </div>
            </div>
            <div className="flex items-center justify-end">
              <div
                ref={navigatorRef}
                className="relative flex items-center gap-2"
                onMouseEnter={() => {
                  if (hoverCloseTimerRef.current) {
                    window.clearTimeout(hoverCloseTimerRef.current);
                    hoverCloseTimerRef.current = null;
                  }
                }}
                onMouseLeave={() => {
                  if (!activeNavigator) {
                    if (hoverCloseTimerRef.current) {
                      window.clearTimeout(hoverCloseTimerRef.current);
                    }
                    hoverCloseTimerRef.current = window.setTimeout(() => {
                      setHoverNavigator(null);
                    }, 120);
                  }
                }}
              >
                <Button
                  type="button"
                  variant={visibleNavigator === 'mcq' ? 'default' : 'outline'}
                  size="sm"
                  onMouseEnter={() => {
                    if (hoverCloseTimerRef.current) {
                      window.clearTimeout(hoverCloseTimerRef.current);
                      hoverCloseTimerRef.current = null;
                    }
                    setHoverNavigator('mcq');
                  }}
                  onClick={() => setActiveNavigator((prev) => (prev === 'mcq' ? null : 'mcq'))}
                >
                  MCQ
                </Button>
                <Button
                  type="button"
                  variant={visibleNavigator === 'msq' ? 'default' : 'outline'}
                  size="sm"
                  onMouseEnter={() => {
                    if (hoverCloseTimerRef.current) {
                      window.clearTimeout(hoverCloseTimerRef.current);
                      hoverCloseTimerRef.current = null;
                    }
                    setHoverNavigator('msq');
                  }}
                  onClick={() => setActiveNavigator((prev) => (prev === 'msq' ? null : 'msq'))}
                >
                  MSQ
                </Button>
                <Button
                  type="button"
                  variant={visibleNavigator === 'coding' ? 'default' : 'outline'}
                  size="sm"
                  onMouseEnter={() => {
                    if (hoverCloseTimerRef.current) {
                      window.clearTimeout(hoverCloseTimerRef.current);
                      hoverCloseTimerRef.current = null;
                    }
                    setHoverNavigator('coding');
                  }}
                  onClick={() => setActiveNavigator((prev) => (prev === 'coding' ? null : 'coding'))}
                >
                  CP
                </Button>
                {visibleNavigator ? (
                  <div
                    className="absolute right-0 top-full mt-1 z-50 w-[320px] rounded-md border border-border/40 bg-card p-3 shadow-xl"
                    onMouseEnter={() => {
                      if (hoverCloseTimerRef.current) {
                        window.clearTimeout(hoverCloseTimerRef.current);
                        hoverCloseTimerRef.current = null;
                      }
                      if (!activeNavigator) {
                        setHoverNavigator(visibleNavigator);
                      }
                    }}
                    onMouseLeave={() => {
                      if (!activeNavigator) {
                        if (hoverCloseTimerRef.current) {
                          window.clearTimeout(hoverCloseTimerRef.current);
                        }
                        hoverCloseTimerRef.current = window.setTimeout(() => {
                          setHoverNavigator(null);
                        }, 120);
                      }
                    }}
                  >
                    <div className="mb-2 text-xs font-medium uppercase text-muted-foreground">
                      {visibleNavigator === 'coding' ? 'Coding Problems' : `${visibleNavigator.toUpperCase()} Questions`}
                    </div>
                    <div className="grid grid-cols-8 gap-2">
                      {questionIndicesByType[visibleNavigator].map((questionIndex) => {
                        const question = questions[questionIndex];
                        const answered = question ? isQuestionAnswered(question) : false;
                        const active = currentQuestionIndex === questionIndex;
                        return (
                          <button
                            key={`${visibleNavigator}-${questionIndex}`}
                            type="button"
                            onClick={() => {
                              setCurrentQuestionIndex(questionIndex);
                              if (activeNavigator) setActiveNavigator(activeNavigator);
                            }}
                            className={`h-8 rounded-md border text-xs font-medium transition ${
                              active
                                ? 'border-primary bg-primary text-primary-foreground'
                                : answered
                                  ? 'border-emerald-500/60 bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                                  : 'border-amber-500/50 bg-amber-500/10 text-amber-700 dark:text-amber-300'
                            }`}
                            title={answered ? 'Answered' : 'Not answered'}
                          >
                            {questionIndex + 1}
                          </button>
                        );
                      })}
                    </div>
                    <div className="mt-2 flex items-center gap-3 text-[11px] text-muted-foreground">
                      <span className="inline-flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />Answered</span>
                      <span className="inline-flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-full bg-amber-500" />Not answered</span>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
            {fullscreenExitDeadline && fullscreenCountdownSeconds > 0 ? (
              <div className="rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                Fullscreen required. Return within {fullscreenCountdownSeconds}s or assessment will close. Hint: press F11.
              </div>
            ) : null}
            <div>
              <Button variant="outline" onClick={backToAssessmentHome}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Skill Assessment
              </Button>
            </div>

            {/* Progress */}
            <Progress value={questions.length > 0 ? ((currentQuestionIndex + 1) / questions.length) * 100 : 0} />

            {/* Question */}
            {currentQuestion ? (
              <Card className="border-border/20 bg-gradient-card">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Brain className="w-5 h-5" />
                    <span>Question {currentQuestionIndex + 1}</span>
                    <Badge variant="secondary">{currentQuestion.type}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="text-lg whitespace-pre-wrap">
                    {currentQuestion.type === 'coding' ? '' : currentQuestion.question}
                  </div>

                  {currentQuestion.type === 'mcq' && currentQuestion.options && (
                    <RadioGroup
                      value={typeof answers[currentQuestion.id] === 'string' ? (answers[currentQuestion.id] as string) : ''}
                      onValueChange={handleAnswerChange}
                    >
                      {currentQuestion.options.map((option, index) => (
                        <div key={index} className="flex items-center space-x-2">
                          <RadioGroupItem value={option} id={`option-${index}`} />
                          <Label htmlFor={`option-${index}`} className="flex-1 cursor-pointer">
                            {option}
                          </Label>
                        </div>
                      ))}
                    </RadioGroup>
                  )}

                  {currentQuestion.type === 'msq' && currentQuestion.options && (
                    <div className="space-y-3">
                      {currentQuestion.options.map((option, index) => {
                        const selected = Array.isArray(answers[currentQuestion.id]) && (answers[currentQuestion.id] as string[]).includes(option);
                        return (
                          <div key={index} className="flex items-center space-x-2">
                            <Checkbox
                              id={`msq-${index}`}
                              checked={selected}
                              className="rounded-[3px]"
                              onCheckedChange={(checked) => handleMsqChange(option, Boolean(checked))}
                            />
                            <Label htmlFor={`msq-${index}`} className="flex-1 cursor-pointer">{option}</Label>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {currentQuestion.type === 'coding' && (
                    <div className="grid grid-cols-1 lg:grid-cols-10 gap-4">
                      <div className="space-y-4 lg:col-span-3">
                        <div className="rounded-md border border-border/30 bg-background/40 p-3 text-sm whitespace-pre-wrap">
                          {currentQuestion.question}
                        </div>
                        <div className="rounded-md border border-border/30 bg-background/30 p-3 space-y-2">
                          <div className="font-medium text-sm">Testcase Execution</div>
                          {currentQuestion.test_cases && currentQuestion.test_cases.length > 0 ? (
                            <div className="space-y-2 text-xs">
                              {currentQuestion.test_cases.map((test, idx) => (
                                <div key={idx} className="rounded border border-border/30 p-2">
                                  <div>Input: {test.input || '(empty)'}</div>
                                  <div>Expected: {test.output || '(compile only)'}</div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div className="text-xs text-muted-foreground">No testcases available</div>
                          )}
                          <Button
                            type="button"
                            size="sm"
                            onClick={runCodingTests}
                            disabled={codingTestState[currentQuestion.id]?.isRunning}
                          >
                            {codingTestState[currentQuestion.id]?.isRunning ? 'Running...' : 'Run Testcases'}
                          </Button>
                          {codingTestState[currentQuestion.id]?.error ? (
                            <div className="text-xs text-destructive">{codingTestState[currentQuestion.id]?.error}</div>
                          ) : null}
                          {codingTestState[currentQuestion.id]?.data ? (
                            <div className="space-y-2 text-xs">
                              <div className="font-medium">
                                Passed {codingTestState[currentQuestion.id]?.data?.passed} / {codingTestState[currentQuestion.id]?.data?.total}
                              </div>
                              {codingTestState[currentQuestion.id]?.data?.results.map((res) => (
                                <div key={res.index} className="rounded border border-border/30 p-2">
                                  <div>Case {res.index}: {res.success ? 'Passed' : 'Failed'}</div>
                                  <div>Actual: {res.actual_output || '(empty)'}</div>
                                </div>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      </div>
                      <div className="lg:col-span-7">
                        <Compiler
                          key={`assessment-coding-${currentQuestion.id}`}
                          withLayout={false}
                          persistenceScope={`assessment-${assessmentId || 'new'}-q-${currentQuestion.id}`}
                          initialCode={getStableCodingInitialCode(currentQuestion.id)}
                          onCodeChange={handleCurrentCodingCodeChange}
                        />
                      </div>
                    </div>
                  )}

                  {(currentQuestion.type !== 'coding' && (currentQuestion.type === 'mcq' || currentQuestion.type === 'msq') === false) && (
                    <Textarea
                      placeholder="Enter your answer here..."
                      value={typeof answers[currentQuestion.id] === 'string' ? (answers[currentQuestion.id] as string) : ''}
                      onChange={(e) => handleAnswerChange(e.target.value)}
                      className="min-h-[120px] font-mono"
                    />
                  )}

                  <div className="flex justify-between">
                    <Button
                      variant="outline"
                      onClick={previousQuestion}
                      disabled={currentQuestionIndex === 0}
                    >
                      Previous
                    </Button>
                    <Button
                      onClick={nextQuestion}
                      disabled={isSubmitting}
                      className="bg-gradient-primary"
                    >
                      {isSubmitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                      {currentQuestionIndex === questions.length - 1 ? 'Complete Assessment' : 'Next'}
                      {!isSubmitting && <ArrowRight className="w-4 h-4 ml-2" />}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="border-border/20 bg-gradient-card">
                <CardContent className="p-8 text-center">
                  <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
                  <p>Loading questions...</p>
                </CardContent>
              </Card>
            )}
          </div>
      </div>
    );
  }

  return (
    <AppLayout>
      <div className="p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          <div className="text-center">
            <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
              Skill Assessment
            </h1>
          </div>

          {/* Current Level */}
          <Card className="border-border/20 bg-gradient-card">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Target className="w-5 h-5" />
                <span>Current Level</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-2xl font-bold capitalize">{currentLevel}</h3>
                  <p className="text-muted-foreground">
                    {currentLevel === 'beginner' && 'Master the fundamentals of programming'}
                    {currentLevel === 'intermediate' && 'Dive deeper into algorithms and design patterns'}
                    {currentLevel === 'advanced' && 'Explore complex systems and optimization'}
                  </p>
                </div>
                <Badge variant="secondary" className="text-lg px-4 py-2">
                  {currentLevel === 'beginner' && '🌱'}
                  {currentLevel === 'intermediate' && '🚀'}
                  {currentLevel === 'advanced' && '⭐'}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Assessment Info */}
          <div className="grid md:grid-cols-1 gap-6">
            <Card className="border-border/20">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Brain className="w-5 h-5" />
                  <span>Assessment Details</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span>Questions:</span>
                  <span className="font-medium">25 questions</span>
                </div>
                <div className="flex justify-between">
                  <span>Time Limit:</span>
                  <span className="font-medium">30 minutes</span>
                </div>
                <div className="flex justify-between">
                  <span>Passing Score:</span>
                  <span className="font-medium">80%</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Start Assessment */}
          <Card className="border-border/20 bg-gradient-card">
            <CardContent className="p-8 text-center">
              <h3 className="text-xl font-bold mb-4">Ready to Test Your Skills?</h3>
              <Button 
                onClick={startAssessment} 
                size="lg" 
                className="bg-gradient-primary"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Loading Questions...
                  </>
                ) : (
                  <>
                    <Trophy className="w-5 h-5 mr-2" />
                    Start {currentLevel.charAt(0).toUpperCase() + currentLevel.slice(1)} Assessment
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  );
};

export default Assessment;
