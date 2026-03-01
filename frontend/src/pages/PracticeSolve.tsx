import React from 'react';
import { Link, useParams } from 'react-router-dom';
import TopNavigation from '@/components/layout/TopNavigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowLeft, BookOpen } from 'lucide-react';
import Compiler from './Compiler';

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
      <div className="px-4 py-4">
        <div className="max-w-7xl mx-auto space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <BookOpen className="w-5 h-5 text-primary" />
              </div>
              <div>
                <div className="text-lg font-semibold">{decodedTitle}</div>
                <div className="text-sm text-muted-foreground">{levelLabel} Practice</div>
              </div>
            </div>
            <Button variant="outline" asChild className="gap-2">
              <Link to="/practice">
                <ArrowLeft className="w-4 h-4" />
                Back to Practice Arena
              </Link>
            </Button>
          </div>

          <div className="flex flex-col lg:flex-row gap-4">
            <div className="w-full lg:w-[30%]">
              <Card className="border-border/20 bg-gradient-card">
                <CardContent className="p-6 space-y-4">
                  <div className="text-base font-semibold">Problem Description</div>
                  <div className="text-sm text-muted-foreground">
                    Solve {decodedTitle} by designing a clear approach, handling edge cases, and
                    validating inputs and outputs. Provide a clean, readable Java solution and
                    explain any key steps.
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
