import React from 'react';
import './globals.css';
import Navbar from '@/components/Navbar';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'DocMind — Internal Knowledge Assistant',
  description: 'Instant answers with exact source citations from internal company documents.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#f7f7f5] text-[#202124] font-sans antialiased selection:bg-slate-900 selection:text-white">
        <Navbar />
        <main className="min-h-screen px-4 pb-6 pt-20 sm:px-6 lg:ml-64 lg:px-9 lg:py-8">{children}</main>
      </body>
    </html>
  );
}
