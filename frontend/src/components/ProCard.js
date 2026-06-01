import Link from 'next/link';
import { Star, MapPin, Briefcase, Clock } from 'lucide-react';
import styles from './ProCard.module.css';

export default function ProCard({ pro }) {
  const {
    id, full_name, avatar_url, category, category_label,
    hourly_rate, avg_rating, total_jobs, city, state,
    is_available, experience, bio,
  } = pro;

  const getInitials = (name) => {
    if (!name) return '?';
    return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
  };

  const renderStars = (rating) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalf = rating - fullStars >= 0.5;

    for (let i = 0; i < 5; i++) {
      if (i < fullStars) {
        stars.push(<Star key={i} size={14} fill="#f59f00" stroke="#f59f00" />);
      } else if (i === fullStars && hasHalf) {
        stars.push(<Star key={i} size={14} fill="#f59f00" stroke="#f59f00" style={{ clipPath: 'inset(0 50% 0 0)' }} />);
      } else {
        stars.push(<Star key={i} size={14} stroke="#e0ddd6" fill="none" />);
      }
    }
    return stars;
  };

  return (
    <Link href={`/pro/${id}`} className={styles.card} id={`pro-card-${id}`}>
      <div className={styles.top}>
        <div className={styles.avatar}>
          {avatar_url ? (
            <img src={avatar_url} alt={full_name} />
          ) : (
            <span>{getInitials(full_name)}</span>
          )}
        </div>
        <div className={styles.info}>
          <h3 className={styles.name}>{full_name}</h3>
          <p className={styles.category}>{category_label || category}</p>
        </div>
        {is_available !== undefined && (
          <span className={`badge ${is_available ? 'badge--available' : 'badge--unavailable'}`}>
            {is_available ? 'Available' : 'Busy'}
          </span>
        )}
      </div>

      {bio && <p className={styles.bio}>{bio.length > 80 ? bio.slice(0, 80) + '…' : bio}</p>}

      <div className={styles.meta}>
        <div className={styles.metaItem}>
          <div className={styles.stars}>
            {renderStars(parseFloat(avg_rating || 0))}
          </div>
          <span className={styles.ratingNum}>{parseFloat(avg_rating || 0).toFixed(1)}</span>
        </div>

        {(city || state) && (
          <div className={styles.metaItem}>
            <MapPin size={14} />
            <span>{[city, state].filter(Boolean).join(', ')}</span>
          </div>
        )}
      </div>

      <div className={styles.bottom}>
        <div className={styles.stats}>
          <div className={styles.stat}>
            <Briefcase size={14} />
            <span>{total_jobs || 0} jobs</span>
          </div>
          {experience > 0 && (
            <div className={styles.stat}>
              <Clock size={14} />
              <span>{experience} yrs exp</span>
            </div>
          )}
        </div>

        {hourly_rate && (
          <p className={styles.rate}>
            ₹{parseFloat(hourly_rate).toLocaleString()}<span>/hr</span>
          </p>
        )}
      </div>
    </Link>
  );
}
