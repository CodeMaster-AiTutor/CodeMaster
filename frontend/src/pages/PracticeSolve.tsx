import React, { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import TopNavigation from '@/components/layout/TopNavigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowLeft, BookOpen, CheckCircle2, Loader2, XCircle } from 'lucide-react';
import Compiler from './Compiler';
import { practiceAPI } from '@/lib/api';

const getCachedProblemDescription = (title: string, level: string) => {
  try {
    const raw = localStorage.getItem('practice_catalog_cache');
    if (!raw) return '';
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return '';
    const found = parsed.find(
      (item: { level?: string; title?: string; description?: string }) =>
        (item.level || '').toLowerCase() === level.toLowerCase() &&
        (item.title || '').trim().toLowerCase() === title.trim().toLowerCase()
    );
    return found?.description || '';
  } catch {
    return '';
  }
};

const getCachedProblemCode = (cacheKey: string) => {
  try {
    return localStorage.getItem(cacheKey) || '';
  } catch {
    return '';
  }
};

type TestRunResult = {
  index: number;
  input: string;
  expected_output: string;
  actual_output: string;
  success: boolean;
  errors: string[];
};

const PracticeSolve = () => {
  const { level, title } = useParams<{ level?: string; title?: string }>();
  const decodedTitle = title ? decodeURIComponent(title) : 'Practice Problem';
  const normalizedLevel = (level || '').toLowerCase();
  const levelKey =
    normalizedLevel === 'advanced'
      ? 'advanced'
      : normalizedLevel === 'intermediate'
        ? 'intermediate'
        : 'basic';
  const levelLabel =
    levelKey === 'advanced'
      ? 'Advanced'
      : levelKey === 'intermediate'
        ? 'Intermediate'
        : 'Beginner';
  const catalogLevel = levelKey === 'basic' ? 'beginner' : levelKey;
  const storageLevelKey = catalogLevel;
  const solveKey = `practice:solved:${storageLevelKey}:${decodedTitle}`;
  const touchedKey = `practice:touched:${storageLevelKey}:${decodedTitle}`;
  const codeScopeKey = `practice:code:${storageLevelKey}:${decodedTitle}`;
  const codeCacheKey = `practice:code-cache:${storageLevelKey}:${decodedTitle}`;
  const [problemDescription, setProblemDescription] = useState<string>(() =>
    getCachedProblemDescription(decodedTitle, catalogLevel)
  );
  const [problemId, setProblemId] = useState<number | null>(null);
  const [initialEditorCode, setInitialEditorCode] = useState<string>(() => getCachedProblemCode(codeCacheKey));
  const [hasUserEdited, setHasUserEdited] = useState<boolean>(false);
  const [currentCode, setCurrentCode] = useState<string>('');
  const [isRunningTests, setIsRunningTests] = useState<boolean>(false);
  const [testResults, setTestResults] = useState<TestRunResult[]>([]);
  const [testSummary, setTestSummary] = useState<{ solved: boolean; passed: number; total: number } | null>(null);
  const [testError, setTestError] = useState<string>('');
  const [earnablePoints, setEarnablePoints] = useState<number>(catalogLevel === 'advanced' ? 15 : catalogLevel === 'intermediate' ? 10 : 5);
  const [pointsEarnedAlready, setPointsEarnedAlready] = useState<boolean>(false);
  const [lastPointsAwarded, setLastPointsAwarded] = useState<number>(0);

  useEffect(() => {
    let active = true;
    const cached = getCachedProblemDescription(decodedTitle, catalogLevel);
    if (cached) {
      setProblemDescription(cached);
    }
    const loadDescription = async () => {
      try {
        const catalog = await practiceAPI.getCatalog();
        if (!active) return;
        try {
          localStorage.setItem('practice_catalog_cache', JSON.stringify(catalog));
        } catch {
          void 0;
        }
        const found = catalog.find(
          (item) =>
            item.level === catalogLevel &&
            item.title.trim().toLowerCase() === decodedTitle.trim().toLowerCase()
        );
        setProblemDescription(found?.description || '');
        setProblemId(found?.id ?? null);
        setEarnablePoints(found?.earnable_points ?? (catalogLevel === 'advanced' ? 15 : catalogLevel === 'intermediate' ? 10 : 5));
        setPointsEarnedAlready(Boolean(found?.points_earned));
      } catch {
        setProblemDescription(cached || '');
        setProblemId(null);
      }
    };
    loadDescription();
    return () => {
      active = false;
    };
  }, [catalogLevel, decodedTitle]);

  useEffect(() => {
    setInitialEditorCode(getCachedProblemCode(codeCacheKey));
    if (!problemId) {
      setHasUserEdited(false);
      return;
    }
    setHasUserEdited(false);
    let active = true;
    const loadDraft = async () => {
      try {
        const draft = await practiceAPI.getDraft(problemId);
        if (!active) {
          return;
        }
        const hasDraft = Boolean(draft?.has_draft);
        const nextCode = hasDraft ? (draft.code || '') : '';
        const localCachedCode = getCachedProblemCode(codeCacheKey);
        if (!localCachedCode) {
          setInitialEditorCode(nextCode);
        }
        if (nextCode) {
          try {
            localStorage.setItem(codeCacheKey, nextCode);
          } catch {
            void 0;
          }
        }
        if (hasDraft || nextCode.trim().length > 0) {
          try {
            localStorage.setItem(touchedKey, 'true');
          } catch {
            void 0;
          }
        }
      } catch {
        if (active) {
          setInitialEditorCode(getCachedProblemCode(codeCacheKey));
        }
      }
    };
    loadDraft();
    return () => {
      active = false;
    };
  }, [problemId, touchedKey, codeCacheKey]);

  useEffect(() => {
    if (!problemId || !hasUserEdited) {
      return;
    }
    const handle = window.setTimeout(async () => {
      try {
        await practiceAPI.saveDraft(problemId, currentCode);
        try {
          localStorage.setItem(codeCacheKey, currentCode);
        } catch {
          void 0;
        }
        if (currentCode.trim().length > 0) {
          try {
            localStorage.setItem(touchedKey, 'true');
          } catch {
            void 0;
          }
        }
      } catch {
        void 0;
      }
    }, 1200);
    return () => {
      window.clearTimeout(handle);
    };
  }, [problemId, currentCode, touchedKey, hasUserEdited, codeCacheKey]);

  const handleCodeChange = (value: string) => {
    setCurrentCode(value);
    setHasUserEdited(true);
    try {
      localStorage.setItem(codeCacheKey, value);
    } catch {
      void 0;
    }
    if (value.trim().length > 0) {
      try {
        localStorage.setItem(touchedKey, 'true');
      } catch {
        void 0;
      }
    }
  };
  const displayDescription = useMemo(
    () => {
      const normalizedTitle = decodedTitle.trim().toLowerCase();
      const lines = problemDescription.replace(/\t/g, '    ').split('\n');
      const firstLine = (lines[0] || '').trim().toLowerCase();
      const withoutTitle = firstLine === normalizedTitle ? lines.slice(1) : lines;
      const trimmed = withoutTitle.map((line) => line.trim());
      const testSectionIndex = trimmed.findIndex(
        (line) => line.toLowerCase() === 'test cases' || line.toLowerCase() === 'test scenarios'
      );
      const visibleLines =
        testSectionIndex >= 0 ? withoutTitle.slice(0, testSectionIndex) : withoutTitle;
      return visibleLines.join('\n').trimEnd();
    },
    [problemDescription, decodedTitle]
  );
  const hasDescription = displayDescription.trim().length > 0;
  const handleExecutionSuccess = () => {
    void 0;
  };

  const handleRunTestCases = async () => {
    setTestError('');
    setTestResults([]);
    setTestSummary(null);
    if (!problemId) {
      setTestError('Problem mapping not found.');
      return;
    }
    if (!currentCode.trim()) {
      setTestError('Please write code before running test cases.');
      return;
    }
    setIsRunningTests(true);
    try {
      const result = await practiceAPI.validateSolution(problemId, currentCode);
      setTestResults(result.results || []);
      setTestSummary({ solved: result.solved, passed: result.passed, total: result.total });
      setLastPointsAwarded(result.points_awarded || 0);
      if ((result.points_awarded || 0) > 0) {
        setPointsEarnedAlready(true);
      }
      if (typeof result.current_points === 'number') {
        try {
          const raw = localStorage.getItem('user');
          if (raw) {
            const user = JSON.parse(raw) as Record<string, unknown>;
            user.total_points = result.current_points;
            localStorage.setItem('user', JSON.stringify(user));
          }
        } catch {
          void 0;
        }
      }
      try {
        await practiceAPI.saveDraft(problemId, currentCode);
      } catch {
        void 0;
      }
      try {
        localStorage.setItem(codeCacheKey, currentCode);
      } catch {
        void 0;
      }
      try {
        localStorage.setItem(touchedKey, 'true');
      } catch {
        void 0;
      }
      if (result.solved) {
        localStorage.setItem(solveKey, 'true');
      } else {
        localStorage.removeItem(solveKey);
      }
    } catch (error) {
      setTestError(error instanceof Error ? error.message : 'Failed to run test cases.');
    } finally {
      setIsRunningTests(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <TopNavigation onMenuClick={() => void 0} />
      <div className="px-4 py-4 pt-24">
        <div className="max-w-7xl mx-auto space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <BookOpen className="w-5 h-5 text-primary" />
              </div>
              <div>
                <div className="text-2xl md:text-3xl font-semibold text-foreground">{decodedTitle}</div>
                <div className="text-sm text-muted-foreground">{levelLabel} Practice</div>
                <div className="text-xs text-primary mt-1">
                  Earnable skill points: +{earnablePoints} {pointsEarnedAlready ? '(already earned)' : ''}
                </div>
                {lastPointsAwarded > 0 ? (
                  <div className="text-xs text-emerald-400 mt-1">Last run reward: +{lastPointsAwarded} points</div>
                ) : null}
              </div>
            </div>
            <Button variant="outline" asChild className="gap-2">
              <Link to="/practice?tab=practice-arena">
                <ArrowLeft className="w-4 h-4" />
                Back to Practice Arena
              </Link>
            </Button>
          </div>

          <div className="flex flex-col lg:flex-row gap-4">
            <div className="w-full lg:w-[30%]">
              <Card className="border-border/20 bg-gradient-card">
                <CardContent className="p-6 space-y-4">
                  <div className="text-sm text-foreground/90 whitespace-pre-wrap leading-6">
                    {hasDescription ? displayDescription : 'Description unavailable'}
                  </div>
                  <div className="pt-2 space-y-3">
                    <Button
                      className="w-full"
                      onClick={handleRunTestCases}
                      disabled={isRunningTests || !problemId}
                    >
                      {isRunningTests ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Running test cases
                        </>
                      ) : (
                        'Run Test Cases'
                      )}
                    </Button>
                    {testError ? (
                      <div className="text-xs text-red-300">{testError}</div>
                    ) : null}
                    {testSummary ? (
                      <div className={`text-xs ${testSummary.solved ? 'text-green-300' : 'text-amber-300'}`}>
                        {testSummary.solved
                          ? `All test cases passed (${testSummary.passed}/${testSummary.total}). Problem marked complete.`
                          : `Passed ${testSummary.passed}/${testSummary.total} test cases.`}
                      </div>
                    ) : null}
                    {testResults.length > 0 ? (
                      <div className="space-y-2">
                        {testResults.map((test) => (
                          <div
                            key={`test-${test.index}`}
                            className="rounded-md border border-border/40 bg-background/40 p-2 text-xs"
                          >
                            <div className="flex items-center gap-2 mb-1">
                              {test.success ? (
                                <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
                              ) : (
                                <XCircle className="w-3.5 h-3.5 text-red-400" />
                              )}
                              <span>Test Case {test.index}</span>
                            </div>
                            <div className="text-foreground/90">Expected: {test.expected_output || '(empty)'}</div>
                            <div className="text-foreground/90">Actual: {test.actual_output || '(empty)'}</div>
                          </div>
                        ))}
                      </div>
                    ) : null}
                  </div>
                </CardContent>
              </Card>
            </div>
            <div className="w-full lg:w-[70%]">
              <Compiler
                key={codeScopeKey}
                withLayout={false}
                onExecutionSuccess={handleExecutionSuccess}
                onCodeChange={handleCodeChange}
                persistenceScope={codeScopeKey}
                initialCode={initialEditorCode}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PracticeSolve;
