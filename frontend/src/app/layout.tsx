import type { Metadata } from "next";
import { Inter, Unbounded } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
});

const unbounded = Unbounded({
  variable: "--font-heading",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Sagarvani — Conversational Marine Decision-Intelligence Platform",
  description: "Conversational marine decision-intelligence platform powered by ORCA multi-agent reasoning, fusing ocean, weather, and geospatial data into validated, explainable recommendations.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${unbounded.variable} dark`}>
      <body className="min-h-full flex flex-col font-sans bg-background text-foreground">
        {children}
      </body>
    </html>
  );
}
