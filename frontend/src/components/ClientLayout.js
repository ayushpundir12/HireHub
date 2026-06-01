'use client';

import { AuthProvider } from '@/context/AuthContext';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import Toast from '@/components/Toast';
import { ToastProvider } from '@/context/ToastContext';

export default function ClientLayout({ children }) {
  return (
    <AuthProvider>
      <ToastProvider>
        <Navbar />
        <main style={{ minHeight: `calc(100vh - var(--nav-height) - 200px)`, paddingTop: 'var(--nav-height)' }}>
          {children}
        </main>
        <Footer />
        <Toast />
      </ToastProvider>
    </AuthProvider>
  );
}
