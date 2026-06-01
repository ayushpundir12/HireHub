'use client';

import { useState, useEffect } from 'react';
import { apiGet, apiPost, apiPatch } from '@/lib/api';
import { useToast } from '@/context/ToastContext';
import { useAuth } from '@/context/AuthContext';
import { BOOKING_STATUSES } from '@/lib/constants';
import {
  Briefcase, DollarSign, Star, TrendingUp, Clock,
  Check, X, Play, Flag, Loader2, BarChart3
} from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid
} from 'recharts';
import styles from './dashboard.module.css';

export default function DashboardPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [kpi, setKpi] = useState(null);
  const [earnings, setEarnings] = useState(null);
  const [earningsRange, setEarningsRange] = useState('weekly');
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [otpInputs, setOtpInputs] = useState({});
  const [actionLoading, setActionLoading] = useState({});

  useEffect(() => {
    const fetchAll = async () => {
      const [kpiRes, earningsRes, bookingsRes] = await Promise.all([
        apiGet('/dashboard/pro/'),
        apiGet(`/dashboard/pro/earnings/?range=${earningsRange}`),
        apiGet('/bookings/incoming/'),
      ]);
      if (kpiRes.data) setKpi(kpiRes.data);
      if (earningsRes.data) setEarnings(earningsRes.data);
      if (bookingsRes.data) setBookings(bookingsRes.data.results || []);
      setLoading(false);
    };
    fetchAll();
  }, [earningsRange]);

  const handleStatusUpdate = async (bookingId, newStatus) => {
    setActionLoading(prev => ({ ...prev, [bookingId]: true }));
    const { error } = await apiPatch(`/bookings/${bookingId}/status/`, { status: newStatus });
    setActionLoading(prev => ({ ...prev, [bookingId]: false }));

    if (error) {
      toast.error(typeof error === 'string' ? error : 'Failed to update status.');
      return;
    }

    toast.success(`Booking ${newStatus === 'confirmed' ? 'accepted' : newStatus === 'cancelled' ? 'declined' : 'updated'}.`);
    // Refresh bookings
    const { data } = await apiGet('/bookings/incoming/');
    if (data) setBookings(data.results || []);
  };

  const handleRequestCompletion = async (bookingId) => {
    setActionLoading(prev => ({ ...prev, [bookingId]: true }));
    const { error } = await apiPost(`/bookings/${bookingId}/request-completion/`, {});
    setActionLoading(prev => ({ ...prev, [bookingId]: false }));

    if (error) {
      toast.error(typeof error === 'string' ? error : 'Failed to request completion.');
      return;
    }

    toast.success('OTP sent to the client. Ask them for the code.');
    const { data } = await apiGet('/bookings/incoming/');
    if (data) setBookings(data.results || []);
  };

  const handleConfirmCompletion = async (bookingId) => {
    const otp = otpInputs[bookingId];
    if (!otp || otp.length !== 6) {
      toast.error('Please enter the 6-digit OTP.');
      return;
    }

    setActionLoading(prev => ({ ...prev, [bookingId]: true }));
    const { error } = await apiPost(`/bookings/${bookingId}/confirm-completion/`, { otp });
    setActionLoading(prev => ({ ...prev, [bookingId]: false }));

    if (error) {
      toast.error(typeof error === 'string' ? error : 'Invalid OTP.');
      return;
    }

    toast.success('Job marked as completed!');
    setOtpInputs(prev => ({ ...prev, [bookingId]: '' }));
    // Refresh all data
    const [kpiRes, bookingsRes] = await Promise.all([
      apiGet('/dashboard/pro/'),
      apiGet('/bookings/incoming/'),
    ]);
    if (kpiRes.data) setKpi(kpiRes.data);
    if (bookingsRes.data) setBookings(bookingsRes.data.results || []);
  };

  const formatDate = (str) => {
    return new Date(str).toLocaleDateString('en-IN', {
      day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className={styles.page}>
        <div className="container">
          <div className="kpi-grid">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="kpi-card">
                <div className="skeleton" style={{ width: '60%', height: 14, marginBottom: 10 }} />
                <div className="skeleton" style={{ width: '40%', height: 28 }} />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className="container">
        <div className={styles.header}>
          <div>
            <h1 className="display-md">Dashboard</h1>
            <p className="text-md text-muted">Welcome back, {user?.full_name?.split(' ')[0]}</p>
          </div>
        </div>

        {/* KPI Cards */}
        {kpi && (
          <div className="kpi-grid">
            <div className="kpi-card">
              <p className="kpi-card__label">Total Jobs</p>
              <p className="kpi-card__value">{kpi.total_jobs}</p>
            </div>
            <div className="kpi-card">
              <p className="kpi-card__label">Total Earnings</p>
              <p className="kpi-card__value">₹{kpi.total_earnings.toLocaleString()}</p>
            </div>
            <div className="kpi-card">
              <p className="kpi-card__label">Avg Rating</p>
              <p className="kpi-card__value" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                {kpi.avg_rating.toFixed(1)} <Star size={18} fill="#f59f00" stroke="#f59f00" />
              </p>
            </div>
            <div className="kpi-card">
              <p className="kpi-card__label">Acceptance Rate</p>
              <p className="kpi-card__value">{kpi.acceptance_rate}%</p>
            </div>
            <div className="kpi-card">
              <p className="kpi-card__label">Pending</p>
              <p className="kpi-card__value" style={{ color: kpi.pending_bookings > 0 ? 'var(--color-accent)' : 'inherit' }}>
                {kpi.pending_bookings}
              </p>
            </div>
          </div>
        )}

        {/* Earnings Chart */}
        <div className={styles.chartSection}>
          <div className={styles.chartHeader}>
            <h2 className="heading-md">
              <BarChart3 size={18} style={{ display: 'inline', marginRight: 6 }} />
              Earnings
            </h2>
            <div className={styles.chartTabs}>
              {['daily', 'weekly', 'monthly'].map(r => (
                <button
                  key={r}
                  className={`btn btn--ghost btn--sm ${earningsRange === r ? styles.chartTabActive : ''}`}
                  onClick={() => setEarningsRange(r)}
                >
                  {r.charAt(0).toUpperCase() + r.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {earnings && earnings.points && earnings.points.length > 0 ? (
            <div className={styles.chart}>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={earnings.points}>
                  <defs>
                    <linearGradient id="earningsGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--color-accent)" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="var(--color-accent)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
                  <XAxis dataKey="period" fontSize={12} stroke="var(--color-ink-muted)" />
                  <YAxis fontSize={12} stroke="var(--color-ink-muted)" tickFormatter={v => `₹${v}`} />
                  <Tooltip
                    contentStyle={{
                      background: 'var(--color-surface)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 8,
                      fontSize: 13,
                    }}
                    formatter={(value) => [`₹${value.toLocaleString()}`, 'Earnings']}
                  />
                  <Area
                    type="monotone"
                    dataKey="earnings"
                    stroke="var(--color-accent)"
                    strokeWidth={2}
                    fill="url(#earningsGrad)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="empty-state" style={{ padding: '40px 0' }}>
              <p className="text-muted">No earnings data for this period yet.</p>
            </div>
          )}
        </div>

        {/* Incoming Bookings */}
        <div className={styles.bookingsSection}>
          <h2 className="heading-md" style={{ marginBottom: 16 }}>Incoming Bookings</h2>

          {bookings.length === 0 ? (
            <div className="empty-state" style={{ padding: '32px 0' }}>
              <Clock size={40} />
              <p className="text-muted" style={{ marginTop: 12 }}>No incoming bookings right now.</p>
            </div>
          ) : (
            <div className={styles.bookingsList}>
              {bookings.map(booking => {
                const statusInfo = BOOKING_STATUSES[booking.status] || {};
                const isLoading = actionLoading[booking.id];

                return (
                  <div key={booking.id} className={`card ${styles.bookingItem}`}>
                    <div className={styles.bookingTop}>
                      <div>
                        <h3 className={styles.bookingTitle}>{booking.category}</h3>
                        <p className="text-sm text-muted">From {booking.client_name} · {formatDate(booking.scheduled_at)}</p>
                      </div>
                      <span className={`badge ${statusInfo.class || ''}`}>
                        {statusInfo.label || booking.status}
                      </span>
                    </div>

                    <p className={styles.bookingAmount}>₹{parseFloat(booking.amount).toLocaleString()}</p>

                    {/* Action Buttons per Status */}
                    <div className={styles.bookingActions}>
                      {booking.status === 'pending' && (
                        <>
                          <button
                            className="btn btn--success btn--sm"
                            onClick={() => handleStatusUpdate(booking.id, 'confirmed')}
                            disabled={isLoading}
                          >
                            <Check size={14} /> Accept
                          </button>
                          <button
                            className="btn btn--danger btn--sm"
                            onClick={() => handleStatusUpdate(booking.id, 'cancelled')}
                            disabled={isLoading}
                          >
                            <X size={14} /> Decline
                          </button>
                        </>
                      )}

                      {booking.status === 'confirmed' && (
                        <button
                          className="btn btn--primary btn--sm"
                          onClick={() => handleStatusUpdate(booking.id, 'in_progress')}
                          disabled={isLoading}
                        >
                          <Play size={14} /> Start Job
                        </button>
                      )}

                      {booking.status === 'in_progress' && (
                        <button
                          className="btn btn--accent btn--sm"
                          onClick={() => handleRequestCompletion(booking.id)}
                          disabled={isLoading}
                        >
                          <Flag size={14} /> Request Completion
                        </button>
                      )}

                      {booking.status === 'awaiting_confirmation' && (
                        <div className={styles.otpWrap}>
                          <input
                            type="text"
                            className="form-input"
                            placeholder="Enter 6-digit OTP"
                            value={otpInputs[booking.id] || ''}
                            onChange={(e) => setOtpInputs(prev => ({
                              ...prev, [booking.id]: e.target.value.replace(/\D/g, '').slice(0, 6)
                            }))}
                            maxLength={6}
                            inputMode="numeric"
                            style={{ width: 160 }}
                          />
                          <button
                            className="btn btn--success btn--sm"
                            onClick={() => handleConfirmCompletion(booking.id)}
                            disabled={isLoading}
                          >
                            {isLoading ? <Loader2 size={14} className={styles.spinner} /> : <Check size={14} />}
                            Confirm
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
