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
      <body className="min-h-screen bg-[#f7f9fa] font-sans text-[#171a1d] antialiased selection:bg-slate-900 selection:text-white">
        <Navbar />
        <main className="min-h-screen pt-16 lg:ml-[220px] lg:pt-0">{children}</main>
      </body>
    </html>
  );
}
