import Link from 'next/link';
import styles from './Footer.module.css';

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={`container ${styles.inner}`}>
        <div className={styles.grid}>
          {/* Brand */}
          <div className={styles.brand}>
            <Link href="/" className={styles.logo}>
              <span className={styles.logoMark}>H</span>
              <span className={styles.logoText}>HireHub</span>
            </Link>
            <p className={styles.tagline}>
              Find trusted professionals for any job. Verified, reviewed, and reliable.
            </p>
          </div>

          {/* Links */}
          <div className={styles.col}>
            <h4 className={styles.colTitle}>For Clients</h4>
            <Link href="/browse" className={styles.link}>Find Pros</Link>
            <Link href="/bookings" className={styles.link}>My Bookings</Link>
            <Link href="/signup" className={styles.link}>Create Account</Link>
          </div>

          <div className={styles.col}>
            <h4 className={styles.colTitle}>For Professionals</h4>
            <Link href="/become-pro" className={styles.link}>Become a Pro</Link>
            <Link href="/dashboard" className={styles.link}>Pro Dashboard</Link>
          </div>

          <div className={styles.col}>
            <h4 className={styles.colTitle}>Company</h4>
            <Link href="/" className={styles.link}>About Us</Link>
            <Link href="/" className={styles.link}>Contact</Link>
            <Link href="/" className={styles.link}>Privacy Policy</Link>
          </div>
        </div>

        <div className={styles.bottom}>
          <p className={styles.copy}>© {new Date().getFullYear()} HireHub. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
