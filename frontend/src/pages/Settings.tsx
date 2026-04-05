import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Code, User, Shield, Trash2, Palette, Sun, Moon, Bell, Save, Loader2 } from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import AppLayout from '@/components/layout/AppLayout';
import { authAPI, profileAPI, settingsAPI } from '@/lib/api';
import { useTheme } from 'next-themes';
import { useNavigate } from 'react-router-dom';
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction
} from '@/components/ui/alert-dialog';

const EDITOR_FONT_SIZE_KEY = 'settings:editor-font-size';
const EDITOR_THEME_KEY = 'settings:editor-theme';
const EDITOR_UPDATED_AT_KEY = 'settings:editor-updated-at';
const SETTINGS_SUPPORTS_EDITOR_THEME_KEY = 'settings:supports-editor-theme';
const STREAK_REMINDERS_KEY = 'settings:streak-reminders';
const EDITOR_THEMES = [
  { value: 'vs-dark', label: 'VS Code Dark' },
  { value: 'vs', label: 'VS Code Light' },
  { value: 'hc-black', label: 'High Contrast Dark' },
  { value: 'hc-light', label: 'High Contrast Light' },
  { value: 'github-dark', label: 'GitHub Dark' },
  { value: 'github-light', label: 'GitHub Light' },
  { value: 'jellyfish', label: 'Jellyfish' }
];

const getStoredEditorFontSize = () => {
  try {
    return localStorage.getItem(EDITOR_FONT_SIZE_KEY) || '14';
  } catch {
    return '14';
  }
};

const getStoredEditorTheme = () => {
  try {
    return localStorage.getItem(EDITOR_THEME_KEY) || 'vs-dark';
  } catch {
    return 'vs-dark';
  }
};

const getStoredEditorUpdatedAt = () => {
  try {
    const stored = localStorage.getItem(EDITOR_UPDATED_AT_KEY);
    const parsed = stored ? Date.parse(stored) : 0;
    return Number.isFinite(parsed) ? parsed : 0;
  } catch {
    return 0;
  }
};

const getStoredEditorThemeSupport = () => {
  try {
    const stored = localStorage.getItem(SETTINGS_SUPPORTS_EDITOR_THEME_KEY);
    if (stored === 'false') {
      return false;
    }
    if (stored === 'true') {
      return true;
    }
    return true;
  } catch {
    return true;
  }
};

const getCurrentAppThemeIsDark = () => {
  try {
    const rootHasDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark');
    if (rootHasDark) {
      return true;
    }
    const storedTheme = localStorage.getItem('theme');
    if (storedTheme === 'light') {
      return false;
    }
    if (storedTheme === 'dark') {
      return true;
    }
    return false;
  } catch {
    return false;
  }
};

const getStoredStreakReminders = () => {
  try {
    const stored = localStorage.getItem(STREAK_REMINDERS_KEY);
    if (stored === 'false') {
      return false;
    }
    if (stored === 'true') {
      return true;
    }
    return true;
  } catch {
    return true;
  }
};

const Settings = () => {
  const { setTheme, resolvedTheme } = useTheme();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isUpdatingPassword, setIsUpdatingPassword] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [deletePassword, setDeletePassword] = useState('');
  const hasLoadedRef = useRef(false);
  const persistTimerRef = useRef<number | null>(null);
  const [settings, setSettings] = useState(() => ({
    fontSize: getStoredEditorFontSize(),
    editorTheme: getStoredEditorTheme(),
    darkMode: true,
    emailNotifications: true,
    streakReminders: getStoredStreakReminders()
  }));

  const updateSettings = <K extends keyof typeof settings>(key: K, value: (typeof settings)[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    if (key === 'fontSize') {
      try {
        localStorage.setItem(EDITOR_FONT_SIZE_KEY, String(value));
        localStorage.setItem(EDITOR_UPDATED_AT_KEY, new Date().toISOString());
      } catch {
        void 0;
      }
    }
    if (key === 'editorTheme') {
      try {
        localStorage.setItem(EDITOR_THEME_KEY, String(value));
        localStorage.setItem(EDITOR_UPDATED_AT_KEY, new Date().toISOString());
      } catch {
        void 0;
      }
    }
    if (key === 'streakReminders') {
      try {
        localStorage.setItem(STREAK_REMINDERS_KEY, String(Boolean(value)));
      } catch {
        void 0;
      }
    }
  };

  useEffect(() => {
    const loadSettings = async () => {
      setIsLoading(true);
      try {
        const data = await settingsAPI.getSettings();
        const darkMode = getCurrentAppThemeIsDark();
        const themeValues = new Set(EDITOR_THEMES.map((theme) => theme.value));
        const localUpdatedAt = getStoredEditorUpdatedAt();
        const apiUpdatedAt = data.updated_at ? Date.parse(data.updated_at) : 0;
        const apiUpdatedAtValue = Number.isFinite(apiUpdatedAt) ? apiUpdatedAt : 0;
        const localEditorTheme = themeValues.has(getStoredEditorTheme()) ? getStoredEditorTheme() : 'vs-dark';
        const localFontSize = getStoredEditorFontSize();
        const localIsNewer = localUpdatedAt && (!apiUpdatedAtValue || localUpdatedAt > apiUpdatedAtValue);
        const storedSupportsEditorTheme = getStoredEditorThemeSupport();
        const apiSupportsEditorTheme = typeof data.editor_theme === 'string' && data.editor_theme.length > 0;
        if (apiSupportsEditorTheme && !storedSupportsEditorTheme) {
          try {
            localStorage.setItem(SETTINGS_SUPPORTS_EDITOR_THEME_KEY, 'true');
          } catch {
            void 0;
          }
        }
        const supportsEditorTheme = storedSupportsEditorTheme || apiSupportsEditorTheme;
        if (localIsNewer) {
          setSettings((prev) => ({
            ...prev,
            fontSize: localFontSize,
            editorTheme: localEditorTheme,
            darkMode,
          }));
          try {
            const payload: { font_size: number; editor_theme?: string } = {
              font_size: Number(localFontSize),
            };
            if (supportsEditorTheme) {
              payload.editor_theme = localEditorTheme;
            }
            const response = await settingsAPI.updateSettings(payload);
            if (response?.updated_at) {
              localStorage.setItem(EDITOR_UPDATED_AT_KEY, response.updated_at);
            }
            localStorage.setItem(EDITOR_FONT_SIZE_KEY, localFontSize);
            localStorage.setItem(EDITOR_THEME_KEY, localEditorTheme);
          } catch (error) {
            const message = error instanceof Error ? error.message : '';
            if (message.includes('Unknown settings: editor_theme')) {
              localStorage.setItem(SETTINGS_SUPPORTS_EDITOR_THEME_KEY, 'false');
              try {
                const response = await settingsAPI.updateSettings({ font_size: Number(localFontSize) });
                if (response?.updated_at) {
                  localStorage.setItem(EDITOR_UPDATED_AT_KEY, response.updated_at);
                }
              } catch {
                void 0;
              }
            }
          }
        } else {
          const nextEditorTheme = themeValues.has(data.editor_theme) ? data.editor_theme : 'vs-dark';
          setSettings((prev) => ({
            ...prev,
            fontSize: String(data.font_size ?? 14),
            editorTheme: nextEditorTheme,
            darkMode,
          }));
          try {
            localStorage.setItem(EDITOR_FONT_SIZE_KEY, String(data.font_size ?? 14));
            localStorage.setItem(EDITOR_THEME_KEY, nextEditorTheme);
            if (data.updated_at) {
              localStorage.setItem(EDITOR_UPDATED_AT_KEY, data.updated_at);
            }
          } catch {
            void 0;
          }
        }
      } catch (error) {
        toast({
          title: "Failed to load settings",
          description: error instanceof Error ? error.message : 'Please try again later.',
          variant: "destructive"
        });
      } finally {
        setIsLoading(false);
        hasLoadedRef.current = true;
      }
    };
    loadSettings();
  }, []);

  useEffect(() => {
    if (!resolvedTheme) {
      return;
    }
    const isDark = resolvedTheme === 'dark';
    setSettings((prev) => (prev.darkMode === isDark ? prev : { ...prev, darkMode: isDark }));
  }, [resolvedTheme]);

  const persistEditorSettings = useCallback(async () => {
    setIsSaving(true);
    try {
      const supportsEditorTheme = getStoredEditorThemeSupport();
      const payload: { font_size: number; editor_theme?: string; theme: string } = {
        font_size: Number(settings.fontSize),
        theme: settings.darkMode ? 'dark' : 'light',
      };
      if (supportsEditorTheme) {
        payload.editor_theme = settings.editorTheme;
      }
      const response = await settingsAPI.updateSettings(payload);
      try {
        localStorage.setItem(EDITOR_FONT_SIZE_KEY, String(settings.fontSize));
        localStorage.setItem(EDITOR_THEME_KEY, settings.editorTheme);
        localStorage.setItem(EDITOR_UPDATED_AT_KEY, response?.updated_at ?? new Date().toISOString());
      } catch {
        void 0;
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : '';
      if (message.includes('Unknown settings: editor_theme')) {
        localStorage.setItem(SETTINGS_SUPPORTS_EDITOR_THEME_KEY, 'false');
        try {
          const response = await settingsAPI.updateSettings({
            font_size: Number(settings.fontSize),
            theme: settings.darkMode ? 'dark' : 'light',
          });
          localStorage.setItem(EDITOR_UPDATED_AT_KEY, response?.updated_at ?? new Date().toISOString());
        } catch (innerError) {
          toast({
            title: "Failed to save settings",
            description: innerError instanceof Error ? innerError.message : 'Please try again later.',
            variant: "destructive"
          });
        }
      } else {
        toast({
          title: "Failed to save settings",
          description: message || 'Please try again later.',
          variant: "destructive"
        });
      }
    } finally {
      setIsSaving(false);
    }
  }, [settings.darkMode, settings.editorTheme, settings.fontSize]);

  useEffect(() => {
    if (!hasLoadedRef.current || isLoading) {
      return;
    }
    if (persistTimerRef.current) {
      clearTimeout(persistTimerRef.current);
    }
    persistTimerRef.current = window.setTimeout(() => {
      persistEditorSettings().catch(() => {
        void 0;
      });
    }, 400);
    return () => {
      if (persistTimerRef.current) {
        clearTimeout(persistTimerRef.current);
      }
      if (hasLoadedRef.current && !isLoading) {
        persistEditorSettings().catch(() => {
          void 0;
        });
      }
    };
  }, [isLoading, persistEditorSettings]);

  const handleSaveEditorSettings = async () => {
    setIsSaving(true);
    try {
      const supportsEditorTheme = getStoredEditorThemeSupport();
      const payload: { font_size: number; editor_theme?: string; theme: string } = {
        font_size: Number(settings.fontSize),
        theme: settings.darkMode ? 'dark' : 'light',
      };
      if (supportsEditorTheme) {
        payload.editor_theme = settings.editorTheme;
      }
      const response = await settingsAPI.updateSettings(payload);
      try {
        localStorage.setItem(EDITOR_FONT_SIZE_KEY, String(settings.fontSize));
        localStorage.setItem(EDITOR_THEME_KEY, settings.editorTheme);
        localStorage.setItem(EDITOR_UPDATED_AT_KEY, response?.updated_at ?? new Date().toISOString());
      } catch {
        void 0;
      }
      toast({
        title: "Settings saved",
        description: "Your editor preferences have been updated successfully."
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : '';
      if (message.includes('Unknown settings: editor_theme')) {
        localStorage.setItem(SETTINGS_SUPPORTS_EDITOR_THEME_KEY, 'false');
        try {
          const response = await settingsAPI.updateSettings({
            font_size: Number(settings.fontSize),
            theme: settings.darkMode ? 'dark' : 'light',
          });
          localStorage.setItem(EDITOR_UPDATED_AT_KEY, response?.updated_at ?? new Date().toISOString());
          toast({
            title: "Settings saved",
            description: "Your editor preferences have been updated successfully."
          });
        } catch (innerError) {
          toast({
            title: "Failed to save settings",
            description: innerError instanceof Error ? innerError.message : 'Please try again later.',
            variant: "destructive"
          });
        }
      } else {
        toast({
          title: "Failed to save settings",
          description: message || 'Please try again later.',
          variant: "destructive"
        });
      }
    } finally {
      setIsSaving(false);
    }
  };

  const ensureCsrfToken = async () => {
    const stored = localStorage.getItem('csrf_token');
    if (stored) {
      return stored;
    }
    const data = await authAPI.getCsrfToken();
    return data.csrf_token;
  };

  const clearSessionData = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('csrf_token');
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
  };

  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast({
        title: "Missing fields",
        description: "Fill in current password and the new password twice.",
        variant: "destructive"
      });
      return;
    }
    if (newPassword !== confirmPassword) {
      toast({
        title: "Password mismatch",
        description: "New password and confirmation do not match.",
        variant: "destructive"
      });
      return;
    }
    setIsUpdatingPassword(true);
    try {
      await ensureCsrfToken();
      const response = await profileAPI.updatePassword({
        current_password: currentPassword,
        new_password: newPassword
      });
      if (response.csrf_token) {
        localStorage.setItem('csrf_token', response.csrf_token);
      }
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      clearSessionData();
      toast({
        title: "Password updated",
        description: "Please log in again with your new password."
      });
      navigate('/login');
    } catch (error) {
      toast({
        title: "Password update failed",
        description: error instanceof Error ? error.message : 'Please try again later.',
        variant: "destructive"
      });
    } finally {
      setIsUpdatingPassword(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (!deletePassword) {
      toast({
        title: "Password required",
        description: "Enter your password to delete the account.",
        variant: "destructive"
      });
      return;
    }
    setIsDeleting(true);
    try {
      await ensureCsrfToken();
      await profileAPI.deleteAccount({ password: deletePassword });
      setDeletePassword('');
      setIsDeleteDialogOpen(false);
      clearSessionData();
      toast({
        title: "Account deleted",
        description: "Your account has been removed successfully."
      });
      navigate('/');
    } catch (error) {
      toast({
        title: "Account deletion failed",
        description: error instanceof Error ? error.message : 'Please try again later.',
        variant: "destructive"
      });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <AppLayout>
      <div className="p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
              Settings
            </h1>
          </div>

          <div className="grid gap-6">
            {/* Editor Preferences */}
            <Card className="border-primary/20">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Code className="w-5 h-5 mr-2 text-primary" />
                  Editor Preferences
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="fontSize">Font Size</Label>
                    <Select value={settings.fontSize} onValueChange={(value) => updateSettings('fontSize', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="12">12px</SelectItem>
                        <SelectItem value="14">14px (Default)</SelectItem>
                        <SelectItem value="16">16px</SelectItem>
                        <SelectItem value="18">18px</SelectItem>
                        <SelectItem value="20">20px</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="editorTheme">Editor Theme</Label>
                    <Select value={settings.editorTheme} onValueChange={(value) => updateSettings('editorTheme', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {EDITOR_THEMES.map((theme) => (
                          <SelectItem key={theme.value} value={theme.value}>
                            {theme.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

              </CardContent>
            </Card>

            {/* Appearance */}
            <Card className="border-accent/20">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Palette className="w-5 h-5 mr-2 text-accent" />
                  Appearance
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="darkMode">Change Theme</Label>
                    <p className="text-sm text-muted-foreground">Switch between light and dark themes</p>
                  </div>
                  <div className="flex items-center">
                    <button
                      type="button"
                      id="darkMode"
                      role="switch"
                      aria-checked={settings.darkMode}
                      aria-label="Toggle theme"
                      disabled={isLoading}
                      onClick={() => {
                        const checked = !settings.darkMode;
                        updateSettings('darkMode', checked);
                        setTheme(checked ? 'dark' : 'light');
                      }}
                      className={`relative h-8 w-16 rounded-full border transition-all duration-300 disabled:opacity-60 disabled:cursor-not-allowed ${
                        settings.darkMode
                          ? 'bg-gradient-to-r from-slate-700 via-slate-800 to-slate-900 border-slate-500/60'
                          : 'bg-gradient-to-r from-sky-200 via-sky-100 to-amber-100 border-sky-300/80'
                      }`}
                    >
                      <span className={`absolute left-2 top-1.5 transition-opacity duration-300 ${settings.darkMode ? 'opacity-30' : 'opacity-100'}`}>
                        <Sun className="w-3.5 h-3.5 text-amber-500" />
                      </span>
                      <span className={`absolute right-2 top-1.5 transition-opacity duration-300 ${settings.darkMode ? 'opacity-100' : 'opacity-30'}`}>
                        <Moon className="w-3.5 h-3.5 text-indigo-200" />
                      </span>
                      <span
                        className={`absolute top-0.5 h-6 w-6 rounded-full border border-white/80 shadow-md transition-all duration-300 flex items-center justify-center ${
                          settings.darkMode
                            ? 'left-[2.1rem] bg-slate-950'
                            : 'left-0.5 bg-white'
                        }`}
                      >
                        {settings.darkMode ? (
                          <Moon className="w-3.5 h-3.5 text-indigo-200" />
                        ) : (
                          <Sun className="w-3.5 h-3.5 text-amber-500" />
                        )}
                      </span>
                    </button>
                  </div>
                </div>

                
              </CardContent>
            </Card>

            {/* Notifications */}
            <Card className="border-secondary/20">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Bell className="w-5 h-5 mr-2 text-secondary" />
                  Notifications
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="emailNotifications">Email Notifications</Label>
                    <p className="text-sm text-muted-foreground">Receive updates via email</p>
                  </div>
                  <Switch 
                    id="emailNotifications"
                    checked={settings.emailNotifications}
                    onCheckedChange={(checked) => updateSettings('emailNotifications', checked)}
                    disabled={isLoading}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="streakReminders">Streak Reminders</Label>
                    <p className="text-sm text-muted-foreground">Daily reminders to maintain your streak</p>
                  </div>
                  <Switch 
                    id="streakReminders"
                    checked={settings.streakReminders}
                    onCheckedChange={(checked) => updateSettings('streakReminders', checked)}
                    disabled={isLoading}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Account Management */}
            <Card className="border-destructive/20">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Shield className="w-5 h-5 mr-2 text-destructive" />
                  Account Management
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="currentPassword" className="text-base font-medium">Change Password</Label>
                    <p className="text-sm text-muted-foreground mb-4">Update your password to keep your account secure</p>
                    
                    <div className="space-y-3">
                      <div>
                        <Label htmlFor="currentPassword">Current Password</Label>
                        <Input 
                          id="currentPassword"
                          type="password" 
                          placeholder="Enter current password"
                          value={currentPassword}
                          onChange={(event) => setCurrentPassword(event.target.value)}
                          disabled={isUpdatingPassword}
                        />
                      </div>
                      <div>
                        <Label htmlFor="newPassword">New Password</Label>
                        <Input 
                          id="newPassword"
                          type="password" 
                          placeholder="Enter new password"
                          value={newPassword}
                          onChange={(event) => setNewPassword(event.target.value)}
                          disabled={isUpdatingPassword}
                        />
                      </div>
                      <div>
                        <Label htmlFor="confirmPassword">Confirm New Password</Label>
                        <Input 
                          id="confirmPassword"
                          type="password" 
                          placeholder="Confirm new password"
                          value={confirmPassword}
                          onChange={(event) => setConfirmPassword(event.target.value)}
                          disabled={isUpdatingPassword}
                        />
                      </div>
                      <Button onClick={handleChangePassword} className="bg-primary" disabled={isUpdatingPassword}>
                        {isUpdatingPassword ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Updating...
                          </>
                        ) : (
                          'Update Password'
                        )}
                      </Button>
                    </div>
                  </div>

                  <Separator />

                  <div>
                    <Label className="text-base font-medium text-destructive">Danger Zone</Label>
                    <p className="text-sm text-muted-foreground mb-4">
                      Once you delete your account, there is no going back. Please be certain.
                    </p>
                    
                    <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
                      <AlertDialogTrigger asChild>
                        <Button 
                          variant="destructive" 
                          className="bg-destructive hover:bg-destructive/90"
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          Delete Account
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Delete account</AlertDialogTitle>
                          <AlertDialogDescription>
                            This permanently deletes your account and data. Enter your password to confirm.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <div className="space-y-2">
                          <Label htmlFor="deleteAccountPassword">Password</Label>
                          <Input
                            id="deleteAccountPassword"
                            type="password"
                            placeholder="Enter your password"
                            value={deletePassword}
                            onChange={(event) => setDeletePassword(event.target.value)}
                            disabled={isDeleting}
                          />
                        </div>
                        <AlertDialogFooter>
                          <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
                          <AlertDialogAction onClick={handleDeleteAccount} disabled={isDeleting}>
                            {isDeleting ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Deleting...
                              </>
                            ) : (
                              'Delete Account'
                            )}
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Save Button */}
            <div className="flex justify-end">
              <Button onClick={handleSaveEditorSettings} className="bg-gradient-primary" disabled={isLoading || isSaving}>
                <Save className="w-4 h-4 mr-2" />
                {isSaving ? 'Saving...' : 'Save Settings'}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
};

export default Settings;
