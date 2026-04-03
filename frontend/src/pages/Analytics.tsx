import React, { useEffect, useState } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  BarChart3, 
  TrendingUp, 
  Clock, 
  Target, 
  Code, 
  CheckCircle,
  XCircle,
  Calendar
} from 'lucide-react';
import { analyticsAPI } from '@/lib/api';
import { toast } from '@/hooks/use-toast';

type AnalyticsOverviewResponse = {
  total_submissions?: number;
  success_rate?: number;
  average_time?: number;
  streak?: number;
  total_points?: number;
  problems_solved?: number;
  weekly_goal?: number;
  weekly_progress?: number;
};

type AnalyticsProgressResponse = {
  weekly_activity?: Array<{ date: string; count: number }>;
  skill_progress?: Array<{ skill: string; level: number; max_level: number }>;
};

const Analytics = () => {
  const [stats, setStats] = useState({
    totalProblems: 0,
    solvedProblems: 0,
    successRate: 0,
    skillPoints: 0,
    averageTime: 0,
    streak: 0,
    weeklyGoal: 10,
    weeklyProgress: 0
  });

  const [recentActivity, setRecentActivity] = useState<Array<{
    date: string;
    problems: number;
    time: number;
    success: boolean;
  }>>([]);

  const [skillProgress, setSkillProgress] = useState<Array<{
    skill: string;
    completed: number;
    total: number;
    percentage: number;
  }>>([]);

  useEffect(() => {
    let isMounted = true;
    const fetchAnalyticsData = async () => {
      try {
        const [overviewResponse, progressResponse] = await Promise.all([
          analyticsAPI.getOverview(),
          analyticsAPI.getProgress()
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
          averageTime: Math.round(overview.average_time || 0),
          streak: overview.streak || 0,
          weeklyGoal: overview.weekly_goal || 5,
          weeklyProgress: overview.weekly_progress || 0
        });

        // Format weekly activity from progress response
        if (progress.weekly_activity) {
          const formattedActivity = progress.weekly_activity.map(activity => ({
            date: formatDate(activity.date),
            problems: activity.count,
            time: activity.count * 10, // Estimated time
            success: true
          }));
          setRecentActivity(formattedActivity);
        }

        // Format skill progress from progress response
        if (progress.skill_progress) {
          const formattedProgress = progress.skill_progress.map(skill => ({
            skill: skill.skill,
            completed: skill.level,
            total: skill.max_level,
            percentage: Math.round((skill.level / skill.max_level) * 100)
          }));
          setSkillProgress(formattedProgress);
        }
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
    }, 15000);
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
                  <div className="text-2xl font-bold">{stats.averageTime}m</div>
                  <div className="text-sm text-muted-foreground">Avg. Solve Time</div>
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
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentActivity.length === 0 ? (
                  <div className="text-center py-6 text-muted-foreground">
                    <Calendar className="w-10 h-10 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No recent activity data available</p>
                  </div>
                ) : (
                  recentActivity.map((activity, index) => (
                  <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <div className="flex items-center space-x-3">
                      {activity.success ? (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-500" />
                      )}
                      <div>
                        <div className="font-medium">{activity.date}</div>
                        <div className="text-sm text-muted-foreground">
                          {activity.problems} problems, {activity.time}min
                        </div>
                      </div>
                    </div>
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
              <Code className="h-5 w-5" />
              <span>Skill Progress</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {skillProgress.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Code className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p className="font-medium">No skill progress data available</p>
                  <p className="text-sm mt-1">Complete challenges to track your progress!</p>
                </div>
              ) : (
                skillProgress.map((skill, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">{skill.skill}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-muted-foreground">
                        {skill.completed}/{skill.total}
                      </span>
                      <Badge variant={skill.percentage === 100 ? "default" : "secondary"}>
                        {skill.percentage}%
                      </Badge>
                    </div>
                  </div>
                  <Progress value={skill.percentage} className="h-2" />
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
