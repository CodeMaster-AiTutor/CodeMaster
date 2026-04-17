import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Code2, Loader2 } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import { profileAPI } from '@/lib/api';

const SocialOnboarding = () => {
  const [searchParams] = useSearchParams();
  const provider = (searchParams.get('provider') || 'social').toLowerCase();
  const [skillLevel, setSkillLevel] = useState<'beginner' | 'intermediate' | 'advanced'>('beginner');
  const [isSaving, setIsSaving] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleContinue = async () => {
    setIsSaving(true);
    try {
      const updated = await profileAPI.updateProfile({ skill_level: skillLevel });
      try {
        const stored = localStorage.getItem('user');
        if (stored) {
          const current = JSON.parse(stored) as Record<string, unknown>;
          localStorage.setItem('user', JSON.stringify({ ...current, skill_level: updated.skill_level }));
        }
      } catch {
        void 0;
      }
      toast({
        title: 'Profile setup complete',
        description: 'Your skill level is set. Let’s continue to dashboard.',
      });
      navigate('/dashboard');
    } catch (error) {
      toast({
        title: 'Unable to save level',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row">
      <div className="lg:w-1/2 bg-gradient-to-br from-primary to-accent flex items-center justify-center p-8">
        <div className="text-center text-white max-w-md">
          <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-6 animate-float">
            <Code2 className="w-8 h-8" />
          </div>
          <h1 className="text-3xl font-bold mb-4">One Last Step</h1>
          <p className="text-white/80 text-lg leading-relaxed">
            Welcome from {provider === 'google' ? 'Google' : provider === 'github' ? 'GitHub' : 'social login'}. Choose your current skill level to personalize your learning path.
          </p>
        </div>
      </div>
      <div className="lg:w-1/2 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <Card className="card-glass p-6 space-y-6">
            <div>
              <h2 className="text-3xl font-bold mb-2">Select Skill Level</h2>
              <p className="text-muted-foreground">You can change this later from your profile settings.</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="social-onboarding-skill-level">Programming Skill Level</Label>
              <Select value={skillLevel} onValueChange={(value) => setSkillLevel(value as 'beginner' | 'intermediate' | 'advanced')}>
                <SelectTrigger id="social-onboarding-skill-level">
                  <SelectValue placeholder="Select your skill level" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="beginner">Beginner - New to programming</SelectItem>
                  <SelectItem value="intermediate">Intermediate - Some experience</SelectItem>
                  <SelectItem value="advanced">Advanced - Experienced developer</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button className="w-full btn-primary text-white" onClick={handleContinue} disabled={isSaving}>
              {isSaving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                'Continue to Dashboard'
              )}
            </Button>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default SocialOnboarding;
