'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiGet, apiPost, apiPatch } from '@/lib/api';
import { useToast } from '@/context/ToastContext';
import {
  Bell, CheckCheck, Briefcase, ShieldCheck, Star,
  XCircle, Clock, ChevronRight
} from 'lucide-react';
import styles from './notifications.module.css';

const TYPE_ICONS = {
  booking_received: Briefcase,
  booking_confirmed: CheckCheck,
  booking_cancelled: XCircle,
  booking_completed: CheckCheck,
  kyc_approved: ShieldCheck,
  kyc_rejected: XCircle,
  review_received: Star,
};

const TYPE_COLORS = {
  booking_received: 'var(--color-info)',
  booking_confirmed: 'var(--color-success)',
  booking_cancelled: 'var(--color-danger)',
  booking_completed: 'var(--color-success)',
  kyc_approved: 'var(--color-success)',
  kyc_rejected: 'var(--color-danger)',
  review_received: '#f59f00',
};

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();
  const router = useRouter();

  useEffect(() => {
    const fetch = async () => {
      const { data } = await apiGet('/notifications/');
      if (data) setNotifications(data.results || []);
      setLoading(false);
    };
    fetch();
  }, []);

  const timeAgo = (dateStr) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    return new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
  };

  const handleMarkRead = async (id) => {
    await apiPatch(`/notifications/${id}/read/`, {});
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
  };

  const handleMarkAllRead = async () => {
    const { data } = await apiPost('/notifications/read-all/', {});
    if (data) {
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      toast.success('All notifications marked as read.');
    }
  };

  const handleClick = (notif) => {
    if (!notif.is_read) handleMarkRead(notif.id);
    if (notif.link) router.push(notif.link);
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className={styles.page}>
      <div className="container container--narrow">
        <div className={styles.header}>
          <h1 className="display-md">Notifications</h1>
          {unreadCount > 0 && (
            <button className="btn btn--ghost btn--sm" onClick={handleMarkAllRead}>
              <CheckCheck size={16} /> Mark all read
            </button>
          )}
        </div>

        {loading ? (
          <div className={styles.list}>
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className={styles.skeletonItem}>
                <div className="skeleton" style={{ width: 40, height: 40, borderRadius: '50%' }} />
                <div style={{ flex: 1 }}>
                  <div className="skeleton" style={{ width: '70%', height: 16, marginBottom: 6 }} />
                  <div className="skeleton" style={{ width: '50%', height: 12 }} />
                </div>
              </div>
            ))}
          </div>
        ) : notifications.length === 0 ? (
          <div className="empty-state">
            <Bell size={48} />
            <h3 className="heading-md" style={{ marginTop: 16 }}>No notifications</h3>
            <p className="text-muted">You&apos;re all caught up!</p>
          </div>
        ) : (
          <div className={styles.list}>
            {notifications.map(notif => {
              const Icon = TYPE_ICONS[notif.type] || Bell;
              const color = TYPE_COLORS[notif.type] || 'var(--color-ink-muted)';

              return (
                <button
                  key={notif.id}
                  className={`${styles.item} ${!notif.is_read ? styles.unread : ''}`}
                  onClick={() => handleClick(notif)}
                  id={`notif-${notif.id}`}
                >
                  <div className={styles.iconWrap} style={{ color, background: `${color}15` }}>
                    <Icon size={18} />
                  </div>
                  <div className={styles.content}>
                    <p className={styles.title}>{notif.title}</p>
                    <p className={styles.message}>{notif.message}</p>
                    <p className={styles.time}>{timeAgo(notif.created_at)}</p>
                  </div>
                  {notif.link && <ChevronRight size={16} className={styles.arrow} />}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
