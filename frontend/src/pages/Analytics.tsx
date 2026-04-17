import React, { useEffect, useState } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import {
  BarChart3,
  TrendingUp,
  Clock,
  Target,
  Code,
  Calendar,
  PlayCircle,
  Wallet,
  Info
} from 'lucide-react';
import { analyticsAPI, dashboardAPI } from '@/lib/api';
import { toast } from '@/hooks/use-toast';

type AnalyticsOverviewResponse = {
  total_submissions?: number;
  success_rate?: number;
  total_time_spent_seconds?: number;
  streak?: number;
  total_points?: number;
  problems_solved?: number;
  weekly_goal?: number;
  weekly_progress?: number;
  monthly_goal?: number;
  monthly_progress?: number;
};

type AnalyticsProgressResponse = {
  point_history?: Array<{
    id?: number;
    source?: string;
    points_delta?: number;
    time?: string;
  }>;
  point_sources?: Array<{
    event_type?: string;
    source?: string;
    earned_points?: number;
    used_points?: number;
    net_points?: number;
    events?: number;
  }>;
};

const Analytics = () => {
  const [stats, setStats] = useState({
    totalProblems: 0,
    solvedProblems: 0,
    successRate: 0,
    skillPoints: 0,
    totalTimeSeconds: 0,
    streak: 0,
    weeklyGoal: 5,
    weeklyProgress: 0,
    monthlyGoal: 15,
    monthlyProgress: 0
  });

  const [recentActivity, setRecentActivity] = useState<Array<{
    type: string;
    title: string;
    status: string;
    time: string;
    points: number;
  }>>([]);

  const [skillProgress, setSkillProgress] = useState<Array<{
    id: number;
    source: string;
    delta: number;
    time: string;
  }>>([]);

  useEffect(() => {
    let isMounted = true;
    const fetchAnalyticsData = async () => {
      try {
        const [overviewResponse, progressResponse, activityResponse] = await Promise.all([
          analyticsAPI.getOverview(),
          analyticsAPI.getProgress(),
          dashboardAPI.getRecentActivity(7)
        ]);
        if (!isMounted) {
          return;
        }

        const overview = overviewResponse as AnalyticsOverviewResponse;
        const progress = progressResponse as AnalyticsProgressResponse;

        // Update stats from API response
        setStats({
          totalProblems: overview.total_submissions || 0,
          solvedProblems: overview.problems_solved || 0,
          successRate: overview.success_rate || 0,
          skillPoints: overview.total_points || 0,
          totalTimeSeconds: Math.round(overview.total_time_spent_seconds || 0),
          streak: overview.streak || 0,
          weeklyGoal: overview.weekly_goal || 5,
          weeklyProgress: overview.weekly_progress || 0,
          monthlyGoal: overview.monthly_goal || 15,
          monthlyProgress: overview.monthly_progress || 0
        });

        const activityPayload = activityResponse as { activities?: Array<{ type?: string; title?: string; status?: string; time?: string; points?: number }> };
        const formattedActivity = Array.isArray(activityPayload.activities)
          ? activityPayload.activities.map((activity) => ({
              type: activity.type || 'activity',
              title: activity.title || 'Activity',
              status: activity.status || 'completed',
              time: activity.time ? formatDate(activity.time) : 'Unknown',
              points: Number(activity.points || 0)
            }))
          : [];
        setRecentActivity(formattedActivity.slice(0, 7));

        const formattedProgress = Array.isArray(progress.point_history)
          ? progress.point_history.map((item, idx) => ({
              id: Number(item.id || idx),
              source: item.source || 'Other',
              delta: Number(item.points_delta || 0),
              time: item.time ? formatDate(item.time) : 'Unknown',
            }))
          : [];
        setSkillProgress(formattedProgress);
      } catch (error) {
        if (!isMounted) {
          return;
        }
        console.error('Failed to fetch analytics data:', error);
        const message = error instanceof Error ? error.message : '';
        if (message.toLowerCase().includes('authentication required')) {
          return;
        }
        toast({
          title: "Failed to load analytics",
          description: message || 'Please try again later.',
          variant: "destructive"
        });
      }
    };

    void fetchAnalyticsData();
    const interval = window.setInterval(() => {
      void fetchAnalyticsData();
    }, 5000);
    return () => {
      isMounted = false;
      window.clearInterval(interval);
    };
  }, []);

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit' 
    });
  };

  const formatDuration = (seconds: number): string => {
    if (!seconds || seconds <= 0) {
      return '0m';
    }
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    if (hrs <= 0) {
      return `${mins}m`;
    }
    return `${hrs}h ${mins}m`;
  };

  const topRecentActivity = recentActivity.slice(0, 7);

  return (
    <AppLayout>
      <div className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">Analytics Dashboard</h1>
        </div>

        {/* Key Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2">
                <Target className="h-8 w-8 text-primary" />
                <div>
                  <div className="text-2xl font-bold">{stats.solvedProblems}</div>
                  <div className="text-sm text-muted-foreground">Problems Solved</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2">
                <TrendingUp className="h-8 w-8 text-green-500" />
                <div>
                  <div className="text-2xl font-bold">{stats.skillPoints}</div>
                  <div className="text-sm text-muted-foreground">Skill Points</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2">
                <Clock className="h-8 w-8 text-blue-500" />
                <div>
                  <div className="text-2xl font-bold">{formatDuration(stats.totalTimeSeconds)}</div>
                  <div className="text-sm text-muted-foreground">Total Time Spent</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2">
                <Calendar className="h-8 w-8 text-orange-500" />
                <div>
                  <div className="text-2xl font-bold">{stats.streak}</div>
                  <div className="text-sm text-muted-foreground">Day Streak</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Weekly Goal Progress */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5" />
                <span>Weekly Goal</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between text-sm">
                <span>Problems solved this week</span>
                <span>{stats.weeklyProgress}/{stats.weeklyGoal}</span>
              </div>
              <Progress value={(stats.weeklyProgress / stats.weeklyGoal) * 100} className="h-3" />
              <div className="text-sm text-muted-foreground">
                {stats.weeklyGoal - stats.weeklyProgress} more problems to reach your weekly goal
              </div>
              <div className="pt-2 border-t border-border/50 space-y-3">
                <div className="flex items-center space-x-2">
                  <BarChart3 className="h-5 w-5" />
                  <span className="text-2xl font-semibold leading-none tracking-tight">Monthly Goal</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Problems solved this month</span>
                  <span>{stats.monthlyProgress}/{stats.monthlyGoal}</span>
                </div>
                <Progress value={(stats.monthlyProgress / stats.monthlyGoal) * 100} className="h-3 mt-2" />
                <div className="text-sm text-muted-foreground mt-2">
                  {stats.monthlyGoal - stats.monthlyProgress} more problems to reach your monthly goal
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-[16rem] overflow-y-hidden hover:overflow-y-auto pr-1">
                {recentActivity.length === 0 ? (
                  <div className="text-center py-6 text-muted-foreground">
                    <Calendar className="w-10 h-10 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No recent activity data available</p>
                  </div>
                ) : (
                  topRecentActivity.map((activity, index) => (
                  <div key={`top-${index}`} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <div className="flex items-center space-x-3">
                      {activity.type === 'assessment' ? (
                        <Target className="h-5 w-5 text-blue-500" />
                      ) : activity.type === 'code_submission' ? (
                        <Code className="h-5 w-5 text-green-500" />
                      ) : (
                        <PlayCircle className="h-5 w-5 text-primary" />
                      )}
                      <div>
                        <div className="font-medium">{activity.title}</div>
                        <div className="text-sm text-muted-foreground">
                          {activity.status} • {activity.time}
                        </div>
                      </div>
                    </div>
                    {activity.points > 0 ? <Badge variant="secondary">+{activity.points} pts</Badge> : null}
                  </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Skill Progress */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
                <Wallet className="h-5 w-5" />
                <span>Skill Points Progress</span>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                      <Info className="h-4 w-4 text-muted-foreground" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-96 max-h-96 overflow-y-auto">
                    <div className="space-y-3 text-sm">
                      <div className="font-semibold">How to earn points</div>
                      <div className="text-muted-foreground">Practice solved: Beginner +5, Intermediate +10, Advanced +15</div>
                      <div className="text-muted-foreground">Video watched: Beginner +10, Intermediate +15, Advanced +20</div>
                      <div className="text-muted-foreground">Achievement completion: Beginner +10, Intermediate +20, Advanced +30</div>
                      <div className="text-muted-foreground">Weekly goal completion: +10</div>
                      <div className="text-muted-foreground">Monthly goal completion: +20</div>
                      <div className="text-muted-foreground">Login streak milestone bonus: day 5 +20, day 10 +30, day 15 +40, then +10 every next 5-day milestone</div>
                      <div className="pt-2 border-t border-border/50 font-semibold">Where to spend points</div>
                      <div className="text-muted-foreground">AI code generation request: -5 per request</div>
                    </div>
                  </PopoverContent>
                </Popover>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-[23rem] overflow-y-hidden hover:overflow-y-auto pr-1">
              {skillProgress.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Wallet className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p className="font-medium">No points history yet</p>
                  <p className="text-sm mt-1">Earn or use points to see source-wise progress.</p>
                </div>
              ) : (
                skillProgress.map((skill) => (
                <div key={skill.id} className="space-y-2 p-3 rounded-lg bg-muted/40">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">{skill.source}</span>
                    <div className="flex items-center space-x-2">
                      <Badge variant={skill.delta >= 0 ? 'secondary' : 'destructive'}>
                        {skill.delta >= 0 ? `+${skill.delta}` : `${skill.delta}`}
                      </Badge>
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground">{skill.time}</div>
                </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
};

export default Analytics;
