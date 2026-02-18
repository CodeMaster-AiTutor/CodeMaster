import React, { useState, useEffect } from 'react';
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
import { Switch } from '@/components/ui/switch';
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
import { useLocation, useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import { useTheme } from 'next-themes';
import { API_BASE_URL, profileAPI } from '@/lib/api';

interface TopNavigationProps {
  onMenuClick: () => void;
}

const TopNavigation: React.FC<TopNavigationProps> = ({ onMenuClick }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();
  const { theme, setTheme } = useTheme();
  const isSettingsRoute = location.pathname === '/settings';
  const searchAutoComplete = isSettingsRoute ? 'new-password' : 'off';
  const searchName = isSettingsRoute ? 'settings-search' : 'nav-search';
  
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
          streak: 0,
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
        const updatedUser = nextUser ? { ...nextUser, profile_image_url: profile.profile_image_url } : null;
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

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-lg border-b border-border/20">
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
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <Input 
              placeholder="Search challenges, tutorials..." 
              type="search"
              name={searchName}
              autoComplete={searchAutoComplete}
              autoCapitalize="off"
              autoCorrect="off"
              spellCheck={false}
              inputMode="search"
              aria-autocomplete="none"
              data-lpignore="true"
              data-1p-ignore="true"
              data-bwignore="true"
              readOnly={isSettingsRoute}
              onFocus={(event) => {
                if (isSettingsRoute) {
                  event.currentTarget.readOnly = false;
                }
              }}
              className="pl-10 bg-muted/50 border-0 focus:bg-background"
            />
          </div>
        </div>

        {/* Right Side */}
        <div className="flex items-center space-x-4">
          {/* Streak */}
          <div className="hidden sm:flex items-center space-x-2 px-3 py-1 bg-orange-500/10 rounded-full">
            <Flame className="w-4 h-4 text-orange-500" />
            <span className="text-sm font-medium text-orange-500">{userInfo.streak}</span>
          </div>

          {/* Level Badge */}
          <Badge variant="secondary" className="hidden sm:block">
            {userInfo.level}
          </Badge>

          {/* Theme Toggle */}
          <div className="flex items-center space-x-2">
            <Sun className="w-4 h-4" />
            <Switch 
              checked={theme === 'dark'}
              onCheckedChange={toggleTheme}
            />
            <Moon className="w-4 h-4" />
          </div>

          {/* Notifications */}
          <Button variant="ghost" size="sm" className="relative">
            <Bell className="w-5 h-5" />
            {userInfo.notifications > 0 && (
              <Badge className="absolute -top-1 -right-1 w-5 h-5 text-xs p-0 flex items-center justify-center bg-destructive text-destructive-foreground">
                {userInfo.notifications}
              </Badge>
            )}
          </Button>

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
