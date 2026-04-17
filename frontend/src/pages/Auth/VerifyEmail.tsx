import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { authAPI } from '@/lib/api';

const VerifyEmail = () => {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Verifying your email...');

  useEffect(() => {
    const token = (params.get('token') || '').trim();
    const email = (params.get('email') || '').trim().toLowerCase();
    if (!token || !email) {
      setStatus('error');
      setMessage('Invalid verification link.');
      return;
    }
    const run = async () => {
      try {
        const result = await authAPI.verifyEmail({ email, token });
        setStatus('success');
        setMessage(result.message || 'Email verified successfully.');
        const pendingRaw = sessionStorage.getItem('pending_signup_credentials');
        let password = '';
        if (pendingRaw) {
          try {
            const pending = JSON.parse(pendingRaw) as { email?: string; password?: string; expiresAt?: number };
            const expiresAt = Number(pending.expiresAt || 0);
            if (pending.email?.toLowerCase() === email && pending.password && expiresAt > Date.now()) {
              password = pending.password;
            }
          } catch {
            void 0;
          }
        }
        if (password) {
          sessionStorage.setItem('login_prefill_password', password);
        }
        const query = new URLSearchParams({ email, verified: '1' });
        window.setTimeout(() => navigate(`/login?${query.toString()}`), 1200);
      } catch (error) {
        setStatus('error');
        setMessage(error instanceof Error ? error.message : 'Email verification failed.');
      }
    };
    void run();
  }, [navigate, params]);

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-background">
      <Card className="w-full max-w-lg p-8 card-glass">
        <div className="flex flex-col items-center text-center gap-4">
          {status === 'loading' ? <Loader2 className="w-8 h-8 animate-spin text-primary" /> : null}
          {status === 'success' ? <CheckCircle2 className="w-8 h-8 text-green-400" /> : null}
          {status === 'error' ? <XCircle className="w-8 h-8 text-red-400" /> : null}
          <h1 className="text-2xl font-semibold">Email Verification</h1>
          <p className="text-muted-foreground">{message}</p>
          {status === 'error' ? (
            <Button onClick={() => navigate('/login')} className="btn-primary text-white">
              Go to Login
            </Button>
          ) : null}
        </div>
      </Card>
    </div>
  );
};

export default VerifyEmail;
