import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = { title: 'سرمایه‌گزین', description: 'سرمایه‌گزین', icons: { icon: { url: '/favicon.ico', type: 'image/x-icon', sizes: '16x16 32x32 48x48 64x64' } } };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="fa" dir="rtl"><body>{children}</body></html>;
}
