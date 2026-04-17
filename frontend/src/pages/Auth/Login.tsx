import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Code2, 
  Mail, 
  Lock, 
  Eye, 
  EyeOff,
  Github,
  Chrome,
  ArrowLeft,
  AlertCircle
} from 'lucide-react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import { authAPI } from '@/lib/api';
import { Loader2 } from 'lucide-react';

const Login = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  useEffect(() => {
    const email = (searchParams.get('email') || '').trim().toLowerCase();
    const verified = (searchParams.get('verified') || '').trim() === '1';
    const verifyPending = (searchParams.get('verify_pending') || '').trim() === '1';
    const prefillPassword = sessionStorage.getItem('login_prefill_password') || '';
    if (email) {
      setFormData((prev) => ({ ...prev, email }));
    }
    if (prefillPassword) {
      setFormData((prev) => ({ ...prev, password: prefillPassword }));
      sessionStorage.removeItem('login_prefill_password');
    } else if (email) {
      const pendingRaw = sessionStorage.getItem('pending_signup_credentials');
      if (pendingRaw) {
        try {
          const pending = JSON.parse(pendingRaw) as { email?: string; password?: string; expiresAt?: number };
          const expiresAt = Number(pending.expiresAt || 0);
          if (pending.email?.toLowerCase() === email && pending.password && expiresAt > Date.now()) {
            setFormData((prev) => ({ ...prev, password: pending.password || '' }));
          }
        } catch {
          void 0;
        }
      }
    }
    if (verified) {
      toast({
        title: "Email verified",
        description: "You can now log in to your account.",
      });
    } else if (verifyPending && email) {
      toast({
        title: "Verify your email",
        description: "Open your inbox and click the verification link to activate login.",
      });
    }
  }, [searchParams, toast]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setIsLoading(true);
    
    try {
      // Call backend API for login
      const response = await authAPI.login({
        email: formData.email,
        password: formData.password
      });
      
      toast({
        title: "Welcome back!",
        description: `Successfully logged in as ${response.user.username}.`,
      });
      sessionStorage.removeItem('pending_signup_credentials');
      
      // Navigate to dashboard
      navigate('/dashboard');
    } catch (error) {
      toast({
        title: "Login failed",
        description: error instanceof Error ? error.message : 'Please check your credentials and try again.',
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSocialLogin = async (provider: string) => {
    if (provider === 'Google') {
      try {
        setIsLoading(true);
        const response = await authAPI.getGoogleAuthUrl();
        
        // Store state in sessionStorage for verification
        sessionStorage.setItem('google_oauth_state', response.state);
        
        // Redirect to Google OAuth
        window.location.href = response.auth_url;
      } catch (error) {
        setIsLoading(false);
        toast({
          title: "Google Login Failed",
          description: error instanceof Error ? error.message : 'Failed to initiate Google login.',
          variant: "destructive",
        });
      }
    } else if (provider === 'GitHub') {
      try {
        setIsLoading(true);
        const response = await authAPI.getGithubAuthUrl();
        sessionStorage.setItem('github_oauth_state', response.state);
        window.location.href = response.auth_url;
      } catch (error) {
        setIsLoading(false);
        toast({
          title: "GitHub Login Failed",
          description: error instanceof Error ? error.message : 'Failed to initiate GitHub login.',
          variant: "destructive",
        });
      }
    } else {
      toast({
        title: `${provider} Login`,
        description: "Social login will be available soon!",
      });
    }
  };

  return (
    <div className="min-h-screen lg:h-screen flex flex-col lg:flex-row lg:overflow-hidden">
      {/* Left Side - Branding */}
      <div className="relative overflow-hidden lg:w-1/2 lg:h-screen bg-gradient-to-br from-primary to-accent flex items-center justify-center p-8">
        <div className="auth-grid-shimmer" />
        <div className="auth-blob w-40 h-40 bg-white/30 top-16 left-12" />
        <div className="auth-blob w-52 h-52 bg-accent/40 bottom-20 right-10 [animation-delay:1.8s]" />
        <div className="auth-blob w-28 h-28 bg-white/20 top-1/2 right-1/4 [animation-delay:0.9s]" />
        <div className="relative text-center text-white max-w-md">
          <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-6 animate-float">
            <Code2 className="w-8 h-8" />
          </div>
          <h1 className="text-3xl font-bold mb-4">Welcome Back to CodeMaster</h1>
          <p className="text-white/80 text-lg leading-relaxed">
            Continue your coding journey with AI-powered learning tools and interactive challenges.
          </p>
          <div className="mt-8 grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">10K+</div>
              <div className="text-white/60 text-sm">Active Users</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">50+</div>
              <div className="text-white/60 text-sm">Challenges</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">95%</div>
              <div className="text-white/60 text-sm">Success Rate</div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="lg:w-1/2 lg:h-screen overflow-y-auto">
        <div className="min-h-screen lg:min-h-full flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <div className="mb-8">
            <Link to="/" className="inline-flex items-center text-muted-foreground hover:text-foreground mb-6">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Link>
            
            <h2 className="text-3xl font-bold mb-2">Sign In</h2>
            <p className="text-muted-foreground">
              Enter your credentials to access your account
            </p>
          </div>

          <Card className="card-glass p-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Email Field */}
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-medium">
                  Email Address
                </Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="Enter your email"
                    className="pl-10"
                    value={formData.email}
                    onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  />
                </div>
                {errors.email && (
                  <Alert variant="destructive" className="py-2">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription className="text-sm">{errors.email}</AlertDescription>
                  </Alert>
                )}
              </div>

              {/* Password Field */}
              <div className="space-y-2">
                <Label htmlFor="password" className="text-sm font-medium">
                  Password
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Enter your password"
                    className="pl-10 pr-10"
                    value={formData.password}
                    onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.password && (
                  <Alert variant="destructive" className="py-2">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription className="text-sm">{errors.password}</AlertDescription>
                  </Alert>
                )}
              </div>

              {/* Forgot Password */}
              <div className="flex justify-end">
                <Link 
                  to="/forgot-password" 
                  className="text-sm text-primary hover:text-primary/80 transition-colors"
                >
                  Forgot your password?
                </Link>
              </div>

              {/* Submit Button */}
              <Button 
                type="submit" 
                className="w-full btn-primary text-white" 
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Signing In...
                  </>
                ) : (
                  'Sign In'
                )}
              </Button>
            </form>

            {/* Divider */}
            <div className="my-6">
              <Separator className="relative">
                <span className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-card px-2 text-sm text-muted-foreground">
                  Or continue with
                </span>
              </Separator>
            </div>

            {/* Social Login */}
            <div className="grid grid-cols-2 gap-4">
              <Button 
                variant="outline" 
                onClick={() => handleSocialLogin('Google')}
                className="w-full"
              >
                <Chrome className="w-4 h-4 mr-2" />
                Google
              </Button>
              <Button 
                variant="outline" 
                onClick={() => handleSocialLogin('GitHub')}
                className="w-full"
              >
                <Github className="w-4 h-4 mr-2" />
                GitHub
              </Button>
            </div>

            {/* Sign Up Link */}
            <div className="mt-6 text-center">
              <p className="text-muted-foreground">
                Don't have an account?{' '}
                <Link to="/signup" className="text-primary hover:text-primary/80 font-medium transition-colors">
                  Sign up for free
                </Link>
              </p>
            </div>
          </Card>
        </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
