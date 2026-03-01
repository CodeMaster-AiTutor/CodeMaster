import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import AppLayout from '@/components/layout/AppLayout';
import { Button } from '@/components/ui/button';
import { ArrowLeft, BookOpen, Maximize2, Minimize2 } from 'lucide-react';

const TheoryCourse = () => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const toggleFullscreen = useCallback(async () => {
    const element = containerRef.current;
    if (!document.fullscreenElement && element?.requestFullscreen) {
      await element.requestFullscreen();
      return;
    }
    if (document.fullscreenElement && document.exitFullscreen) {
      await document.exitFullscreen();
    }
  }, []);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(Boolean(document.fullscreenElement));
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  return (
    <AppLayout>
      <div className="min-h-screen bg-background">
        <div className="px-4 py-4">
          <div className="max-w-7xl mx-auto space-y-4">
            <div
              ref={containerRef}
              className={`${isFullscreen ? 'h-full w-full' : ''} rounded-xl border border-border/30 overflow-hidden bg-background`}
            >
              <div className={`${isFullscreen ? 'h-full flex flex-col' : ''} p-4`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <BookOpen className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <div className="text-lg font-semibold">Java Theory Course</div>
                      <div className="text-sm text-muted-foreground">Beginner to advanced concepts</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" asChild className="gap-2">
                      <Link to="/practice">
                        <ArrowLeft className="w-4 h-4" />
                        Back to Practice Arena
                      </Link>
                    </Button>
                    <Button variant="outline" className="gap-2" onClick={toggleFullscreen}>
                      {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                      {isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
                    </Button>
                  </div>
                </div>
                <div className={`${isFullscreen ? 'flex-1 mt-4' : 'mt-4'}`}>
                  <iframe
                    title="Java Theory Course"
                    src="/theory-course/hello-world.html"
                    className={`${isFullscreen ? 'h-full' : 'h-[80vh]'} w-full`}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
};

export default TheoryCourse;
