'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { apiGet } from '@/lib/api';
import { Star, MapPin, Briefcase, Clock, ArrowRight, User } from 'lucide-react';
import styles from './proDetail.module.css';

export default function ProDetailPage() {
  const { id } = useParams();
  const [pro, setPro] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      const [proRes, reviewRes] = await Promise.all([
        apiGet(`/pros/${id}/`),
        apiGet(`/pros/${id}/reviews/`),
      ]);
      if (proRes.data) setPro(proRes.data);
      if (reviewRes.data) setReviews(reviewRes.data.results || []);
      setLoading(false);
    };
    fetchData();
  }, [id]);

  const getInitials = (name) => {
    if (!name) return '?';
    return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
  };

  const renderStars = (rating) => {
    const stars = [];
    for (let i = 0; i < 5; i++) {
      stars.push(
        <Star
          key={i}
          size={16}
          fill={i < Math.round(rating) ? '#f59f00' : 'none'}
          stroke={i < Math.round(rating) ? '#f59f00' : '#e0ddd6'}
        />
      );
    }
    return stars;
  };

  const timeAgo = (dateStr) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    if (days < 1) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 30) return `${days} days ago`;
    if (days < 365) return `${Math.floor(days / 30)} months ago`;
    return `${Math.floor(days / 365)} years ago`;
  };

  if (loading) {
    return (
      <div className={styles.page}>
        <div className="container">
          <div className={styles.skeleton}>
            <div className="skeleton" style={{ width: 96, height: 96, borderRadius: '50%' }} />
            <div className="skeleton" style={{ width: '40%', height: 24, marginTop: 16 }} />
            <div className="skeleton" style={{ width: '25%', height: 16, marginTop: 8 }} />
          </div>
        </div>
      </div>
    );
  }

  if (!pro) {
    return (
      <div className={styles.page}>
        <div className="container">
          <div className="empty-state">
            <h3 className="heading-md">Professional not found</h3>
            <p className="text-muted">This profile may no longer be available.</p>
            <Link href="/browse" className="btn btn--outline" style={{ marginTop: 16 }}>Browse Pros</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className="container">
        <div className={styles.layout}>
          {/* Main Content */}
          <div className={styles.main}>
            {/* Profile Header */}
            <div className={styles.profileHeader}>
              <div className={styles.avatarLg}>
                {pro.avatar_url ? (
                  <img src={pro.avatar_url} alt={pro.full_name} />
                ) : (
                  <span>{getInitials(pro.full_name)}</span>
                )}
              </div>
              <div className={styles.headerInfo}>
                <div className={styles.headerTop}>
                  <h1 className={styles.proName}>{pro.full_name}</h1>
                  <span className={`badge ${pro.is_available ? 'badge--available' : 'badge--unavailable'}`}>
                    {pro.is_available ? 'Available' : 'Busy'}
                  </span>
                </div>
                <p className={styles.proCategory}>{pro.category_label || pro.category}</p>
                <div className={styles.headerMeta}>
                  <div className={styles.metaItem}>
                    {renderStars(parseFloat(pro.avg_rating || 0))}
                    <span className={styles.ratingNum}>
                      {parseFloat(pro.avg_rating || 0).toFixed(1)} ({pro.total_jobs || 0} jobs)
                    </span>
                  </div>
                  {(pro.city || pro.state) && (
                    <div className={styles.metaItem}>
                      <MapPin size={15} />
                      <span>{[pro.city, pro.state].filter(Boolean).join(', ')}</span>
                    </div>
                  )}
                  {pro.experience > 0 && (
                    <div className={styles.metaItem}>
                      <Clock size={15} />
                      <span>{pro.experience} yrs experience</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Bio */}
            {pro.bio && (
              <div className={styles.section}>
                <h2 className="heading-md">About</h2>
                <p className="text-md" style={{ color: 'var(--color-ink-light)', marginTop: 8, lineHeight: 1.7 }}>
                  {pro.bio}
                </p>
              </div>
            )}

            {/* Reviews */}
            <div className={styles.section}>
              <h2 className="heading-md">Reviews ({reviews.length})</h2>
              {reviews.length === 0 ? (
                <p className="text-sm text-muted" style={{ marginTop: 12 }}>No reviews yet.</p>
              ) : (
                <div className={styles.reviewList}>
                  {reviews.map(review => (
                    <div key={review.id} className={styles.reviewCard}>
                      <div className={styles.reviewTop}>
                        <div className={styles.reviewAvatar}>
                          {review.client_avatar ? (
                            <img src={review.client_avatar} alt={review.client_name} />
                          ) : (
                            <User size={16} />
                          )}
                        </div>
                        <div>
                          <p className={styles.reviewName}>{review.client_name}</p>
                          <p className={styles.reviewDate}>{timeAgo(review.created_at)}</p>
                        </div>
                        <div className={styles.reviewStars}>{renderStars(review.rating)}</div>
                      </div>
                      {review.comment && (
                        <p className={styles.reviewComment}>{review.comment}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar — Booking CTA */}
          <aside className={styles.sidebar}>
            <div className={styles.bookingCard}>
              {pro.hourly_rate && (
                <div className={styles.priceBlock}>
                  <span className={styles.price}>₹{parseFloat(pro.hourly_rate).toLocaleString()}</span>
                  <span className={styles.priceUnit}>/hour</span>
                </div>
              )}
              <div className={styles.bookingStats}>
                <div className={styles.bookingStat}>
                  <Briefcase size={16} />
                  <span>{pro.total_jobs || 0} jobs done</span>
                </div>
                <div className={styles.bookingStat}>
                  <Star size={16} fill="#f59f00" stroke="#f59f00" />
                  <span>{parseFloat(pro.avg_rating || 0).toFixed(1)} rating</span>
                </div>
              </div>
              <Link
                href={`/book/${pro.user_id}`}
                className="btn btn--accent btn--full btn--lg"
                id="pro-book-now"
              >
                Book Now <ArrowRight size={18} />
              </Link>
              <p className="text-xs text-muted" style={{ textAlign: 'center', marginTop: 8 }}>
                Free cancellation before confirmation
              </p>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
