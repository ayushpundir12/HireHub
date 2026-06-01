'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { apiGet } from '@/lib/api';
import { CATEGORIES } from '@/lib/constants';
import ProCard from '@/components/ProCard';
import { Search, SlidersHorizontal, X, Loader2 } from 'lucide-react';
import styles from './browse.module.css';

export default function BrowsePage() {
  const searchParams = useSearchParams();
  const [pros, setPros] = useState([]);
  const [loading, setLoading] = useState(true);
  const [nextCursor, setNextCursor] = useState(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  const [filters, setFilters] = useState({
    category: searchParams.get('category') || '',
    city: searchParams.get('city') || '',
    rating_min: '',
    available: '',
  });

  const fetchPros = async (cursor = null, append = false) => {
    const params = new URLSearchParams();
    if (filters.category) params.set('category', filters.category);
    if (filters.city) params.set('city', filters.city);
    if (filters.rating_min) params.set('rating_min', filters.rating_min);
    if (filters.available) params.set('available', filters.available);
    if (cursor) params.set('cursor', cursor);

    const { data, error } = await apiGet(`/pros/?${params.toString()}`);

    if (data) {
      if (append) {
        setPros(prev => [...prev, ...(data.results || [])]);
      } else {
        setPros(data.results || []);
      }
      setNextCursor(data.next ? new URL(data.next).searchParams.get('cursor') : null);
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchPros().finally(() => setLoading(false));
  }, [filters]);

  const handleLoadMore = async () => {
    if (!nextCursor) return;
    setLoadingMore(true);
    await fetchPros(nextCursor, true);
    setLoadingMore(false);
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({ category: '', city: '', rating_min: '', available: '' });
  };

  const activeFilterCount = Object.values(filters).filter(Boolean).length;

  return (
    <div className={styles.page}>
      <div className="container">
        {/* Header */}
        <div className={styles.header}>
          <div>
            <h1 className="display-md">Find Professionals</h1>
            <p className="text-md text-muted" style={{ marginTop: 4 }}>
              Browse verified service providers in your area
            </p>
          </div>
          <button
            className={`btn btn--outline ${styles.filterToggle}`}
            onClick={() => setShowFilters(!showFilters)}
            id="browse-filter-toggle"
          >
            <SlidersHorizontal size={16} />
            Filters
            {activeFilterCount > 0 && (
              <span className={styles.filterCount}>{activeFilterCount}</span>
            )}
          </button>
        </div>

        <div className={styles.layout}>
          {/* Filters Sidebar */}
          <aside className={`${styles.sidebar} ${showFilters ? styles.sidebarOpen : ''}`}>
            <div className={styles.sidebarHeader}>
              <h3 className="heading-md">Filters</h3>
              {activeFilterCount > 0 && (
                <button className="btn btn--ghost btn--sm" onClick={clearFilters}>
                  Clear all
                </button>
              )}
              <button className={styles.closeSidebar} onClick={() => setShowFilters(false)}>
                <X size={20} />
              </button>
            </div>

            <div className={styles.filterGroup}>
              <label className="form-label">Category</label>
              <select
                className="form-input"
                value={filters.category}
                onChange={(e) => handleFilterChange('category', e.target.value)}
                id="filter-category"
              >
                <option value="">All Categories</option>
                {CATEGORIES.map(cat => (
                  <option key={cat.value} value={cat.value}>{cat.label}</option>
                ))}
              </select>
            </div>

            <div className={styles.filterGroup}>
              <label className="form-label">City</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Mumbai"
                value={filters.city}
                onChange={(e) => handleFilterChange('city', e.target.value)}
                id="filter-city"
              />
            </div>

            <div className={styles.filterGroup}>
              <label className="form-label">Minimum Rating</label>
              <select
                className="form-input"
                value={filters.rating_min}
                onChange={(e) => handleFilterChange('rating_min', e.target.value)}
                id="filter-rating"
              >
                <option value="">Any Rating</option>
                <option value="4.5">4.5+ Stars</option>
                <option value="4.0">4.0+ Stars</option>
                <option value="3.5">3.5+ Stars</option>
                <option value="3.0">3.0+ Stars</option>
              </select>
            </div>

            <div className={styles.filterGroup}>
              <label className="form-label">Availability</label>
              <select
                className="form-input"
                value={filters.available}
                onChange={(e) => handleFilterChange('available', e.target.value)}
                id="filter-available"
              >
                <option value="">All</option>
                <option value="true">Available Now</option>
              </select>
            </div>
          </aside>

          {/* Results */}
          <div className={styles.results}>
            {loading ? (
              <div className={styles.loadingGrid}>
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className={styles.skeletonCard}>
                    <div className="skeleton" style={{ width: 52, height: 52, borderRadius: '50%' }} />
                    <div style={{ flex: 1 }}>
                      <div className="skeleton" style={{ width: '60%', height: 16, marginBottom: 8 }} />
                      <div className="skeleton" style={{ width: '40%', height: 12 }} />
                    </div>
                  </div>
                ))}
              </div>
            ) : pros.length === 0 ? (
              <div className="empty-state">
                <Search size={48} />
                <h3 className="heading-md" style={{ marginTop: 16 }}>No pros found</h3>
                <p className="text-md text-muted">Try adjusting your filters or search in a different area</p>
              </div>
            ) : (
              <>
                <p className="text-sm text-muted" style={{ marginBottom: 16 }}>
                  {pros.length} professional{pros.length !== 1 ? 's' : ''} found
                </p>
                <div className={styles.proGrid}>
                  {pros.map(pro => (
                    <ProCard key={pro.id} pro={pro} />
                  ))}
                </div>

                {nextCursor && (
                  <div className={styles.loadMore}>
                    <button
                      className="btn btn--outline"
                      onClick={handleLoadMore}
                      disabled={loadingMore}
                      id="browse-load-more"
                    >
                      {loadingMore ? (
                        <><Loader2 size={16} className={styles.spinner} /> Loading…</>
                      ) : (
                        'Load More'
                      )}
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
