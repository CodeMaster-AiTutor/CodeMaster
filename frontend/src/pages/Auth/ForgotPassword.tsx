import React, { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Code2, Mail, Lock, Eye, EyeOff, ArrowLeft, AlertCircle, KeyRound, CheckCircle2, Loader2 } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import { authAPI } from '@/lib/api';

const ForgotPassword = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [step, setStep] = useState<'request' | 'reset' | 'success'>('request');
  const [isLoading, setIsLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [cooldownSeconds, setCooldownSeconds] = useState(0);
  const [otpDigits, setOtpDigits] = useState<string[]>(['', '', '', '', '', '']);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formData, setFormData] = useState({
    email: '',
    otp: '',
    newPassword: '',
    confirmPassword: '',
  });
  const navigate = useNavigate();
  const { toast } = useToast();
  const otpRefs = useRef<Array<HTMLInputElement | null>>([]);

  useEffect(() => {
    if (cooldownSeconds <= 0) return;
    const id = window.setInterval(() => {
      setCooldownSeconds((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => window.clearInterval(id);
  }, [cooldownSeconds]);

  const validateRequest = () => {
    const next: Record<string, string> = {};
    if (!formData.email) next.email = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(formData.email)) next.email = 'Please enter a valid email';
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const validateReset = () => {
    const next: Record<string, string> = {};
    if (!formData.otp || formData.otp.length !== 6) next.otp = 'Enter 6-digit OTP';
    if (!formData.newPassword.trim()) next.newPassword = 'New password is required';
    else if (formData.newPassword !== formData.newPassword.trim()) next.newPassword = 'Password cannot be blank or start/end with spaces';
    if (!formData.confirmPassword) next.confirmPassword = 'Confirm your password';
    if (formData.newPassword && formData.confirmPassword && formData.newPassword !== formData.confirmPassword) {
      next.confirmPassword = 'Passwords do not match';
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleOtpDigitChange = (index: number, value: string) => {
    const digit = value.replace(/\D/g, '').slice(-1);
    const nextDigits = [...otpDigits];
    nextDigits[index] = digit;
    setOtpDigits(nextDigits);
    setFormData((prev) => ({ ...prev, otp: nextDigits.join('') }));
    if (digit && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Backspace' && !otpDigits[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  const handleOtpPaste = (event: React.ClipboardEvent<HTMLInputElement>) => {
    event.preventDefault();
    const pastedDigits = event.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6).split('');
    if (!pastedDigits.length) {
      return;
    }
    const nextDigits = ['','','','','',''];
    for (let i = 0; i < pastedDigits.length; i += 1) {
      nextDigits[i] = pastedDigits[i];
    }
    setOtpDigits(nextDigits);
    setFormData((prev) => ({ ...prev, otp: nextDigits.join('') }));
    const focusIndex = Math.min(pastedDigits.length, 5);
    otpRefs.current[focusIndex]?.focus();
  };

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateRequest()) return;
    setIsLoading(true);
    try {
      const result = await authAPI.requestForgotPasswordOtp({ email: formData.email.trim().toLowerCase() });
      setStep('reset');
      setCooldownSeconds(60);
      if (result.delivery_failed && result.dev_otp) {
        const nextDigits = result.dev_otp.split('').slice(0, 6);
        const filled = ['','','','','',''];
        for (let i = 0; i < nextDigits.length; i += 1) filled[i] = nextDigits[i];
        setOtpDigits(filled);
        setFormData((prev) => ({ ...prev, otp: filled.join('') }));
        toast({ title: 'OTP generated (dev mode)', description: `Email failed; use OTP: ${result.dev_otp}` });
      } else {
        toast({ title: 'OTP sent', description: 'Check your email for the OTP.' });
      }
    } catch (error) {
      toast({
        title: 'Failed to send OTP',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOtp = async () => {
    if (!formData.email || cooldownSeconds > 0) return;
    setIsResending(true);
    try {
      const result = await authAPI.requestForgotPasswordOtp({ email: formData.email.trim().toLowerCase() });
      setCooldownSeconds(60);
      if (result.delivery_failed && result.dev_otp) {
        const nextDigits = result.dev_otp.split('').slice(0, 6);
        const filled = ['','','','','',''];
        for (let i = 0; i < nextDigits.length; i += 1) filled[i] = nextDigits[i];
        setOtpDigits(filled);
        setFormData((prev) => ({ ...prev, otp: filled.join('') }));
        toast({ title: 'OTP regenerated (dev mode)', description: `Email failed; use OTP: ${result.dev_otp}` });
      } else {
        toast({ title: 'OTP resent', description: 'A new OTP has been sent to your email.' });
      }
    } catch (error) {
      toast({
        title: 'Failed to resend OTP',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsResending(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateReset()) return;
    setIsLoading(true);
    try {
      await authAPI.resetPasswordWithOtp({
        email: formData.email.trim().toLowerCase(),
        otp: formData.otp.trim(),
        new_password: formData.newPassword.trim(),
      });
      setStep('success');
      toast({ title: 'Password updated', description: 'Your password has been changed successfully.' });
    } catch (error) {
      toast({
        title: 'Password reset failed',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row">
      <div className="lg:w-1/2 bg-gradient-to-br from-primary to-accent flex items-center justify-center p-8">
        <div className="text-center text-white max-w-md">
          <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-6 animate-float">
            <Code2 className="w-8 h-8" />
          </div>
          <h1 className="text-3xl font-bold mb-4">Reset Your Password</h1>
          <p className="text-white/80 text-lg leading-relaxed">Secure OTP-based reset flow to recover your CodeMaster account.</p>
        </div>
      </div>

      <div className="lg:w-1/2 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <div className="mb-8">
            <Link to="/login" className="inline-flex items-center text-muted-foreground hover:text-foreground mb-6">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Login
            </Link>
            <h2 className="text-3xl font-bold mb-2">Forgot Password</h2>
            <p className="text-muted-foreground">
              {step === 'request' ? 'Enter your email to receive OTP' : step === 'reset' ? 'Enter OTP and set a new password' : 'Password reset complete'}
            </p>
          </div>

          <Card className="card-glass p-6">
            {step === 'request' ? (
              <form onSubmit={handleRequestOtp} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      id="email"
                      type="email"
                      className="pl-10"
                      value={formData.email}
                      onChange={(e) => setFormData((prev) => ({ ...prev, email: e.target.value }))}
                      placeholder="Enter your registered email"
                    />
                  </div>
                  {errors.email ? (
                    <Alert variant="destructive" className="py-2">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription className="text-sm">{errors.email}</AlertDescription>
                    </Alert>
                  ) : null}
                </div>
                <Button type="submit" className="w-full btn-primary text-white" disabled={isLoading}>
                  {isLoading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Sending OTP...</> : 'Send OTP'}
                </Button>
              </form>
            ) : null}

            {step === 'reset' ? (
              <form onSubmit={handleResetPassword} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="otp">OTP</Label>
                  <div className="flex items-center gap-2">
                    <KeyRound className="w-4 h-4 text-muted-foreground" />
                    <div className="flex gap-2">
                      {otpDigits.map((digit, index) => (
                        <Input
                          key={index}
                          ref={(element) => { otpRefs.current[index] = element; }}
                          type="text"
                          inputMode="numeric"
                          maxLength={1}
                          className="w-11 h-11 text-center text-lg"
                          value={digit}
                          onChange={(e) => handleOtpDigitChange(index, e.target.value)}
                          onKeyDown={(e) => handleOtpKeyDown(index, e)}
                          onPaste={handleOtpPaste}
                        />
                      ))}
                    </div>
                  </div>
                  {errors.otp ? <p className="text-sm text-destructive">{errors.otp}</p> : null}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="new-password">New Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      id="new-password"
                      type={showPassword ? 'text' : 'password'}
                      className="pl-10 pr-10"
                      value={formData.newPassword}
                      onChange={(e) => setFormData((prev) => ({ ...prev, newPassword: e.target.value }))}
                      placeholder="Create new password"
                    />
                    <button type="button" className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground" onClick={() => setShowPassword((v) => !v)}>
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {errors.newPassword ? <p className="text-sm text-destructive">{errors.newPassword}</p> : null}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirm-password">Confirm Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      id="confirm-password"
                      type={showConfirmPassword ? 'text' : 'password'}
                      className="pl-10 pr-10"
                      value={formData.confirmPassword}
                      onChange={(e) => setFormData((prev) => ({ ...prev, confirmPassword: e.target.value }))}
                      placeholder="Confirm new password"
                    />
                    <button type="button" className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground" onClick={() => setShowConfirmPassword((v) => !v)}>
                      {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {errors.confirmPassword ? <p className="text-sm text-destructive">{errors.confirmPassword}</p> : null}
                </div>
                <div className="flex gap-3">
                  <Button type="button" variant="outline" className="w-1/2" onClick={() => setStep('request')} disabled={isLoading}>
                    Back
                  </Button>
                  <Button type="submit" className="w-1/2 btn-primary text-white" disabled={isLoading}>
                    {isLoading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Updating...</> : 'Change Password'}
                  </Button>
                </div>
                <div className="text-center">
                  <Button
                    type="button"
                    variant="ghost"
                    className="text-primary"
                    onClick={handleResendOtp}
                    disabled={isResending || cooldownSeconds > 0 || isLoading}
                  >
                    {isResending ? 'Resending OTP...' : cooldownSeconds > 0 ? `Resend OTP in ${cooldownSeconds}s` : 'Resend OTP'}
                  </Button>
                </div>
              </form>
            ) : null}

            {step === 'success' ? (
              <div className="text-center space-y-6">
                <CheckCircle2 className="w-12 h-12 text-green-400 mx-auto" />
                <p className="text-muted-foreground">Password changed successfully. You can login with your new password.</p>
                <Button className="w-full btn-primary text-white" onClick={() => navigate('/login')}>
                  Go to Login
                </Button>
              </div>
            ) : null}
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
