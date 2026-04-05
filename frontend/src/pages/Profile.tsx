import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { User, Mail, Calendar, Trophy, Upload, Target, BookOpen, Flame } from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import AppLayout from '@/components/layout/AppLayout';
import { API_BASE_URL, profileAPI } from '@/lib/api';

type ProfileStats = {
  beginner: { solved: number; total: number };
  intermediate: { solved: number; total: number };
  advanced: { solved: number; total: number };
};

type ProfileData = {
  id: number;
  username: string;
  email: string;
  profile_image_url?: string | null;
  bio?: string | null;
  skill_level?: string | null;
  created_at?: string | null;
  streak_days?: number | null;
  stats?: {
    beginner?: { solved?: number; total?: number };
    intermediate?: { solved?: number; total?: number };
    advanced?: { solved?: number; total?: number };
  };
};

type SubmissionItem = {
  id: number;
  problem_id: number;
  problem_title: string | null;
  level?: string | null;
  difficulty: string | null;
  status: string;
  submitted_at: string | null;
  score?: number | null;
  time_ms?: number | null;
};

const getCachedProfile = (): ProfileData | null => {
  try {
    const cached = localStorage.getItem('profile:cache');
    if (cached) {
      return JSON.parse(cached);
    }
  } catch (error) {
    console.warn('Failed to read cached profile', error);
  }
  try {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const user = JSON.parse(userStr);
      return {
        id: user.id ?? 0,
        username: user.username || 'User',
        email: user.email || '',
        profile_image_url: user.profile_image_url ?? null,
        bio: user.bio ?? null,
        skill_level: user.skill_level || 'beginner',
        created_at: user.created_at ?? null,
        streak_days: user.streak_days ?? null,
      };
    }
  } catch (error) {
    console.warn('Failed to read user cache', error);
  }
  return null;
};

const initialProfile = getCachedProfile();

const Profile = () => {
  const [profile, setProfile] = useState<ProfileData | null>(initialProfile);
  const [submissions, setSubmissions] = useState<SubmissionItem[]>([]);
  const hasCachedProfileRef = useRef(Boolean(initialProfile));
  const [isUploading, setIsUploading] = useState(false);

  const apiOrigin = API_BASE_URL.replace(/\/api\/?$/, '');
  const stats: ProfileStats = {
    beginner: {
      solved: profile?.stats?.beginner?.solved ?? 0,
      total: profile?.stats?.beginner?.total ?? 0,
    },
    intermediate: {
      solved: profile?.stats?.intermediate?.solved ?? 0,
      total: profile?.stats?.intermediate?.total ?? 0,
    },
    advanced: {
      solved: profile?.stats?.advanced?.solved ?? 0,
      total: profile?.stats?.advanced?.total ?? 0,
    },
  };
  const displayName = profile?.username || 'User';
  const initials = displayName
    .split(' ')
    .filter(Boolean)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
  const joinDate = profile?.created_at ? new Date(profile.created_at) : null;
  const avatarUrl = profile?.profile_image_url
    ? profile.profile_image_url.startsWith('http')
      ? profile.profile_image_url
      : `${apiOrigin}${profile.profile_image_url}`
    : '';

  useEffect(() => {
    const loadProfile = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        return;
      }
      try {
        const data = await profileAPI.getProfile();
        setProfile(data);
        try {
          localStorage.setItem('profile:cache', JSON.stringify(data));
          const stored = localStorage.getItem('user');
          const currentUser = stored ? JSON.parse(stored) : {};
          localStorage.setItem(
            'user',
            JSON.stringify({
              ...currentUser,
              id: data.id,
              username: data.username,
              email: data.email,
              profile_image_url: data.profile_image_url,
              skill_level: data.skill_level,
              created_at: data.created_at,
              streak_days: data.streak_days,
              bio: data.bio,
            })
          );
        } catch (error) {
          console.warn('Failed to update profile cache', error);
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Please try again later.';
        if (message.includes('Missing Authorization Header') && hasCachedProfileRef.current) {
          return;
        }
        toast({
          title: 'Failed to load profile',
          description: message,
          variant: 'destructive',
        });
      }
    };
    loadProfile();
  }, []);

  useEffect(() => {
    const loadSubmissions = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        return;
      }
      try {
        const data = await profileAPI.getSubmissions(200, { solvedOnly: true, currentLevelOnly: true });
        setSubmissions(Array.isArray(data) ? data : []);
      } catch {
        setSubmissions([]);
      }
    };
    loadSubmissions();
  }, [profile?.skill_level]);

  const handleAvatarUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    try {
      const result = await profileAPI.uploadAvatar(file);
      setProfile((prev) => {
        if (!prev) return prev;
        const next = { ...prev, profile_image_url: result.profile_image_url };
        try {
          localStorage.setItem('profile:cache', JSON.stringify(next));
        } catch (error) {
          console.warn('Failed to update cached avatar', error);
        }
        return next;
      });
      try {
        const stored = localStorage.getItem('user');
        if (stored) {
          const currentUser = JSON.parse(stored);
          localStorage.setItem('user', JSON.stringify({ ...currentUser, profile_image_url: result.profile_image_url }));
        }
      } catch (error) {
        console.warn('Failed to sync avatar to local storage', error);
      }
      toast({
        title: 'Avatar updated',
        description: 'Your profile photo has been updated.',
      });
    } catch (error) {
      toast({
        title: 'Avatar upload failed',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsUploading(false);
      event.target.value = '';
    }
  };

  const handleTakeAssessment = () => {
    toast({
      title: "Assessment started", 
      description: "Redirecting to level assessment test..."
    });
  };

  return (
    <AppLayout>
      <div className="p-4">
        <div className="max-w-6xl mx-auto space-y-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
              Profile
            </h1>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* User Info Card */}
            <div className="lg:col-span-1">
              <Card className="border-primary/20">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <User className="w-5 h-5 mr-2 text-primary" />
                    User Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Avatar Upload */}
                  <div className="flex flex-col items-center space-y-4">
                    <Avatar className="w-24 h-24">
                      <AvatarImage src={avatarUrl} />
                      <AvatarFallback className="text-lg bg-primary text-primary-foreground">
                        {initials || 'U'}
                      </AvatarFallback>
                    </Avatar>
                    
                    <div className="relative">
                      <Input
                        type="file"
                        accept="image/*"
                        onChange={handleAvatarUpload}
                        className="hidden"
                        id="avatar-upload"
                      />
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => document.getElementById('avatar-upload')?.click()}
                        disabled={isUploading}
                      >
                        <Upload className="w-4 h-4 mr-2" />
                        {isUploading ? 'Uploading...' : 'Upload Photo'}
                      </Button>
                    </div>
                  </div>

                  <Separator />

                  {/* User Details */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <User className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Name</span>
                      </div>
                      <span className="font-medium">{displayName}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Mail className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Email</span>
                      </div>
                      <span className="font-medium">{profile?.email || '—'}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Target className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Level</span>
                      </div>
                      <Badge variant="secondary">{profile?.skill_level || 'beginner'}</Badge>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Calendar className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Joined</span>
                      </div>
                      <span className="font-medium">{joinDate ? joinDate.toDateString() : '—'}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Flame className="w-4 h-4 text-orange-500" />
                        <span className="text-sm text-muted-foreground">Streak</span>
                      </div>
                      <span className="font-medium text-orange-500">{profile?.streak_days ?? 0} days</span>
                    </div>
                  </div>

                  <Separator />

                  {/* Assessment Button */}
                  <Button 
                    onClick={handleTakeAssessment}
                    className="w-full bg-gradient-primary"
                  >
                    <Trophy className="w-4 h-4 mr-2" />
                    Take Level Assessment
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Stats and Submission History */}
            <div className="lg:col-span-2 space-y-6">
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="border-success/20">
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold text-success mb-1">{stats.beginner.solved}</div>
                    <div className="text-sm text-muted-foreground">Beginner Solved</div>
                  </CardContent>
                </Card>
                
                <Card className="border-warning/20">
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold text-warning mb-1">{stats.intermediate.solved}</div>
                    <div className="text-sm text-muted-foreground">Intermediate Solved</div>
                  </CardContent>
                </Card>
                
                <Card className="border-destructive/20">
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold text-destructive mb-1">{stats.advanced.solved}</div>
                    <div className="text-sm text-muted-foreground">Advanced Solved</div>
                  </CardContent>
                </Card>
              </div>

              {/* Progress Overview */}
              <Card className="border-accent/20">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <BookOpen className="w-5 h-5 mr-2 text-accent" />
                    Progress Overview
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex items-center justify-between text-sm mb-2">
                        <span>Beginner Problems</span>
                        <span>{stats.beginner.solved}/{stats.beginner.total}</span>
                      </div>
                      <Progress value={stats.beginner.total ? (stats.beginner.solved / stats.beginner.total) * 100 : 0} className="h-2" />
                    </div>
                    
                    <div>
                      <div className="flex items-center justify-between text-sm mb-2">
                        <span>Intermediate Problems</span>
                        <span>{stats.intermediate.solved}/{stats.intermediate.total}</span>
                      </div>
                      <Progress value={stats.intermediate.total ? (stats.intermediate.solved / stats.intermediate.total) * 100 : 0} className="h-2" />
                    </div>
                    
                    <div>
                      <div className="flex items-center justify-between text-sm mb-2">
                        <span>Advanced Problems</span>
                        <span>{stats.advanced.solved}/{stats.advanced.total}</span>
                      </div>
                      <Progress value={stats.advanced.total ? (stats.advanced.solved / stats.advanced.total) * 100 : 0} className="h-2" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Submission History */}
              <Card className="border-muted">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <BookOpen className="w-5 h-5 mr-2" />
                    Submission History
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 max-h-[12rem] overflow-y-hidden hover:overflow-y-auto pr-1">
                    {submissions.length === 0 ? (
                      <div className="text-center py-8">
                        <BookOpen className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                        <h3 className="text-lg font-medium mb-2">No solved submissions yet</h3>
                        <p className="text-muted-foreground">
                          Solve problems in your current level to build submission history.
                        </p>
                      </div>
                    ) : (
                      submissions.map((item) => (
                        <div key={item.id} className="rounded-lg border border-border/60 p-3 bg-muted/30">
                          <div className="flex items-center justify-between gap-3">
                            <div className="font-medium truncate">{item.problem_title || `Problem #${item.problem_id}`}</div>
                            <Badge variant="secondary">{item.difficulty || 'N/A'}</Badge>
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {item.level || profile?.skill_level || 'beginner'}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
};

export default Profile;
