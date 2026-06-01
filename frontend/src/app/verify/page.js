'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/context/ToastContext';
import { ShieldCheck, RefreshCw } from 'lucide-react';
import styles from '../auth.module.css';

export default function VerifyPage() {
  const [emailOtp, setEmailOtp] = useState('');
  const [phoneOtp, setPhoneOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const { user, verifyOtp, resendOtp } = useAuth();
  const { toast } = useToast();
  const router = useRouter();
  const timerRef = useRef(null);

  // Cooldown timer
  useEffect(() => {
    if (resendCooldown > 0) {
      timerRef.current = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000);
    }
    return () => clearTimeout(timerRef.current);
  }, [resendCooldown]);

  const handleVerify = async (e) => {
    e.preventDefault();

    if (emailOtp.length !== 6 || phoneOtp.length !== 6) {
      toast.error('Please enter both 6-digit OTPs.');
      return;
    }

    setLoading(true);
    const { data, error } = await verifyOtp(emailOtp, phoneOtp);
    setLoading(false);

    if (error) {
      if (typeof error === 'object') {
        const messages = Object.values(error).flat().join(', ');
        toast.error(messages);
      } else {
        toast.error(error);
      }
      return;
    }

    toast.success('Verified successfully!');
    router.push('/browse');
  };

  const handleResend = async (type) => {
    const { error } = await resendOtp(type);
    if (error) {
      toast.error('Failed to resend OTP.');
      return;
    }
    toast.success(`OTP resent to your ${type === 'email' ? 'email' : type === 'phone' ? 'phone' : 'email and phone'}.`);
    setResendCooldown(60);
  };

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.header}>
          <div className={styles.verifyIcon}>
            <ShieldCheck size={32} />
          </div>
          <h1 className={styles.title}>Verify your account</h1>
          <p className={styles.subtitle}>
            We sent verification codes to your email and phone number.
            Enter them below to activate your account.
          </p>
        </div>

        <form onSubmit={handleVerify} className={styles.form}>
          <div className="form-group">
            <label className="form-label" htmlFor="email-otp">Email OTP</label>
            <input
              type="text"
              id="email-otp"
              className="form-input"
              placeholder="Enter 6-digit code"
              value={emailOtp}
              onChange={(e) => setEmailOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
              maxLength={6}
              inputMode="numeric"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="phone-otp">Phone OTP</label>
            <input
              type="text"
              id="phone-otp"
              className="form-input"
              placeholder="Enter 6-digit code"
              value={phoneOtp}
              onChange={(e) => setPhoneOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
              maxLength={6}
              inputMode="numeric"
            />
          </div>

          <button
            type="submit"
            className="btn btn--primary btn--full btn--lg"
            disabled={loading}
            id="verify-submit-btn"
          >
            {loading ? 'Verifying…' : 'Verify Account'}
          </button>
        </form>

        <div className={styles.resendWrap}>
          <p className="text-sm text-muted">Didn&apos;t receive the code?</p>
          <button
            className={`btn btn--ghost btn--sm ${styles.resendBtn}`}
            onClick={() => handleResend('both')}
            disabled={resendCooldown > 0}
            id="resend-otp-btn"
          >
            <RefreshCw size={14} />
            {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend OTP'}
          </button>
        </div>
      </div>
    </div>
  );
}
