'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { apiGet } from '@/lib/api';
import {
  Menu, X, Bell, User, ChevronDown,
  LayoutDashboard, Briefcase, LogOut, Settings, Shield
} from 'lucide-react';
import styles from './Navbar.module.css';

export default function Navbar() {
  const { user, isAuthenticated, isPro, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [scrolled, setScrolled] = useState(false);
  const dropdownRef = useRef(null);
  const router = useRouter();

  // Track scroll for navbar shadow
  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Poll unread count every 30s
  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchUnread = async () => {
      const { data } = await apiGet('/notifications/unread-count/');
      if (data) setUnreadCount(data.unread_count);
    };

    fetchUnread();
    const interval = setInterval(fetchUnread, 30000);
    return () => clearInterval(interval);
  }, [isAuthenticated]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClick = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleLogout = async () => {
    await logout();
    setProfileOpen(false);
    router.push('/');
  };

  const getInitials = (name) => {
    if (!name) return '?';
    return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
  };

  return (
    <nav className={`${styles.nav} ${scrolled ? styles.scrolled : ''}`}>
      <div className={`container ${styles.inner}`}>
        {/* Logo */}
        <Link href="/" className={styles.logo}>
          <span className={styles.logoMark}>H</span>
          <span className={styles.logoText}>HireHub</span>
        </Link>

        {/* Desktop Nav */}
        <div className={styles.desktopNav}>
          <Link href="/browse" className={styles.navLink}>Find Pros</Link>
          {isAuthenticated && (
            <>
              <Link href="/bookings" className={styles.navLink}>My Bookings</Link>
              {isPro && (
                <Link href="/dashboard" className={styles.navLink}>Dashboard</Link>
              )}
            </>
          )}
        </div>

        {/* Right Section */}
        <div className={styles.right}>
          {isAuthenticated ? (
            <>
              {/* Notifications */}
              <Link href="/notifications" className={styles.bellBtn}>
                <Bell size={20} />
                {unreadCount > 0 && (
                  <span className={styles.bellBadge}>
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </Link>

              {/* Profile Dropdown */}
              <div className={styles.profileWrap} ref={dropdownRef}>
                <button
                  className={styles.profileBtn}
                  onClick={() => setProfileOpen(!profileOpen)}
                  id="nav-profile-btn"
                >
                  <div className="avatar avatar--sm">
                    {user?.avatar_url ? (
                      <img src={user.avatar_url} alt={user.full_name} />
                    ) : (
                      getInitials(user?.full_name)
                    )}
                  </div>
                  <span className={styles.profileName}>{user?.full_name?.split(' ')[0]}</span>
                  <ChevronDown size={14} className={`${styles.chevron} ${profileOpen ? styles.chevronUp : ''}`} />
                </button>

                {profileOpen && (
                  <div className={styles.dropdown}>
                    <div className={styles.dropdownHeader}>
                      <p className={styles.dropdownName}>{user?.full_name}</p>
                      <p className={styles.dropdownEmail}>{user?.email}</p>
                    </div>
                    <div className={styles.dropdownDivider} />
                    <Link href="/profile" className={styles.dropdownItem} onClick={() => setProfileOpen(false)}>
                      <Settings size={16} /> Profile Settings
                    </Link>
                    <Link href="/bookings" className={styles.dropdownItem} onClick={() => setProfileOpen(false)}>
                      <Briefcase size={16} /> My Bookings
                    </Link>
                    {isPro ? (
                      <Link href="/dashboard" className={styles.dropdownItem} onClick={() => setProfileOpen(false)}>
                        <LayoutDashboard size={16} /> Pro Dashboard
                      </Link>
                    ) : (
                      <Link href="/become-pro" className={styles.dropdownItem} onClick={() => setProfileOpen(false)}>
                        <Shield size={16} /> Become a Pro
                      </Link>
                    )}
                    <div className={styles.dropdownDivider} />
                    <button className={styles.dropdownItem} onClick={handleLogout}>
                      <LogOut size={16} /> Log Out
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className={styles.authBtns}>
              <Link href="/login" className="btn btn--ghost">Log In</Link>
              <Link href="/signup" className="btn btn--primary btn--sm">Sign Up</Link>
            </div>
          )}

          {/* Mobile Menu Toggle */}
          <button
            className={styles.mobileToggle}
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
            id="nav-mobile-toggle"
          >
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <div className={styles.mobileMenu}>
          <Link href="/browse" className={styles.mobileLink} onClick={() => setMobileOpen(false)}>
            Find Pros
          </Link>
          {isAuthenticated ? (
            <>
              <Link href="/bookings" className={styles.mobileLink} onClick={() => setMobileOpen(false)}>
                My Bookings
              </Link>
              <Link href="/notifications" className={styles.mobileLink} onClick={() => setMobileOpen(false)}>
                Notifications {unreadCount > 0 && `(${unreadCount})`}
              </Link>
              {isPro ? (
                <Link href="/dashboard" className={styles.mobileLink} onClick={() => setMobileOpen(false)}>
                  Pro Dashboard
                </Link>
              ) : (
                <Link href="/become-pro" className={styles.mobileLink} onClick={() => setMobileOpen(false)}>
                  Become a Pro
                </Link>
              )}
              <Link href="/profile" className={styles.mobileLink} onClick={() => setMobileOpen(false)}>
                Profile Settings
              </Link>
              <button className={`${styles.mobileLink} ${styles.mobileLogout}`} onClick={handleLogout}>
                Log Out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className={styles.mobileLink} onClick={() => setMobileOpen(false)}>
                Log In
              </Link>
              <Link href="/signup" className={`btn btn--primary btn--full ${styles.mobileCta}`} onClick={() => setMobileOpen(false)}>
                Sign Up
              </Link>
            </>
          )}
        </div>
      )}
    </nav>
  );
}
