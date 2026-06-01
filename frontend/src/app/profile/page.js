'use client';

import { useState, useEffect } from 'react';
import { apiGet, apiPatch, apiPost } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/context/ToastContext';
import Link from 'next/link';
import { User, Save, Lock, Shield, Loader2 } from 'lucide-react';
import styles from './profile.module.css';

export default function ProfilePage() {
  const { user, fetchProfile } = useAuth();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [changingPw, setChangingPw] = useState(false);

  const [profile, setProfile] = useState({
    full_name: '',
    locality: '',
    phone_number: '',
    avatar_url: '',
    lat: '',
    lng: '',
  });

  const [passwords, setPasswords] = useState({
    new_password: '',
    confirm_password: '',
  });

  useEffect(() => {
    const fetchData = async () => {
      const { data } = await apiGet('/auth/profile/');
      if (data) {
        setProfile({
          full_name: data.full_name || '',
          locality: data.locality || '',
          phone_number: data.phone_number || '',
          avatar_url: data.avatar_url || '',
          lat: data.lat || '',
          lng: data.lng || '',
        });
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    const { error } = await apiPatch('/auth/profile/', profile);
    setSaving(false);

    if (error) {
      toast.error('Failed to update profile.');
      return;
    }

    toast.success('Profile updated!');
    fetchProfile();
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();

    if (passwords.new_password.length < 8) {
      toast.error('Password must be at least 8 characters.');
      return;
    }

    if (passwords.new_password !== passwords.confirm_password) {
      toast.error('Passwords do not match.');
      return;
    }

    setChangingPw(true);
    const { error } = await apiPost('/auth/change-password/', passwords);
    setChangingPw(false);

    if (error) {
      toast.error(typeof error === 'string' ? error : 'Failed to change password.');
      return;
    }

    toast.success('Password changed!');
    setPasswords({ new_password: '', confirm_password: '' });
  };

  if (loading) {
    return (
      <div className={styles.page}>
        <div className="container container--narrow">
          <div className="skeleton" style={{ height: 400 }} />
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className="container container--narrow">
        <h1 className="display-md" style={{ marginBottom: 32 }}>Profile Settings</h1>

        {/* Profile Info */}
        <div className={`card ${styles.section}`}>
          <div className={styles.sectionHeader}>
            <User size={20} />
            <h2 className="heading-md">Personal Information</h2>
          </div>

          <form onSubmit={handleProfileSave} className={styles.form}>
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input
                className="form-input"
                value={profile.full_name}
                onChange={(e) => setProfile(p => ({ ...p, full_name: e.target.value }))}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Email</label>
              <input className="form-input" value={user?.email || ''} disabled />
              <span className="form-hint">Email cannot be changed</span>
            </div>

            <div className="form-group">
              <label className="form-label">Phone Number</label>
              <input
                className="form-input"
                value={profile.phone_number}
                onChange={(e) => setProfile(p => ({ ...p, phone_number: e.target.value }))}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Locality</label>
              <input
                className="form-input"
                value={profile.locality}
                onChange={(e) => setProfile(p => ({ ...p, locality: e.target.value }))}
                placeholder="e.g. Sector 15, Gurgaon"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Avatar URL</label>
              <input
                className="form-input"
                value={profile.avatar_url}
                onChange={(e) => setProfile(p => ({ ...p, avatar_url: e.target.value }))}
                placeholder="https://..."
              />
            </div>

            <button type="submit" className="btn btn--primary" disabled={saving}>
              {saving ? <Loader2 size={16} className={styles.spinner} /> : <Save size={16} />}
              Save Changes
            </button>
          </form>
        </div>

        {/* Change Password */}
        <div className={`card ${styles.section}`}>
          <div className={styles.sectionHeader}>
            <Lock size={20} />
            <h2 className="heading-md">Change Password</h2>
          </div>

          <form onSubmit={handlePasswordChange} className={styles.form}>
            <div className="form-group">
              <label className="form-label">New Password</label>
              <input
                type="password"
                className="form-input"
                value={passwords.new_password}
                onChange={(e) => setPasswords(p => ({ ...p, new_password: e.target.value }))}
                placeholder="Min 8 characters"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Confirm Password</label>
              <input
                type="password"
                className="form-input"
                value={passwords.confirm_password}
                onChange={(e) => setPasswords(p => ({ ...p, confirm_password: e.target.value }))}
                placeholder="Repeat new password"
              />
            </div>

            <button type="submit" className="btn btn--primary" disabled={changingPw}>
              {changingPw ? <Loader2 size={16} className={styles.spinner} /> : <Lock size={16} />}
              Change Password
            </button>
          </form>
        </div>

        {/* Become Pro Link */}
        {user?.role !== 'pro' && (
          <div className={`card ${styles.section}`} style={{ background: 'var(--color-accent-light)' }}>
            <div className={styles.sectionHeader}>
              <Shield size={20} />
              <h2 className="heading-md">Want to earn on HireHub?</h2>
            </div>
            <p className="text-md text-muted" style={{ marginTop: 8 }}>
              Apply to become a verified professional and start receiving bookings.
            </p>
            <Link href="/become-pro" className="btn btn--accent" style={{ marginTop: 16 }}>
              Become a Pro
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
