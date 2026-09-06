import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import type { ReactNode } from "react";
import "./globals.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" });
const geistMono = Geist_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: {
    default: "Pose Embed research tracker",
    template: "%s | Pose Embed",
  },
  description:
    "A public weekly execution plan for robust one-shot human-motion retrieval research.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" className={`${geist.variable} ${geistMono.variable}`}>
      <body>
        <a className="skip-link" href="#main-content">
          Skip to content
        </a>
        <header className="site-header">
          <div className="header-inner">
            <Link className="wordmark" href="/" aria-label="Pose Embed home">
              <span aria-hidden="true" className="wordmark-mark">PE</span>
              <span>Pose Embed</span>
            </Link>
            <nav aria-label="Primary navigation" className="primary-nav">
              <Link href="/">Plan</Link>
              <Link href="/protocol">Protocol</Link>
              <Link href="/literature">Literature</Link>
              <Link href="/edit">Update</Link>
            </nav>
          </div>
        </header>
        <main id="main-content">{children}</main>
        <footer className="site-footer">
          <div className="footer-inner">
            <p>Robust human-motion retrieval, Fall 2026.</p>
            <div className="footer-links">
              <Link href="/api/export?format=markdown">Export Markdown</Link>
              <Link href="/api/health">System status</Link>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
