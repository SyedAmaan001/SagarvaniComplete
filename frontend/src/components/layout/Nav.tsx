"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Menu, X, Terminal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion, useScroll, useMotionTemplate, useTransform } from "framer-motion";

export function Nav() {
  const [isOpen, setIsOpen] = useState(false);
  const { scrollY } = useScroll();
  
  // Transition background opacity based on scroll
  const bgOpacity = useTransform(scrollY, [0, 80], [0, 0.95]);
  const backgroundColor = useMotionTemplate`rgba(5, 10, 48, ${bgOpacity})`;
  const borderBottom = useMotionTemplate`1px solid rgba(27, 42, 107, ${bgOpacity})`;

  const links = [
    { label: "Solutions", href: "/solutions" },
    { label: "How It Works", href: "/how-it-works" },
    { label: "Access Channels", href: "/access" },
    { label: "Data Sources", href: "/data-sources" },
    { label: "Contact", href: "/contact" },
  ];

  return (
    <motion.header
      className="fixed top-0 left-0 right-0 z-50 flex items-center h-20 px-6 lg:px-12 backdrop-blur-md"
      style={{
        backgroundColor,
        borderBottom,
      }}
    >
      <div className="flex items-center justify-between w-full max-w-7xl mx-auto">
        {/* Sagarvani Brand Logo */}
        <Link href="/" className="flex items-center gap-3.5 group">
          <div className="relative w-12 h-12 rounded-xl overflow-hidden border border-[#1B2A6B]/80 bg-[#0B1550]/40 p-1 flex items-center justify-center shadow-[0_0_20px_rgba(0,255,255,0.2)] group-hover:border-[#00FFFF]/60 group-hover:shadow-[0_0_25px_rgba(0,255,255,0.3)] transition-all">
            <Image
              src="/logo.png"
              alt="Sagarvani Logo"
              width={48}
              height={48}
              className="object-contain w-full h-full scale-105"
              priority
            />
          </div>
          <div className="flex flex-col">
            <span className="font-heading font-bold text-xl tracking-wider uppercase text-foreground leading-none">
              Sagarvani
            </span>
            <span className="text-[10px] text-primary tracking-widest uppercase font-semibold mt-1">
              ORCA Marine Intelligence
            </span>
          </div>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-8">
          {links.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="text-sm font-medium text-text-secondary hover:text-primary transition-colors tracking-wide"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* Action Button: Try Sagarvani -> /dashboard */}
        <div className="hidden md:flex items-center gap-3">
          <Button 
            asChild 
            className="bg-primary text-bg-sunken hover:bg-primary/90 font-bold px-6 shadow-[0_0_20px_rgba(0,255,255,0.25)] hover:scale-[1.03] transition-transform duration-150"
          >
            <Link href="/dashboard" className="flex items-center gap-2">
              <Terminal className="size-4" />
              <span>Try Sagarvani</span>
            </Link>
          </Button>
        </div>

        {/* Mobile menu button */}
        <button
          className="md:hidden text-foreground p-2 rounded-lg border border-border bg-bg-elevated"
          onClick={() => setIsOpen(!isOpen)}
          aria-label="Toggle navigation menu"
        >
          {isOpen ? <X size={22} className="text-primary" /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile Nav */}
      {isOpen && (
        <div className="absolute top-20 left-0 right-0 bg-bg-elevated/95 border-b border-border p-6 flex flex-col gap-5 md:hidden shadow-2xl backdrop-blur-xl">
          {links.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="text-base font-medium text-foreground hover:text-primary py-1 transition-colors"
              onClick={() => setIsOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <Button asChild className="bg-primary text-bg-sunken font-bold w-full mt-2 py-6">
            <Link href="/dashboard" onClick={() => setIsOpen(false)} className="flex items-center justify-center gap-2">
              <Terminal className="size-4" />
              <span>Try Sagarvani Console</span>
            </Link>
          </Button>
        </div>
      )}
    </motion.header>
  );
}
