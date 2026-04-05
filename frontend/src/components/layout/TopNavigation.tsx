import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  Menu,
  Code2,
  User,
  Settings,
  LogOut,
  Moon,
  Sun,
  Flame,
  Bell,
  Search
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import { useTheme } from 'next-themes';
import { API_BASE_URL, contentAPI, practiceAPI, profileAPI } from '@/lib/api';

interface TopNavigationProps {
  onMenuClick: () => void;
}

const STREAK_REMINDERS_KEY = 'settings:streak-reminders';
const STREAK_REMINDER_DISMISSED_KEY = 'notifications:streak-reminder-dismissed-date';

const TopNavigation: React.FC<TopNavigationProps> = ({ onMenuClick }) => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { theme, setTheme } = useTheme();
  
  // Get user info from localStorage
  const apiOrigin = API_BASE_URL.replace(/\/api\/?$/, '');
  const getUserInfo = () => {
    try {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        const user = JSON.parse(userStr);
        const level = user.skill_level || 'beginner';
        const username = user.username || 'User';
        const initials = username.substring(0, 2).toUpperCase();
        const storedProfileImage = user.profile_image_url || '';
        const profileImageUrl = storedProfileImage
          ? storedProfileImage.startsWith('http')
            ? storedProfileImage
            : `${apiOrigin}${storedProfileImage}`
          : '';
        
        return {
          name: username,
          level: level.charAt(0).toUpperCase() + level.slice(1), // Capitalize first letter
          initials: initials,
          streak: Number(user.streak_days || 0),
          notifications: 0,
          profileImageUrl: profileImageUrl,
        };
      }
    } catch (e) {
      console.error('Error reading user from localStorage:', e);
    }
    // Default values
    return {
      name: 'User',
      level: 'Beginner',
      initials: 'U',
      streak: 0,
      notifications: 0,
      profileImageUrl: '',
    };
  };

  const [userInfo, setUserInfo] = useState(getUserInfo());
  const [searchQuery, setSearchQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchItems, setSearchItems] = useState<Array<{
    id: string;
    title: string;
    subtitle: string;
    path: string;
    type: 'page' | 'challenge' | 'video' | 'assessment';
  }>>([]);
  const searchContainerRef = useRef<HTMLDivElement | null>(null);
  const getTodayKey = () => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  };
  const isStreakReminderEnabled = () => {
    try {
      return localStorage.getItem(STREAK_REMINDERS_KEY) !== 'false';
    } catch {
      return true;
    }
  };
  const isStreakReminderUnread = () => {
    if (!isStreakReminderEnabled()) {
      return false;
    }
    try {
      return localStorage.getItem(STREAK_REMINDER_DISMISSED_KEY) !== getTodayKey();
    } catch {
      return true;
    }
  };
  const refreshNotifications = () => {
    const unreadCount = isStreakReminderUnread() ? 1 : 0;
    setUserInfo((prev) => ({ ...prev, notifications: unreadCount }));
  };
  const getCurrentSkillLevel = (): 'beginner' | 'intermediate' | 'advanced' => {
    try {
      const raw = localStorage.getItem('user');
      if (!raw) {
        return 'beginner';
      }
      const user = JSON.parse(raw) as { skill_level?: string };
      const level = (user.skill_level || '').toLowerCase();
      if (level === 'intermediate' || level === 'advanced') {
        return level;
      }
      return 'beginner';
    } catch {
      return 'beginner';
    }
  };

  // Update user info when localStorage changes
  useEffect(() => {
    const handleStorageChange = () => {
      setUserInfo(getUserInfo());
    };

    // Listen for storage events (when user logs in/out on another tab)
    window.addEventListener('storage', handleStorageChange);
    
    // Also check periodically (for same-tab updates)
    const interval = setInterval(handleStorageChange, 1000);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const profile = await profileAPI.getProfile();
        const profileImageUrl = profile.profile_image_url
          ? profile.profile_image_url.startsWith('http')
            ? profile.profile_image_url
            : `${apiOrigin}${profile.profile_image_url}`
          : '';
        const nextUser = (() => {
          try {
            const stored = localStorage.getItem('user');
            return stored ? JSON.parse(stored) : null;
          } catch {
            return null;
          }
        })();
        const updatedUser = nextUser
          ? {
              ...nextUser,
              profile_image_url: profile.profile_image_url,
              skill_level: profile.skill_level,
              username: profile.username,
              email: profile.email,
              streak_days: profile.streak_days,
              total_points: profile.total_points,
            }
          : null;
        if (updatedUser) {
          localStorage.setItem('user', JSON.stringify(updatedUser));
        }
        setUserInfo((prev) => ({
          ...prev,
          name: profile.username || prev.name,
          level: profile.skill_level ? profile.skill_level.charAt(0).toUpperCase() + profile.skill_level.slice(1) : prev.level,
          initials: profile.username ? profile.username.substring(0, 2).toUpperCase() : prev.initials,
          streak: profile.streak_days ?? prev.streak,
          profileImageUrl,
        }));
      } catch (error) {
        console.warn('Failed to load profile for nav avatar', error);
      }
    };
    loadProfile();
  }, [apiOrigin]);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const skillLevel = getCurrentSkillLevel();
    const assessmentTitle = `${skillLevel.charAt(0).toUpperCase()}${skillLevel.slice(1)} Assessment`;
    const staticPages: Array<{
      id: string;
      title: string;
      subtitle: string;
      path: string;
      type: 'page' | 'assessment';
    }> = [
      { id: 'page-dashboard', title: 'Dashboard', subtitle: 'Page', path: '/dashboard', type: 'page' },
      { id: 'page-practice', title: 'Practice Arena', subtitle: 'Page', path: '/practice', type: 'page' },
      { id: 'page-analytics', title: 'Analytics', subtitle: 'Page', path: '/analytics', type: 'page' },
      { id: 'page-compiler', title: 'Compiler', subtitle: 'Page', path: '/compiler', type: 'page' },
      { id: 'page-generator', title: 'Generator', subtitle: 'Page', path: '/generator', type: 'page' },
      { id: 'page-explainer', title: 'Explainer', subtitle: 'Page', path: '/explainer', type: 'page' },
      { id: 'page-help', title: 'Help', subtitle: 'Page', path: '/help', type: 'page' },
      { id: 'page-profile', title: 'Profile', subtitle: 'Page', path: '/profile', type: 'page' },
      { id: 'page-settings', title: 'Settings', subtitle: 'Page', path: '/settings', type: 'page' },
      { id: `assessment-${skillLevel}`, title: assessmentTitle, subtitle: 'Assessment', path: `/assessment?level=${skillLevel}`, type: 'assessment' },
    ];
    setSearchItems(staticPages);
    if (!token) {
      return;
    }
    let mounted = true;
    const loadDynamic = async () => {
      try {
        const [catalog, learningPaths] = await Promise.all([
          practiceAPI.getCatalog(),
          contentAPI.getLearningPaths(),
        ]);
        if (!mounted) {
          return;
        }
        const challenges = (catalog || []).map((item) => ({
          id: `challenge-${item.id}`,
          title: item.title,
          subtitle: `Challenge • ${(item.level || 'beginner').toString()}`,
          path: `/practice/solve/${item.level}/${encodeURIComponent(item.title)}`,
          type: 'challenge' as const,
        }));
        const videos = (learningPaths || []).map((item) => ({
          id: `video-${item.id}`,
          title: item.title,
          subtitle: `Video • ${item.level}`,
          path: `/learning-path/java/${encodeURIComponent(item.slug)}`,
          type: 'video' as const,
        }));
        setSearchItems([...staticPages, ...challenges, ...videos]);
      } catch {
        if (!mounted) {
          return;
        }
        setSearchItems(staticPages);
      }
    };
    void loadDynamic();
    return () => {
      mounted = false;
    };
  }, [userInfo.level]);

  useEffect(() => {
    refreshNotifications();
    const interval = window.setInterval(() => {
      refreshNotifications();
    }, 60_000);
    const onStorage = (event: StorageEvent) => {
      if (event.key === STREAK_REMINDERS_KEY || event.key === STREAK_REMINDER_DISMISSED_KEY) {
        refreshNotifications();
      }
    };
    window.addEventListener('storage', onStorage);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener('storage', onStorage);
    };
  }, []);

  useEffect(() => {
    const onMouseDown = (event: MouseEvent) => {
      const target = event.target as Node;
      if (!searchContainerRef.current || searchContainerRef.current.contains(target)) {
        return;
      }
      setSearchOpen(false);
    };
    document.addEventListener('mousedown', onMouseDown);
    return () => {
      document.removeEventListener('mousedown', onMouseDown);
    };
  }, []);

  const filteredSearchItems = useMemo(() => {
    const normalized = searchQuery.trim().toLowerCase();
    if (!normalized) {
      return [];
    }
    return searchItems
      .filter((item) => `${item.title} ${item.subtitle}`.toLowerCase().includes(normalized))
      .slice(0, 20);
  }, [searchItems, searchQuery]);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    toast({
      title: `Switched to ${newTheme === 'light' ? 'Light' : 'Dark'} Mode`,
      description: "Theme preference saved to your profile.",
    });
  };

  const handleLogout = () => {
    // Clear user data from localStorage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    Object.keys(sessionStorage).forEach((key) => {
      if (key.startsWith('compiler:state:')) {
        sessionStorage.removeItem(key);
      }
    });
    Object.keys(localStorage).forEach((key) => {
      if (key.startsWith('compiler:state:') || key === 'compiler:code' || key === 'compiler:code-fallback') {
        localStorage.removeItem(key);
      }
    });
    sessionStorage.removeItem('compiler:output');
    sessionStorage.removeItem('compiler:session-id');
    
    toast({
      title: "Logged out successfully",
      description: "See you soon!",
    });
    navigate('/');
  };

  const markReminderAsRead = () => {
    try {
      localStorage.setItem(STREAK_REMINDER_DISMISSED_KEY, getTodayKey());
    } catch {
      void 0;
    }
    refreshNotifications();
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-lg border-0 shadow-none">
      <div className="flex items-center justify-between h-16 px-6">
        {/* Left Side */}
        <div className="flex items-center -space-x-4">
          <div className="w-16 flex items-center">
            <Button 
              variant="ghost" 
              size="sm"
              onClick={onMenuClick}
              className="-ml-2 p-2"
            >
              <Menu className="w-5 h-5" />
            </Button>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Code2 className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold hidden sm:block">CodeMaster</span>
          </div>
        </div>

        {/* Center - Search */}
        <div className="hidden md:flex flex-1 max-w-md mx-8">
          <div ref={searchContainerRef} className="relative w-full">
            <input type="text" name="username" autoComplete="username" tabIndex={-1} className="hidden" />
            <input type="password" name="password" autoComplete="current-password" tabIndex={-1} className="hidden" />
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <Input 
              placeholder="Search pages, challenges, videos, assessments..." 
              id="cm-global-search"
              type="text"
              name="cm-global-search"
              autoComplete="off"
              autoCapitalize="off"
              autoCorrect="off"
              spellCheck={false}
              inputMode="search"
              aria-autocomplete="none"
              data-form-type="other"
              data-lpignore="true"
              data-1p-ignore="true"
              data-bwignore="true"
              value={searchQuery}
              onFocus={() => setSearchOpen(true)}
              onChange={(event) => setSearchQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && filteredSearchItems.length > 0) {
                  const first = filteredSearchItems[0];
                  navigate(first.path);
                  setSearchOpen(false);
                  setSearchQuery('');
                }
              }}
              className="pl-10 bg-background/85 dark:bg-muted/40 border border-border/65 dark:border-border/75 focus:bg-background dark:focus:bg-background/95 focus:border-primary/50"
            />
            {searchOpen && searchQuery.trim().length > 0 && (
              <div className="absolute top-[calc(100%+0.5rem)] left-0 right-0 bg-background border border-border rounded-md shadow-lg max-h-80 overflow-y-auto z-50">
                {filteredSearchItems.length === 0 ? (
                  <div className="px-3 py-2 text-sm text-muted-foreground">No results found</div>
                ) : (
                  filteredSearchItems.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className="w-full text-left px-3 py-2 hover:bg-muted transition-colors border-b border-border/50 last:border-b-0"
                      onClick={() => {
                        navigate(item.path);
                        setSearchOpen(false);
                        setSearchQuery('');
                      }}
                    >
                      <div className="text-sm font-medium">{item.title}</div>
                      <div className="text-xs text-muted-foreground">{item.subtitle}</div>
                    </button>
                  ))
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Side */}
        <div className="flex items-center space-x-4">
          {/* Streak */}
          <div className="hidden sm:flex items-center space-x-2 px-3 py-1 bg-orange-500/12 border border-orange-500/35 rounded-full">
            <Flame className="w-4 h-4 text-orange-500" />
            <span className="text-sm font-medium text-orange-500">{userInfo.streak}</span>
          </div>

          {/* Level Badge */}
          <Badge variant="secondary" className="hidden sm:block">
            {userInfo.level}
          </Badge>

          {/* Theme Toggle */}
          <div className="flex items-center">
            <button
              type="button"
              role="switch"
              aria-checked={theme === 'dark'}
              aria-label="Toggle theme"
              onClick={toggleTheme}
              className={`relative h-8 w-16 rounded-full border transition-all duration-300 ${
                theme === 'dark'
                  ? 'bg-gradient-to-r from-slate-700 via-slate-800 to-slate-900 border-slate-500/60'
                  : 'bg-gradient-to-r from-sky-200 via-sky-100 to-amber-100 border-sky-300/80'
              }`}
            >
              <span className={`absolute left-2 top-1.5 transition-opacity duration-300 ${theme === 'dark' ? 'opacity-30' : 'opacity-100'}`}>
                <Sun className="w-3.5 h-3.5 text-amber-500" />
              </span>
              <span className={`absolute right-2 top-1.5 transition-opacity duration-300 ${theme === 'dark' ? 'opacity-100' : 'opacity-30'}`}>
                <Moon className="w-3.5 h-3.5 text-indigo-200" />
              </span>
              <span
                className={`absolute top-0.5 h-6 w-6 rounded-full border border-white/80 shadow-md transition-all duration-300 flex items-center justify-center ${
                  theme === 'dark'
                    ? 'left-[2.1rem] bg-slate-950'
                    : 'left-0.5 bg-white'
                }`}
              >
                {theme === 'dark' ? (
                  <Moon className="w-3.5 h-3.5 text-indigo-200" />
                ) : (
                  <Sun className="w-3.5 h-3.5 text-amber-500" />
                )}
              </span>
            </button>
          </div>

          {/* Notifications */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="relative">
                <Bell className="w-5 h-5" />
                {userInfo.notifications > 0 && (
                  <Badge className="absolute -top-1 -right-1 w-5 h-5 text-xs p-0 flex items-center justify-center bg-destructive text-destructive-foreground">
                    {userInfo.notifications}
                  </Badge>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-80" align="end">
              <DropdownMenuLabel>Notifications</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {!isStreakReminderEnabled() ? (
                <div className="px-3 py-2 text-sm text-muted-foreground">
                  Streak reminders are turned off in Settings.
                </div>
              ) : isStreakReminderUnread() ? (
                <div className="px-3 py-3 space-y-2">
                  <div className="text-sm font-medium">Daily Streak Reminder</div>
                  <div className="text-xs text-muted-foreground">
                    Your current streak is {userInfo.streak} day{userInfo.streak === 1 ? '' : 's'}. Log in and practice every day to maintain and grow your streak.
                  </div>
                  <Button size="sm" variant="secondary" onClick={markReminderAsRead}>
                    Mark as read
                  </Button>
                </div>
              ) : (
                <div className="px-3 py-2 text-sm text-muted-foreground">
                  You are all caught up for today.
                </div>
              )}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={userInfo.profileImageUrl} />
                  <AvatarFallback className="bg-primary text-primary-foreground text-sm">
                    {userInfo.initials}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">{userInfo.name}</p>
                  <p className="text-xs leading-none text-muted-foreground">
                    Level: {userInfo.level}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate('/profile')}>
                <User className="mr-2 h-4 w-4" />
                <span>Profile</span>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate('/settings')}>
                <Settings className="mr-2 h-4 w-4" />
                <span>Settings</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </nav>
  );
};

export default TopNavigation;
