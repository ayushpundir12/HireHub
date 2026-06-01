'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiGet } from '@/lib/api';
import { CATEGORIES } from '@/lib/constants';
import {
  Search, ArrowRight, CheckCircle2, Shield,
  CreditCard, Star, ChevronRight, Users
} from 'lucide-react';
import styles from './page.module.css';

export default function HomePage() {
  const [categories, setCategories] = useState([]);
  const [searchCategory, setSearchCategory] = useState('');
  const [searchCity, setSearchCity] = useState('');
  const router = useRouter();

  useEffect(() => {
    const fetchCategories = async () => {
      const { data } = await apiGet('/categories/');
      if (data) setCategories(data);
    };
    fetchCategories();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (searchCategory) params.set('category', searchCategory);
    if (searchCity) params.set('city', searchCity);
    router.push(`/browse?${params.toString()}`);
  };

  return (
    <>
      {/* ── Hero ──────────────────────────────────────────── */}
      <section className={styles.hero}>
        <div className={`container ${styles.heroInner}`}>
          <div className={styles.heroContent}>
            <p className={styles.heroTag}>Trusted by thousands of homes</p>
            <h1 className={styles.heroTitle}>
              Find the right pro<br />
              for <span className={styles.heroAccent}>any job</span>
            </h1>
            <p className={styles.heroSub}>
              Book verified professionals for home services. Every pro is background-checked,
              and every job is confirmed with OTP.
            </p>

            {/* Search Bar */}
            <form className={styles.searchBar} onSubmit={handleSearch}>
              <div className={styles.searchField}>
                <select
                  className={styles.searchSelect}
                  value={searchCategory}
                  onChange={(e) => setSearchCategory(e.target.value)}
                  id="hero-category-select"
                >
                  <option value="">What do you need?</option>
                  {CATEGORIES.map(cat => (
                    <option key={cat.value} value={cat.value}>{cat.label}</option>
                  ))}
                </select>
              </div>
              <div className={styles.searchDivider} />
              <div className={styles.searchField}>
                <input
                  type="text"
                  placeholder="Your city"
                  value={searchCity}
                  onChange={(e) => setSearchCity(e.target.value)}
                  className={styles.searchInput}
                  id="hero-city-input"
                />
              </div>
              <button type="submit" className={styles.searchBtn} id="hero-search-btn">
                <Search size={18} />
                <span>Search</span>
              </button>
            </form>

            <div className={styles.heroTrust}>
              <div className={styles.trustItem}>
                <CheckCircle2 size={16} />
                <span>Verified Pros</span>
              </div>
              <div className={styles.trustItem}>
                <Shield size={16} />
                <span>Background Checked</span>
              </div>
              <div className={styles.trustItem}>
                <CreditCard size={16} />
                <span>Secure Payments</span>
              </div>
            </div>
          </div>

          <div className={styles.heroVisual}>
            <div className={styles.heroCard}>
              <div className={styles.heroCardBadge}>
                <Star size={14} fill="currentColor" /> 4.9
              </div>
              <div className={styles.heroCardContent}>
                <div className={styles.heroCardAvatar}>RS</div>
                <div>
                  <p className={styles.heroCardName}>Rajesh S.</p>
                  <p className={styles.heroCardRole}>Electrician · Delhi</p>
                </div>
              </div>
              <p className={styles.heroCardStat}>127 jobs completed</p>
            </div>
            <div className={`${styles.heroCard} ${styles.heroCard2}`}>
              <div className={styles.heroCardBadge}>
                <Star size={14} fill="currentColor" /> 4.8
              </div>
              <div className={styles.heroCardContent}>
                <div className={`${styles.heroCardAvatar} ${styles.avatar2}`}>PK</div>
                <div>
                  <p className={styles.heroCardName}>Priya K.</p>
                  <p className={styles.heroCardRole}>Chef · Mumbai</p>
                </div>
              </div>
              <p className={styles.heroCardStat}>89 jobs completed</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Categories ────────────────────────────────────── */}
      <section className={`page-section ${styles.catSection}`}>
        <div className="container">
          <div className={styles.sectionHeader}>
            <h2 className="display-md">What do you need help with?</h2>
            <p className="text-md text-muted">Browse by service category</p>
          </div>

          <div className={styles.catGrid}>
            {(categories.length > 0 ? categories : CATEGORIES).map((cat) => {
              const catInfo = CATEGORIES.find(c => c.value === (cat.value || cat.slug));
              return (
                <Link
                  key={cat.value}
                  href={`/browse?category=${cat.value}`}
                  className={styles.catCard}
                  id={`cat-${cat.value}`}
                >
                  <span className={styles.catIcon}>{catInfo?.icon || '🔨'}</span>
                  <span className={styles.catLabel}>{cat.label}</span>
                  {cat.pro_count !== undefined && (
                    <span className={styles.catCount}>{cat.pro_count} pros</span>
                  )}
                  <ChevronRight size={16} className={styles.catArrow} />
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── How It Works ──────────────────────────────────── */}
      <section className={`page-section page-section--alt`}>
        <div className="container">
          <div className={styles.sectionHeader}>
            <h2 className="display-md">How HireHub works</h2>
            <p className="text-md text-muted">Three steps to getting the job done</p>
          </div>

          <div className={styles.stepsGrid}>
            <div className={styles.step}>
              <div className={styles.stepNumber}>1</div>
              <h3 className="heading-md">Search & Choose</h3>
              <p className="text-md text-muted">
                Browse through verified professionals by category, location, and ratings.
                Read real reviews from other customers.
              </p>
            </div>
            <div className={styles.step}>
              <div className={styles.stepNumber}>2</div>
              <h3 className="heading-md">Book & Pay</h3>
              <p className="text-md text-muted">
                Schedule a time, describe your job, and choose to pay online or in cash.
                Razorpay-secured payments.
              </p>
            </div>
            <div className={styles.step}>
              <div className={styles.stepNumber}>3</div>
              <h3 className="heading-md">Get It Done</h3>
              <p className="text-md text-muted">
                The pro arrives, does the work, and you confirm completion with a one-time code.
                Simple, safe, done.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Become a Pro CTA ──────────────────────────────── */}
      <section className={`page-section ${styles.ctaSection}`}>
        <div className="container">
          <div className={styles.ctaCard}>
            <div className={styles.ctaContent}>
              <h2 className="display-md">Earn on your own terms</h2>
              <p className="text-lg text-muted" style={{ maxWidth: 480, marginTop: 12 }}>
                Join HireHub as a professional. Set your own rates, manage your schedule,
                and grow your client base.
              </p>
              <div className={styles.ctaFeatures}>
                <div className={styles.ctaFeature}>
                  <Users size={18} />
                  <span>10+ service categories</span>
                </div>
                <div className={styles.ctaFeature}>
                  <CreditCard size={18} />
                  <span>Direct payments</span>
                </div>
                <div className={styles.ctaFeature}>
                  <Star size={18} />
                  <span>Build your reputation</span>
                </div>
              </div>
              <Link href="/become-pro" className="btn btn--accent btn--lg" id="cta-become-pro">
                Start Your Application <ArrowRight size={18} />
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
