import './globals.css';
import ClientLayout from '@/components/ClientLayout';

export const metadata = {
  title: 'HireHub — Find Trusted Pros for Any Job',
  description: 'Book verified professionals for plumbing, electrical, cleaning, cooking and more. Secure payments, OTP-confirmed completion, and honest reviews.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <ClientLayout>
          {children}
        </ClientLayout>
      </body>
    </html>
  );
}
