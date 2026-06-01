'use client';

import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { supabase } from '@/lib/supabase';
import { apiGet, apiPost } from '@/lib/api';

const AuthContext = createContext({});

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch Django profile
  const fetchProfile = useCallback(async () => {
    const { data, error } = await apiGet('/auth/me/');
    if (!error && data) {
      setUser(data);
    }
    return { data, error };
  }, []);

  // Initialize auth state
  useEffect(() => {
    const initAuth = async () => {
      const { data: { session: currentSession } } = await supabase.auth.getSession();
      setSession(currentSession);

      if (currentSession) {
        await fetchProfile();
      }
      setLoading(false);
    };

    initAuth();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, newSession) => {
        setSession(newSession);
        if (newSession) {
          // Defer fetchProfile to avoid Supabase auth lock deadlock
          setTimeout(() => {
            fetchProfile();
          }, 0);
        } else {
          setUser(null);
        }
      }
    );

    return () => subscription.unsubscribe();
  }, [fetchProfile]);

  // Sign up with email/password
  const signUp = async (email, password, fullName, phoneNumber) => {
    const { data, error } = await apiPost('/auth/signup/', {
      email,
      password,
      full_name: fullName,
      phone_number: phoneNumber,
    });

    if (!error && data?.access_token) {
      // Set the session manually with the token from our backend
      await supabase.auth.setSession({
        access_token: data.access_token,
        refresh_token: '',
      });
    }

    return { data, error };
  };

  // Login with email/password
  const login = async (email, password) => {
    const { data, error } = await apiPost('/auth/login/', { email, password });

    if (!error && data) {
      await supabase.auth.setSession({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
      });
      setUser(data.user);
    }

    return { data, error };
  };

  // Login with Google
  const loginWithGoogle = async () => {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
    return { data, error };
  };

  // Handle OAuth callback
  const handleOAuthCallback = async (accessToken) => {
    const { data, error } = await apiPost('/auth/oauth/callback/', {
      access_token: accessToken,
    });
    if (!error && data?.user) {
      setUser(data.user);
    }
    return { data, error };
  };

  // Verify OTP (email + phone)
  const verifyOtp = async (emailOtp, phoneOtp) => {
    return apiPost('/auth/verify/', {
      email_otp: emailOtp,
      phone_otp: phoneOtp,
    });
  };

  // Verify phone only (OAuth users)
  const verifyPhoneOnly = async (phoneNumber, phoneOtp) => {
    const body = {};
    if (phoneNumber) body.phone_number = phoneNumber;
    if (phoneOtp) body.phone_otp = phoneOtp;
    return apiPost('/auth/verify-phone/', body);
  };

  // Resend OTP
  const resendOtp = async (type = 'both') => {
    return apiPost('/auth/resend-otp/', { type });
  };

  // Logout
  const logout = async () => {
    await apiPost('/auth/logout/', {});
    await supabase.auth.signOut();
    setUser(null);
    setSession(null);
  };

  const value = {
    user,
    session,
    loading,
    signUp,
    login,
    loginWithGoogle,
    handleOAuthCallback,
    verifyOtp,
    verifyPhoneOnly,
    resendOtp,
    logout,
    fetchProfile,
    isAuthenticated: !!session,
    isPro: user?.role === 'pro',
    isVerified: user?.is_email_verified && user?.is_number_verified,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
