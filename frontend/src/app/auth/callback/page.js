'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { supabase } from '@/lib/supabase';
import { API_BASE } from '@/lib/constants';
import { Loader2 } from 'lucide-react';
import styles from '@/app/auth.module.css';

export default function AuthCallbackPage() {
  const router = useRouter();
  const { setUser: _setUser } = useAuth();
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;

    const processCallback = async () => {
      // Supabase parses URL hash automatically and sets session
      const { data: { session }, error: sessionError } = await supabase.auth.getSession();

      if (sessionError || !session) {
        if (mounted) setError('Failed to authenticate with Google.');
        setTimeout(() => router.push('/login'), 3000);
        return;
      }

      try {
        // Call backend directly WITHOUT the Authorization header.
        // The new user doesn't exist in Django yet, so the auth middleware
        // would fail to look them up. We pass the token in the request body instead.
        const response = await fetch(`${API_BASE}/auth/oauth/callback/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ access_token: session.access_token }),
        });

        const data = await response.json();

        if (!response.ok) {
          if (mounted) setError(data.error || 'OAuth login failed.');
          setTimeout(() => router.push('/login'), 3000);
          return;
        }

        if (data.next_step === 'verify_phone') {
          window.location.href = '/verify-phone';
        } else if (data.user) {
          // Fully verified returning user — hard redirect so AuthContext re-inits
          window.location.href = '/browse';
        } else {
          window.location.href = '/browse';
        }
      } catch (err) {
        if (mounted) setError('Network error. Please try again.');
        setTimeout(() => router.push('/login'), 3000);
      }
    };

    // Give Supabase a moment to parse the hash from the URL
    setTimeout(processCallback, 500);

    return () => { mounted = false; };
  }, [router]);

  return (
    <div className={styles.page}>
      <div className={styles.card} style={{ textAlign: 'center', padding: '48px 24px' }}>
        {error ? (
          <div>
            <h3 className="heading-md" style={{ color: 'var(--color-danger)' }}>{error}</h3>
            <p className="text-muted" style={{ marginTop: 8 }}>Redirecting back to login...</p>
          </div>
        ) : (
          <div>
            <Loader2 size={40} className="spinner" style={{ margin: '0 auto', color: 'var(--color-accent)' }} />
            <h3 className="heading-md" style={{ marginTop: 16 }}>Authenticating...</h3>
            <p className="text-muted">Please wait while we set up your account.</p>
          </div>
        )}
      </div>
      <style jsx global>{`
        .spinner {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
