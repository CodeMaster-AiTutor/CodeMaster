import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Trophy, Circle, AlertCircle, BookOpen, Search, CheckCircle2, Target, Play, ExternalLink, ArrowRight } from 'lucide-react';
import AppLayout from '@/components/layout/AppLayout';
import { practiceAPI } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface Problem {
  id: number;
  title: string;
  difficulty: 'Basic' | 'Medium' | 'Advanced';
  status: 'not-started' | 'attempted' | 'solved';
  tags: string[];
  description?: string;
  tutorialUrl?: string;
}

interface LearningPath {
  id: string;
  title: string;
  description: string;
  modules: number;
  completed: number;
  topics: string[];
}

const Practice = () => {
  const [activeTab, setActiveTab] = useState('learning-paths');
  const [searchTerm, setSearchTerm] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [problems, setProblems] = useState<Problem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
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
  
  const handleStartProblem = (problem: Problem) => {
    console.log('Starting problem:', problem.id);
    // Navigate to compiler with problem
  };

  const learningPathsProblems: Problem[] = [];
  const learningPaths: LearningPath[] = [];

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
              {/* Learning Paths Problems List */}
              <div className="space-y-4">
                {learningPathsProblems.length === 0 ? (
                  <Card className="border-muted">
                    <CardContent className="p-12 text-center">
                      <BookOpen className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                      <h3 className="text-lg font-medium mb-2">No learning paths yet</h3>
                      <p className="text-muted-foreground">
                        Learning paths will appear once they are available for your level.
                      </p>
                    </CardContent>
                  </Card>
                ) : (
                  learningPathsProblems.map((problem) => (
                    <Card key={problem.id} className="border-border/20 bg-gradient-card hover:border-primary/30 transition-colors">
                      <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3 mb-2">
                              <h3 className="text-lg font-semibold">{problem.title}</h3>
                              <Badge variant="outline">{problem.difficulty}</Badge>
                            </div>
                            {problem.description ? (
                              <p className="text-muted-foreground mb-3">{problem.description}</p>
                            ) : null}
                            {problem.tutorialUrl && (
                              <a
                                href={problem.tutorialUrl}
                                className="text-primary hover:underline text-sm inline-flex items-center gap-1"
                                onClick={(e) => {
                                  e.preventDefault();
                                }}
                              >
                                Watch tutorial <ExternalLink className="w-3 h-3" />
                              </a>
                            )}
                          </div>
                          <Button
                            className="bg-primary hover:bg-primary/90 text-primary-foreground rounded-full w-10 h-10 p-0"
                            onClick={() => handleStartProblem(problem)}
                          >
                            <ArrowRight className="w-5 h-5" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>

              {/* Learning Paths/Courses Section */}
              <div className="mt-8">
                <h2 className="text-xl font-bold mb-4">Featured Courses</h2>
                <div className="grid gap-6">
                  {learningPaths.length === 0 ? (
                    <Card className="border-muted">
                      <CardContent className="p-12 text-center">
                        <BookOpen className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                        <h3 className="text-lg font-medium mb-2">No featured courses yet</h3>
                        <p className="text-muted-foreground">
                          Courses will show up here once they are connected.
                        </p>
                      </CardContent>
                    </Card>
                  ) : (
                    learningPaths.map((path) => (
                      <Card key={path.id} className="border-border/20 bg-gradient-card">
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <CardTitle className="text-xl mb-2">{path.title}</CardTitle>
                              <p className="text-muted-foreground text-sm mb-4">{path.description}</p>
                              <div className="flex items-center space-x-4 mb-4">
                                <div className="text-sm text-muted-foreground">
                                  {path.completed} / {path.modules} modules completed
                                </div>
                                <Trophy className="w-4 h-4 text-primary" />
                              </div>
                              <Progress value={(path.completed / path.modules) * 100} className="h-2 mb-4" />
                              <div className="flex flex-wrap gap-2">
                                {path.topics.slice(0, 4).map((topic, idx) => (
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
