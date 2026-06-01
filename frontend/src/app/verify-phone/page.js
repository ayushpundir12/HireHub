'use client';

import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/context/ToastContext';
import { Phone } from 'lucide-react';
import styles from '@/app/auth.module.css';

export default function VerifyPhonePage() {
  const [step, setStep] = useState(1); // 1: Enter Phone, 2: Enter OTP
  const [phoneNumber, setPhoneNumber] = useState('');
  const [phoneOtp, setPhoneOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const { verifyPhoneOnly } = useAuth();
  const { toast } = useToast();

  const handleSendOtp = async (e) => {
    e.preventDefault();
    if (!phoneNumber || phoneNumber.length < 10) {
      toast.error('Please enter a valid phone number.');
      return;
    }

    setLoading(true);
    const { data, error } = await verifyPhoneOnly(phoneNumber, null);
    setLoading(false);

    if (error) {
      toast.error(typeof error === 'string' ? error : 'Failed to send OTP.');
      return;
    }

    toast.success('OTP sent to your phone!');
    setStep(2);
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    if (phoneOtp.length !== 6) {
      toast.error('Please enter a 6-digit OTP.');
      return;
    }

    setLoading(true);
    const { data, error } = await verifyPhoneOnly(null, phoneOtp);
    setLoading(false);

    if (error) {
      toast.error(typeof error === 'string' ? error : 'Invalid OTP.');
      return;
    }

    toast.success('Phone number verified successfully!');
    window.location.href = '/browse';
  };

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.header}>
          <div className={styles.verifyIcon}>
            <Phone size={32} />
          </div>
          <h1 className={styles.title}>Verify your phone</h1>
          <p className={styles.subtitle}>
            {step === 1 
              ? "Since you signed up with Google, we just need your phone number to complete your profile."
              : `We sent a code to ${phoneNumber}. Enter it below.`}
          </p>
        </div>

        {step === 1 ? (
          <form onSubmit={handleSendOtp} className={styles.form}>
            <div className="form-group">
              <label className="form-label" htmlFor="phone-number">Phone Number</label>
              <input
                type="tel"
                id="phone-number"
                className="form-input"
                placeholder="e.g. 9876543210"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value.replace(/\D/g, ''))}
              />
            </div>
            <button
              type="submit"
              className="btn btn--primary btn--full btn--lg"
              disabled={loading}
              style={{ marginTop: 16 }}
            >
              {loading ? 'Sending OTP…' : 'Send OTP'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp} className={styles.form}>
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
              style={{ marginTop: 16 }}
            >
              {loading ? 'Verifying…' : 'Verify Phone'}
            </button>
            <button
              type="button"
              className="btn btn--ghost btn--full"
              onClick={() => setStep(1)}
              disabled={loading}
              style={{ marginTop: 8 }}
            >
              Change Phone Number
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
