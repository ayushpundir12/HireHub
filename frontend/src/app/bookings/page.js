'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiGet, apiPost } from '@/lib/api';
import { useToast } from '@/context/ToastContext';
import { BOOKING_STATUSES, PAYMENT_STATUSES } from '@/lib/constants';
import { Calendar, Star, Loader2, MessageSquare } from 'lucide-react';
import styles from './bookings.module.css';

const TAB_FILTERS = [
  { key: '', label: 'All' },
  { key: 'pending', label: 'Pending' },
  { key: 'confirmed', label: 'Confirmed' },
  { key: 'in_progress', label: 'In Progress' },
  { key: 'completed', label: 'Completed' },
  { key: 'cancelled', label: 'Cancelled' },
];

export default function BookingsPage() {
  const [bookings, setBookings] = useState([]);
  const [activeTab, setActiveTab] = useState('');
  const [loading, setLoading] = useState(true);
  const [reviewModal, setReviewModal] = useState(null);
  const [reviewForm, setReviewForm] = useState({ rating: 5, comment: '' });
  const [submitting, setSubmitting] = useState(false);
  const { toast } = useToast();

  const fetchBookings = async () => {
    const params = activeTab ? `?status=${activeTab}` : '';
    const { data } = await apiGet(`/bookings/my/${params}`);
    if (data) setBookings(data.results || []);
    setLoading(false);
  };

  useEffect(() => {
    setLoading(true);
    fetchBookings();
  }, [activeTab]);

  const formatDate = (str) => {
    return new Date(str).toLocaleDateString('en-IN', {
      day: 'numeric', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  const handleReviewSubmit = async () => {
    if (!reviewModal) return;
    setSubmitting(true);
    const { data, error } = await apiPost(`/bookings/${reviewModal}/review/`, {
      rating: reviewForm.rating,
      comment: reviewForm.comment,
    });
    setSubmitting(false);

    if (error) {
      toast.error(typeof error === 'string' ? error : 'Failed to submit review.');
      return;
    }

    toast.success('Review submitted!');
    setReviewModal(null);
    setReviewForm({ rating: 5, comment: '' });
    fetchBookings();
  };

  return (
    <div className={styles.page}>
      <div className="container">
        <h1 className="display-md" style={{ marginBottom: 24 }}>My Bookings</h1>

        {/* Tabs */}
        <div className="tabs">
          {TAB_FILTERS.map(tab => (
            <button
              key={tab.key}
              className={`tab ${activeTab === tab.key ? 'tab--active' : ''}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Bookings List */}
        <div className={styles.list}>
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className={`card ${styles.skeletonCard}`}>
                <div className="skeleton" style={{ width: '60%', height: 18 }} />
                <div className="skeleton" style={{ width: '40%', height: 14, marginTop: 8 }} />
              </div>
            ))
          ) : bookings.length === 0 ? (
            <div className="empty-state">
              <Calendar size={48} />
              <h3 className="heading-md" style={{ marginTop: 16 }}>No bookings found</h3>
              <p className="text-muted">
                {activeTab ? `No ${activeTab} bookings.` : 'You haven\'t made any bookings yet.'}
              </p>
              <Link href="/browse" className="btn btn--primary" style={{ marginTop: 16 }}>
                Find a Pro
              </Link>
            </div>
          ) : (
            bookings.map(booking => {
              const statusInfo = BOOKING_STATUSES[booking.status] || {};
              const paymentInfo = PAYMENT_STATUSES[booking.payment_status] || {};

              return (
                <div key={booking.id} className={`card ${styles.bookingCard}`}>
                  <div className={styles.cardTop}>
                    <div className={styles.cardInfo}>
                      <h3 className={styles.cardTitle}>{booking.category}</h3>
                      <p className={styles.cardPro}>with {booking.pro_name}</p>
                    </div>
                    <span className={`badge ${statusInfo.class || ''}`}>
                      {statusInfo.label || booking.status}
                    </span>
                  </div>

                  <div className={styles.cardMeta}>
                    <span>{formatDate(booking.scheduled_at)}</span>
                    <span>₹{parseFloat(booking.amount).toLocaleString()}</span>
                    <span className={`badge badge--sm ${paymentInfo.class || ''}`}>
                      {paymentInfo.label || booking.payment_status}
                    </span>
                  </div>

                  {/* Actions */}
                  <div className={styles.cardActions}>
                    {booking.status === 'completed' && !booking.has_review && (
                      <button
                        className="btn btn--outline btn--sm"
                        onClick={() => setReviewModal(booking.id)}
                      >
                        <Star size={14} /> Leave Review
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Review Modal */}
      {reviewModal && (
        <div className="modal-overlay" onClick={() => setReviewModal(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2 className="heading-lg" style={{ marginBottom: 20 }}>Leave a Review</h2>

            <div className="form-group">
              <label className="form-label">Rating</label>
              <div className={styles.starInput}>
                {[1, 2, 3, 4, 5].map(n => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => setReviewForm(f => ({ ...f, rating: n }))}
                    className={styles.starBtn}
                  >
                    <Star
                      size={28}
                      fill={n <= reviewForm.rating ? '#f59f00' : 'none'}
                      stroke={n <= reviewForm.rating ? '#f59f00' : '#e0ddd6'}
                    />
                  </button>
                ))}
              </div>
            </div>

            <div className="form-group" style={{ marginTop: 16 }}>
              <label className="form-label">Comment (optional)</label>
              <textarea
                className="form-input"
                placeholder="How was your experience?"
                value={reviewForm.comment}
                onChange={(e) => setReviewForm(f => ({ ...f, comment: e.target.value }))}
                rows={3}
              />
            </div>

            <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
              <button className="btn btn--outline" onClick={() => setReviewModal(null)}>Cancel</button>
              <button
                className="btn btn--primary"
                onClick={handleReviewSubmit}
                disabled={submitting}
              >
                {submitting ? 'Submitting…' : 'Submit Review'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
