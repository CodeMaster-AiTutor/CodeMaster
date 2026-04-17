import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Mail, RefreshCcw } from 'lucide-react';
import { authAPI } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

const VerifyPending = () => {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const email = useMemo(() => (params.get('email') || '').trim().toLowerCase(), [params]);
  const [deadline, setDeadline] = useState<number>(() => Date.now() + 10 * 60 * 1000);
  const [resending, setResending] = useState(false);

  useEffect(() => {
    if (!email) {
      navigate('/signup');
      return;
    }
    const stored = sessionStorage.getItem('pending_signup_credentials');
    if (stored) {
      try {
        const pending = JSON.parse(stored) as { email?: string; expiresAt?: number };
        if (pending.email?.toLowerCase() === email && Number(pending.expiresAt || 0) > Date.now()) {
          setDeadline(Number(pending.expiresAt));
        }
      } catch {
        void 0;
      }
    }
  }, [email, navigate]);

  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);

  const remainingMs = Math.max(0, deadline - now);
  const mins = Math.floor(remainingMs / 60000);
  const secs = Math.floor((remainingMs % 60000) / 1000);
  const expired = remainingMs <= 0;

  const handleResend = async () => {
    if (!email) {
      return;
    }
    setResending(true);
    try {
      const result = await authAPI.resendVerification({ email });
      const nextDeadline = Date.now() + (Number(result.expires_in_seconds || 600) * 1000);
      setDeadline(nextDeadline);
      const pendingRaw = sessionStorage.getItem('pending_signup_credentials');
      if (pendingRaw) {
        try {
          const pending = JSON.parse(pendingRaw) as { email?: string; password?: string; expiresAt?: number };
          sessionStorage.setItem('pending_signup_credentials', JSON.stringify({
            ...pending,
            email,
            expiresAt: nextDeadline
          }));
        } catch {
          void 0;
        }
      }
      toast({ title: 'Verification email sent', description: 'Check your inbox for a new verification link.' });
    } catch (error) {
      toast({
        title: 'Resend failed',
        description: error instanceof Error ? error.message : 'Unable to resend verification email.',
        variant: 'destructive'
      });
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-background">
      <Card className="w-full max-w-xl p-8 card-glass">
        <div className="flex flex-col items-center text-center gap-4">
          <Mail className="w-9 h-9 text-primary" />
          <h1 className="text-2xl font-semibold">Verify your email</h1>
          <p className="text-muted-foreground">We sent a verification link to <span className="text-foreground">{email}</span>.</p>
          {!expired ? (
            <p className="text-sm text-amber-300">Link expires in {mins}:{secs.toString().padStart(2, '0')}</p>
          ) : (
            <p className="text-sm text-red-300">Verification link expired. Please resend.</p>
          )}
          <div className="flex gap-3 pt-2">
            <Button onClick={handleResend} disabled={resending} className="btn-primary text-white">
              <RefreshCcw className="w-4 h-4 mr-2" />
              {resending ? 'Resending...' : 'Resend Verification'}
            </Button>
            <Button variant="outline" onClick={() => navigate('/signup')}>Back to Signup</Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default VerifyPending;
