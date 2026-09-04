"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export function CTABanner() {
  return (
    <motion.section 
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.8 }}
      className="py-24 px-6 lg:px-12 bg-bg-elevated border-y border-border relative overflow-hidden"
    >
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/10 via-bg-elevated to-bg-elevated"></div>
      
      <div className="max-w-4xl mx-auto relative z-10 text-center">
        <h2 className="font-heading font-bold text-4xl md:text-5xl text-foreground mb-6">Step Into Sagarvani</h2>
        <p className="text-lg text-muted-foreground mb-10 max-w-2xl mx-auto">
          From open water to the coastline — one validated answer, however you reach us. Experience marine decision-intelligence powered by ORCA.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button asChild size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 font-bold hover:scale-[1.03] transition-transform duration-150">
            <Link href="/dashboard">Launch Console</Link>
          </Button>
          <Button asChild variant="outline" size="lg" className="border-border text-foreground hover:bg-background hover:text-primary transition-colors">
            <Link href="/contact">Talk to the team</Link>
          </Button>
        </div>
      </div>
    </motion.section>
  );
}
