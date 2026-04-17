import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Code2, 
  Brain, 
  Zap, 
  Trophy,
  BookOpen,
  Target,
  TrendingUp,
  Play,
  Clock,
  CheckCircle,
  Lock,
  ArrowRight,
  Flame,
  Users,
  BarChart3
} from 'lucide-react';
import { Link } from 'react-router-dom';
import AppLayout from '@/components/layout/AppLayout';
import { dashboardAPI } from '@/lib/api';
import { toast } from '@/hooks/use-toast';

type DashboardStatsResponse = {
  current_level?: string;
  streak?: number;
  successful_compilations?: number;
  total_submissions?: number;
  weekly_goal?: number;
  weekly_progress?: number;
  monthly_goal?: number;
  monthly_progress?: number;
  total_points?: number;
  problems_solved?: number;
  user?: {
    skill_level?: string;
    total_points?: number;
  };
  stats?: {
    streak?: number;
    successful_submissions?: number;
    problems_solved?: number;
    total_submissions?: number;
    weekly_goal?: number;
    weekly_progress?: number;
    monthly_goal?: number;
    monthly_progress?: number;
  };
  achievements?: Array<{
    key: string;
    name: string;
    description: string;
    earned: boolean;
    locked?: boolean;
    level?: 'beginner' | 'intermediate' | 'advanced';
    reward_points?: number;
    progress?: { completed: number; total: number };
  }>;
  trending_challenges?: Array<{
    id: number;
    title: string;
    level: 'beginner' | 'intermediate' | 'advanced';
    difficulty: string;
    participants: number;
    attempts: number;
    path?: string;
  }>;
};

type ActivityItem = {
  type?: string;
  title?: string;
  status?: string;
  timestamp?: string;
  time?: string;
  points?: number;
};

const Dashboard = () => {
  const [userStats, setUserStats] = useState({
    level: 'beginner',
    streak: 0,
    problemsSolved: 0,
    totalProblems: 0,
    weeklyGoal: 10,
    weeklyProgress: 0,
    monthlyGoal: 15,
    monthlyProgress: 0,
    skillPoints: 0,
    nextLevelPoints: 1000
  });
  
  const [recentActivity, setRecentActivity] = useState<Array<{
    type: string;
    title: string;
    status: string;
    time: string;
    points: number;
  }>>([]);
  const [achievements, setAchievements] = useState<Array<{ name: string; description: string; earned: boolean; locked: boolean; level: string; rewardPoints: number }>>([]);
  const [upcomingChallenges, setUpcomingChallenges] = useState<Array<{ title: string; difficulty: string; estimatedTime: string; participants: number; path: string }>>([]);
  
  useEffect(() => {
    let isMounted = true;
    const fetchDashboardData = async () => {
      const [statsResult, activityResult] = await Promise.allSettled([
        dashboardAPI.getStats(),
        dashboardAPI.getRecentActivity(7)
      ]);

      if (isMounted && statsResult.status === 'fulfilled') {
        const statsResponse = statsResult.value as DashboardStatsResponse;
        const nestedStats = statsResponse.stats || {};
        const nestedUser = statsResponse.user || {};
        setUserStats({
          level: statsResponse.current_level || nestedUser.skill_level || 'beginner',
          streak: statsResponse.streak ?? nestedStats.streak ?? 0,
          problemsSolved: statsResponse.problems_solved ?? nestedStats.problems_solved ?? statsResponse.successful_compilations ?? nestedStats.successful_submissions ?? 0,
          totalProblems: statsResponse.total_submissions ?? nestedStats.total_submissions ?? 0,
          weeklyGoal: statsResponse.weekly_goal ?? nestedStats.weekly_goal ?? 10,
          weeklyProgress: statsResponse.weekly_progress ?? nestedStats.weekly_progress ?? 0,
          monthlyGoal: statsResponse.monthly_goal ?? nestedStats.monthly_goal ?? 15,
          monthlyProgress: statsResponse.monthly_progress ?? nestedStats.monthly_progress ?? 0,
          skillPoints: statsResponse.total_points ?? nestedUser.total_points ?? 0,
          nextLevelPoints: 1000
        });
        const incomingAchievements = Array.isArray(statsResponse.achievements) ? statsResponse.achievements : [];
        setAchievements(incomingAchievements.map((item) => ({
          name: item.name,
          description: item.progress
            ? `${item.description} (${item.progress.completed}/${item.progress.total})`
            : item.description,
          earned: Boolean(item.earned),
          locked: Boolean(item.locked),
          level: item.level || 'beginner',
          rewardPoints: Number(item.reward_points || 0),
        })));
        const incomingChallenges = Array.isArray(statsResponse.trending_challenges) ? statsResponse.trending_challenges : [];
        setUpcomingChallenges(incomingChallenges.map((item) => ({
          title: item.title,
          difficulty: item.difficulty || 'Easy',
          estimatedTime: item.difficulty === 'Hard' ? '25 min' : item.difficulty === 'Medium' ? '18 min' : '12 min',
          participants: Number(item.participants || 0),
          path: `/practice/solve/${item.level}/${encodeURIComponent(item.title)}`,
        })));
      }

      if (isMounted && activityResult.status === 'fulfilled') {
        const activityResponseRaw = activityResult.value as { activities?: ActivityItem[] } | ActivityItem[];
        const activityResponse = Array.isArray(activityResponseRaw)
          ? activityResponseRaw
          : (activityResponseRaw?.activities || []);
        const formattedActivity = activityResponse.map((activity) => ({
          type: activity.type || 'challenge',
          title: activity.title || 'Activity',
          status: activity.status || 'completed',
          time: activity.timestamp || activity.time ? formatTimeAgo(activity.timestamp || activity.time) : 'Unknown',
          points: activity.points || 0
        }));
        setRecentActivity(formattedActivity.slice(0, 7));
      }

      if (isMounted && statsResult.status === 'rejected' && activityResult.status === 'rejected') {
        const error = statsResult.reason;
        const message = error instanceof Error ? error.message : '';
        if (message.toLowerCase().includes('authentication required')) {
          return;
        }
        toast({
          title: "Failed to load dashboard",
          description: message || 'Please try again later.',
          variant: "destructive"
        });
      }
    };

    void fetchDashboardData();
    const interval = window.setInterval(() => {
      void fetchDashboardData();
    }, 15000);
    return () => {
      isMounted = false;
      window.clearInterval(interval);
    };
  }, []);

  const formatTimeAgo = (timestamp: string): string => {
    const now = new Date();
    const time = new Date(timestamp);
    if (Number.isNaN(time.getTime())) {
      return 'Unknown';
    }
    const diffInSeconds = Math.floor((now.getTime() - time.getTime()) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    return `${Math.floor(diffInSeconds / 86400)} days ago`;
  };

  const quickActions = [
    {
      title: 'Code Compiler',
      description: 'Write and test code instantly',
      icon: Code2,
      color: 'bg-primary',
      path: '/compiler'
    },
    {
      title: 'AI Explainer',
      description: 'Get code explanations',
      icon: Brain,
      color: 'bg-accent',
      path: '/explainer'
    },
    {
      title: 'Code Generator',
      description: 'Generate code with AI',
      icon: Zap,
      color: 'bg-warning',
      path: '/generator'
    },
    {
      title: 'Practice Arena',
      description: 'Solve coding challenges',
      icon: Target,
      color: 'bg-success',
      path: '/practice'
    }
  ];

  const visibleRecentActivity = recentActivity.slice(0, 7);
  const visibleAchievements = achievements;

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto space-y-8">
            {/* Welcome Header */}
            <div className="fade-in">
              <h1 className="text-3xl font-bold mb-2">Welcome back!</h1>
              <p className="text-muted-foreground">Ready to continue your coding journey?</p>
            </div>
            
            <>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 slide-up">
              <Card className="card-feature !p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="w-9 h-9 bg-primary/10 rounded-lg flex items-center justify-center">
                    <Trophy className="w-5 h-5 text-primary" />
                  </div>
                  <Badge variant="secondary" className="capitalize">{userStats.level}</Badge>
                </div>
                <div className="space-y-1">
                  <h3 className="text-xl font-bold">{userStats.skillPoints}</h3>
                  <p className="text-sm text-muted-foreground">Skill Points</p>
                  <Progress value={(userStats.skillPoints / userStats.nextLevelPoints) * 100} className="h-2" />
                </div>
              </Card>

              <Card className="card-feature !p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="w-9 h-9 bg-orange-500/10 rounded-lg flex items-center justify-center">
                    <Flame className="w-5 h-5 text-orange-500" />
                  </div>
                  <div className="text-xl font-bold text-orange-500">{userStats.streak}</div>
                </div>
                <h3 className="font-semibold mb-1">Day Streak</h3>
                <p className="text-sm text-muted-foreground">Keep it going!</p>
              </Card>

              <Card className="card-feature !p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="w-9 h-9 bg-success/10 rounded-lg flex items-center justify-center">
                    <CheckCircle className="w-5 h-5 text-success" />
                  </div>
                  <TrendingUp className="w-4 h-4 text-success" />
                </div>
                <h3 className="text-xl font-bold">{userStats.problemsSolved}</h3>
                <p className="text-sm text-muted-foreground">Problems Solved</p>
              </Card>

              <Card className="card-feature !p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="w-9 h-9 bg-info/10 rounded-lg flex items-center justify-center">
                    <Target className="w-5 h-5 text-info" />
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-medium text-muted-foreground">Weekly Goal</div>
                    <div className="text-sm font-semibold">{userStats.weeklyProgress}/{userStats.weeklyGoal}</div>
                  </div>
                </div>
                <Progress value={(userStats.weeklyProgress / userStats.weeklyGoal) * 100} className="h-2" />
                <div className="flex items-center justify-between mt-2">
                  <div className="w-9 h-9 bg-info/10 rounded-lg flex items-center justify-center">
                    <Target className="w-5 h-5 text-info" />
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-muted-foreground">Monthly Goal</div>
                    <div className="text-base font-semibold">{userStats.monthlyProgress}/{userStats.monthlyGoal}</div>
                  </div>
                </div>
              </Card>
            </div>

            {/* Quick Actions */}
            <div className="space-y-6">
              <h2 className="text-2xl font-bold">Quick Actions</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {quickActions.map((action, index) => (
                  <Link key={index} to={action.path}>
                    <Card className="card-feature group cursor-pointer h-full">
                      <div className={`w-12 h-12 ${action.color} rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                        <action.icon className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="font-semibold mb-2">{action.title}</h3>
                      <p className="text-sm text-muted-foreground mb-4">{action.description}</p>
                      <div className="flex items-center text-primary text-sm font-medium">
                        Get Started <ArrowRight className="w-4 h-4 ml-1" />
                      </div>
                    </Card>
                  </Link>
                ))}
              </div>
            </div>

            <div className="grid lg:grid-cols-2 gap-8">
              <div className="space-y-6">
                <h2 className="text-2xl font-bold">Recent Activity</h2>
                <Card className="card-feature">
                  <div className="space-y-4 max-h-[16rem] overflow-y-hidden hover:overflow-y-auto pr-1">
                    {recentActivity.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
                        <p className="font-medium">No recent activity</p>
                        <p className="text-sm mt-1">Start coding to see your activity here!</p>
                      </div>
                    ) : (
                        visibleRecentActivity.map((activity, index) => (
                        <div key={`top-${index}`} className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                          <div className="flex items-center space-x-3">
                            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                              activity.type === 'practice_problem' ? 'bg-success/10' :
                              activity.type === 'assessment' ? 'bg-info/10' :
                              activity.type === 'video' ? 'bg-warning/10' :
                              activity.type === 'course' ? 'bg-primary/10' :
                              activity.type === 'generation' ? 'bg-warning/10' : 'bg-muted'
                            }`}>
                              {activity.type === 'practice_problem' && <Target className="w-5 h-5 text-success" />}
                              {activity.type === 'assessment' && <Brain className="w-5 h-5 text-info" />}
                              {activity.type === 'video' && <Play className="w-5 h-5 text-warning" />}
                              {activity.type === 'course' && <BookOpen className="w-5 h-5 text-primary" />}
                              {activity.type === 'generation' && <Zap className="w-5 h-5 text-warning" />}
                            </div>
                            <div>
                              <h4 className="font-medium">{activity.title}</h4>
                              <p className="text-sm text-muted-foreground flex items-center">
                                <Clock className="w-3 h-3 mr-1" />
                                {activity.time}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <Badge variant={activity.status === 'solved' || activity.status === 'taken' || activity.status === 'watched' || activity.status === 'opened' ? 'default' : 'secondary'}>
                              {activity.status}
                            </Badge>
                            {activity.points > 0 && (
                              <p className="text-sm text-success mt-1">+{activity.points} pts</p>
                            )}
                          </div>
                        </div>
                        ))
                    )}
                  </div>
                </Card>
              </div>

              <div className="space-y-6">
                <h2 className="text-2xl font-bold">Achievements</h2>
                <Card className="card-feature">
                  <div
                    className="space-y-4 max-h-[17rem] overflow-y-auto pr-1"
                  >
                    {achievements.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        <Trophy className="w-12 h-12 mx-auto mb-3 opacity-50" />
                        <p className="font-medium">No achievements yet</p>
                        <p className="text-sm mt-1">Complete challenges to earn achievements.</p>
                      </div>
                    ) : (
                      visibleAchievements.map((achievement, index) => (
                        <div key={index} className={`flex items-center space-x-3 p-4 rounded-lg ${
                          achievement.locked ? 'bg-muted/40' : achievement.earned ? 'bg-success/10' : 'bg-muted/50'
                        }`}>
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                            achievement.locked ? 'bg-muted text-muted-foreground' : achievement.earned ? 'bg-success text-white' : 'bg-muted'
                          }`}>
                            {achievement.locked ? <Lock className="w-5 h-5" /> : <Trophy className="w-5 h-5" />}
                          </div>
                          <div className="flex-1">
                            <h4 className={`font-medium ${achievement.locked ? 'text-muted-foreground' : achievement.earned ? 'text-success' : 'text-muted-foreground'}`}>
                              {achievement.name}
                            </h4>
                            <p className="text-sm text-muted-foreground">{achievement.description} (+{achievement.rewardPoints} pts)</p>
                          </div>
                          {achievement.locked ? <Badge variant="secondary">Locked</Badge> : achievement.earned ? <CheckCircle className="w-5 h-5 text-success" /> : null}
                        </div>
                      ))
                    )}
                  </div>
                </Card>
              </div>
            </div>

            {/* Upcoming Challenges */}
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold">Trending Challenges</h2>
                <Link to="/practice">
                  <Button variant="outline">View All</Button>
                </Link>
              </div>
              <div className="grid md:grid-cols-3 gap-6">
                {upcomingChallenges.length === 0 ? (
                  <Card className="card-feature md:col-span-3">
                    <div className="text-center py-10 text-muted-foreground">
                      <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p className="font-medium">No trending challenges yet</p>
                      <p className="text-sm mt-1">Check back once new challenges are available.</p>
                    </div>
                  </Card>
                ) : (
                  upcomingChallenges.map((challenge, index) => (
                    <Card key={index} className="card-feature">
                      <div className="space-y-4">
                        <div className="flex items-start justify-between">
                          <h3 className="font-semibold">{challenge.title}</h3>
                          <Badge
                            variant={challenge.difficulty === 'Hard' ? 'destructive' : 'secondary'}
                            className={
                              challenge.difficulty === 'Easy'
                                ? 'bg-green-600 text-white hover:bg-green-600'
                                : challenge.difficulty === 'Medium'
                                  ? 'bg-yellow-500 text-black hover:bg-yellow-500'
                                  : undefined
                            }
                          >
                            {challenge.difficulty}
                          </Badge>
                        </div>
                        <div className="space-y-2 text-sm text-muted-foreground">
                          <div className="flex items-center">
                            <Clock className="w-4 h-4 mr-2" />
                            {challenge.estimatedTime}
                          </div>
                          <div className="flex items-center">
                            <Users className="w-4 h-4 mr-2" />
                            {challenge.participants} participants
                          </div>
                        </div>
                        <Button className="w-full btn-primary text-white" asChild>
                          <Link to={challenge.path}>
                            <Play className="w-4 h-4 mr-2" />
                            Go to Challenge
                          </Link>
                        </Button>
                      </div>
                    </Card>
                  ))
                )}
              </div>
            </div>
            </>
          </div>
        </AppLayout>
  );
};

export default Dashboard;
