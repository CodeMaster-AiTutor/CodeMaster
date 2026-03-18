import React, { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import TopNavigation from '@/components/layout/TopNavigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowLeft, BookOpen } from 'lucide-react';
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
  const solveKey = `practice:solved:${levelKey}:${decodedTitle}`;
  const catalogLevel = levelKey === 'basic' ? 'beginner' : levelKey;
  const [problemDescription, setProblemDescription] = useState<string>(() =>
    getCachedProblemDescription(decodedTitle, catalogLevel)
  );

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
      } catch {
        setProblemDescription(cached || '');
      }
    };
    loadDescription();
    return () => {
      active = false;
    };
  }, [catalogLevel, decodedTitle]);
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
    try {
      localStorage.setItem(solveKey, 'true');
    } catch {
      void 0;
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
                <div className="text-2xl md:text-3xl font-semibold text-white">{decodedTitle}</div>
                <div className="text-sm text-muted-foreground">{levelLabel} Practice</div>
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
                  <div className="text-sm text-zinc-100/90 whitespace-pre-wrap leading-6">
                    {hasDescription ? displayDescription : 'Description unavailable'}
                  </div>
                </CardContent>
              </Card>
            </div>
            <div className="w-full lg:w-[70%]">
              <Compiler withLayout={false} onExecutionSuccess={handleExecutionSuccess} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PracticeSolve;
