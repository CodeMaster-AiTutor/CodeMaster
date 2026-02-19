import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Code, User, Shield, Trash2, Palette, Sun, Moon, Bell, Save } from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import AppLayout from '@/components/layout/AppLayout';
import { settingsAPI } from '@/lib/api';
import { useTheme } from 'next-themes';

const EDITOR_FONT_SIZE_KEY = 'settings:editor-font-size';
const EDITOR_THEME_KEY = 'settings:editor-theme';
const EDITOR_UPDATED_AT_KEY = 'settings:editor-updated-at';
const SETTINGS_SUPPORTS_EDITOR_THEME_KEY = 'settings:supports-editor-theme';
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

const Settings = () => {
  const { setTheme } = useTheme();
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const hasLoadedRef = useRef(false);
  const persistTimerRef = useRef<number | null>(null);
  const [settings, setSettings] = useState(() => ({
    fontSize: getStoredEditorFontSize(),
    editorTheme: getStoredEditorTheme(),
    darkMode: true,
    emailNotifications: true,
    pushNotifications: false,
    streakReminders: true
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
  };

  useEffect(() => {
    const loadSettings = async () => {
      setIsLoading(true);
      try {
        const data = await settingsAPI.getSettings();
        const darkMode = data.theme !== 'light';
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
          setTheme(darkMode ? 'dark' : 'light');
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
          setTheme(darkMode ? 'dark' : 'light');
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
  }, [setTheme]);

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

  const handleChangePassword = () => {
    toast({
      title: "Password change",
      description: "Password change functionality will be implemented with backend integration."
    });
  };

  const handleDeleteAccount = () => {
    toast({
      title: "Account deletion",
      description: "This feature requires backend integration to implement safely.",
      variant: "destructive"
    });
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
                    <Label htmlFor="darkMode">Dark Mode</Label>
                    <p className="text-sm text-muted-foreground">Switch between light and dark themes</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Sun className="w-4 h-4" />
                    <Switch 
                      id="darkMode"
                      checked={settings.darkMode}
                      onCheckedChange={(checked) => {
                        updateSettings('darkMode', checked);
                        setTheme(checked ? 'dark' : 'light');
                      }}
                      disabled={isLoading}
                    />
                    <Moon className="w-4 h-4" />
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
                    <Label htmlFor="pushNotifications">Push Notifications</Label>
                    <p className="text-sm text-muted-foreground">Get browser notifications</p>
                  </div>
                  <Switch 
                    id="pushNotifications"
                    checked={settings.pushNotifications}
                    onCheckedChange={(checked) => updateSettings('pushNotifications', checked)}
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
                        />
                      </div>
                      <div>
                        <Label htmlFor="newPassword">New Password</Label>
                        <Input 
                          id="newPassword"
                          type="password" 
                          placeholder="Enter new password"
                        />
                      </div>
                      <div>
                        <Label htmlFor="confirmPassword">Confirm New Password</Label>
                        <Input 
                          id="confirmPassword"
                          type="password" 
                          placeholder="Confirm new password"
                        />
                      </div>
                      <Button onClick={handleChangePassword} className="bg-primary">
                        Update Password
                      </Button>
                    </div>
                  </div>

                  <Separator />

                  <div>
                    <Label className="text-base font-medium text-destructive">Danger Zone</Label>
                    <p className="text-sm text-muted-foreground mb-4">
                      Once you delete your account, there is no going back. Please be certain.
                    </p>
                    
                    <Button 
                      variant="destructive" 
                      onClick={handleDeleteAccount}
                      className="bg-destructive hover:bg-destructive/90"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete Account
                    </Button>
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
