'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { apiGet, apiPost } from '@/lib/api';
import { useToast } from '@/context/ToastContext';
import { CATEGORIES } from '@/lib/constants';
import { Calendar, Clock, CreditCard, Banknote, ArrowRight, Loader2 } from 'lucide-react';
import styles from './book.module.css';

export default function BookPage() {
  const { proId } = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const [pro, setPro] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    category: '',
    description: '',
    scheduled_at: '',
    duration_hours: '1',
    payment_mode: 'cash',
    locality: '',
  });

  useEffect(() => {
    const fetchPro = async () => {
      const { data } = await apiGet(`/pros/user/${proId}/`);
      if (data && !data.error) {
        setPro(data);
        setForm(f => ({ ...f, category: data.category }));
      }
      setLoading(false);
    };
    fetchPro();
  }, [proId]);

  const amount = pro?.hourly_rate ? (parseFloat(pro.hourly_rate) * parseFloat(form.duration_hours || 1)).toFixed(2) : 0;

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!form.scheduled_at) {
      toast.error('Please select a date and time.');
      return;
    }

    setSubmitting(true);

    const { data, error } = await apiPost('/bookings/', {
      pro: proId,
      category: form.category,
      description: form.description,
      scheduled_at: new Date(form.scheduled_at).toISOString(),
      duration_hours: parseFloat(form.duration_hours),
      amount: parseFloat(amount),
      payment_mode: form.payment_mode,
      locality: form.locality,
    });

    setSubmitting(false);

    if (error) {
      toast.error(typeof error === 'string' ? error : 'Failed to create booking.');
      return;
    }

    // If prepaid, initiate payment
    if (form.payment_mode === 'prepaid' && data?.id) {
      await initiatePayment(data.id);
    } else {
      toast.success('Booking created! The pro will confirm shortly.');
      router.push('/bookings');
    }
  };

  const initiatePayment = async (bookingId) => {
    const { data, error } = await apiPost('/payments/initiate/', {
      booking_id: bookingId,
    });

    if (error) {
      toast.error('Booking created but payment failed. You can pay later from My Bookings.');
      router.push('/bookings');
      return;
    }

    // Open Razorpay checkout
    const options = {
      key: data.key_id,
      amount: data.amount,
      currency: data.currency,
      name: data.name,
      description: data.description,
      order_id: data.order_id,
      prefill: data.prefill,
      handler: async function (response) {
        const verifyRes = await apiPost('/payments/verify/', {
          razorpay_order_id: response.razorpay_order_id,
          razorpay_payment_id: response.razorpay_payment_id,
          razorpay_signature: response.razorpay_signature,
        });

        if (verifyRes.error) {
          toast.error('Payment verification failed.');
        } else {
          toast.success('Payment successful! Booking confirmed.');
        }
        router.push('/bookings');
      },
      theme: { color: '#1a1a1a' },
    };

    if (typeof window !== 'undefined' && window.Razorpay) {
      const rzp = new window.Razorpay(options);
      rzp.open();
    } else {
      // Load Razorpay script dynamically
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.onload = () => {
        const rzp = new window.Razorpay(options);
        rzp.open();
      };
      document.body.appendChild(script);
    }
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
        <h1 className="display-md" style={{ marginBottom: 8 }}>Book a Service</h1>
        <p className="text-md text-muted" style={{ marginBottom: 32 }}>
          {pro ? `Booking with ${pro.full_name}` : 'Create a new booking'}
        </p>

        <form onSubmit={handleSubmit} className={styles.form}>
          {/* Category */}
          <div className="form-group">
            <label className="form-label" htmlFor="book-category">Service Category</label>
            <select
              id="book-category"
              name="category"
              className="form-input"
              value={form.category}
              onChange={handleChange}
            >
              {CATEGORIES.map(cat => (
                <option key={cat.value} value={cat.value}>{cat.label}</option>
              ))}
            </select>
          </div>

          {/* Description */}
          <div className="form-group">
            <label className="form-label" htmlFor="book-description">Describe the Job</label>
            <textarea
              id="book-description"
              name="description"
              className="form-input"
              placeholder="e.g. Fix leaking kitchen tap, replace washers if needed"
              value={form.description}
              onChange={handleChange}
              rows={3}
            />
          </div>

          {/* Date & Time */}
          <div className={styles.row}>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label" htmlFor="book-date">
                <Calendar size={14} style={{ display: 'inline', marginRight: 4 }} />
                Date & Time
              </label>
              <input
                type="datetime-local"
                id="book-date"
                name="scheduled_at"
                className="form-input"
                value={form.scheduled_at}
                onChange={handleChange}
                min={new Date().toISOString().slice(0, 16)}
              />
            </div>
            <div className="form-group" style={{ flex: 0.5 }}>
              <label className="form-label" htmlFor="book-duration">
                <Clock size={14} style={{ display: 'inline', marginRight: 4 }} />
                Duration (hrs)
              </label>
              <select
                id="book-duration"
                name="duration_hours"
                className="form-input"
                value={form.duration_hours}
                onChange={handleChange}
              >
                {[0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 8].map(h => (
                  <option key={h} value={h}>{h} {h === 1 ? 'hour' : 'hours'}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Location */}
          <div className="form-group">
            <label className="form-label" htmlFor="book-locality">Location / Address</label>
            <input
              type="text"
              id="book-locality"
              name="locality"
              className="form-input"
              placeholder="e.g. Sector 15, Gurgaon"
              value={form.locality}
              onChange={handleChange}
            />
          </div>

          {/* Payment Mode */}
          <div className="form-group">
            <label className="form-label">Payment Mode</label>
            <div className={styles.paymentModes}>
              <label className={`${styles.paymentOption} ${form.payment_mode === 'cash' ? styles.paymentActive : ''}`}>
                <input
                  type="radio"
                  name="payment_mode"
                  value="cash"
                  checked={form.payment_mode === 'cash'}
                  onChange={handleChange}
                  className="sr-only"
                />
                <Banknote size={20} />
                <div>
                  <p className={styles.paymentTitle}>Cash on Delivery</p>
                  <p className={styles.paymentDesc}>Pay when the job is done</p>
                </div>
              </label>
              <label className={`${styles.paymentOption} ${form.payment_mode === 'prepaid' ? styles.paymentActive : ''}`}>
                <input
                  type="radio"
                  name="payment_mode"
                  value="prepaid"
                  checked={form.payment_mode === 'prepaid'}
                  onChange={handleChange}
                  className="sr-only"
                />
                <CreditCard size={20} />
                <div>
                  <p className={styles.paymentTitle}>Pay Online</p>
                  <p className={styles.paymentDesc}>Secure payment via Razorpay</p>
                </div>
              </label>
            </div>
          </div>

          {/* Price Summary */}
          <div className={styles.summary}>
            <div className={styles.summaryRow}>
              <span>Rate</span>
              <span>₹{pro?.hourly_rate ? parseFloat(pro.hourly_rate).toLocaleString() : '—'}/hr</span>
            </div>
            <div className={styles.summaryRow}>
              <span>Duration</span>
              <span>{form.duration_hours} hours</span>
            </div>
            <div className={`${styles.summaryRow} ${styles.summaryTotal}`}>
              <span>Total</span>
              <span>₹{parseFloat(amount).toLocaleString()}</span>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn--accent btn--full btn--lg"
            disabled={submitting}
            id="book-submit"
          >
            {submitting ? (
              <><Loader2 size={18} className={styles.spinner} /> Processing…</>
            ) : (
              <>Confirm Booking <ArrowRight size={18} /></>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
