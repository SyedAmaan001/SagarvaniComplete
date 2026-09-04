"use client";
import { motion } from "framer-motion";
import { Globe, Phone, RadioTower } from "lucide-react";

const paths = [
  { label: "Web / App", icon: Globe, desc: "Full conversational dashboard for researchers and operators." },
  { label: "Helpline", icon: Phone, desc: "Voice access for fishermen — no smartphone required." },
  { label: "Low-Bandwidth Portal", icon: RadioTower, desc: "Lightweight access for poor-connectivity coastal areas." },
];

export function AccessEverywhere() {
  return (
    <section className="py-24 md:py-32 border-b border-border">
      <div className="max-w-5xl mx-auto px-6 lg:px-12 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
        >
          <span className="text-primary text-sm font-semibold tracking-wide uppercase">Access Everywhere</span>
          <h2 className="font-heading font-bold text-3xl md:text-5xl text-foreground mt-3 mb-4">
            One intelligence engine, three access paths.
          </h2>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 mt-16">
          {paths.map((p, i) => (
            <motion.div
              key={p.label}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="flex flex-col items-center"
            >
              <div className="w-16 h-16 rounded-full border border-border bg-bg-elevated flex items-center justify-center mb-4">
                <p.icon className="text-primary" size={26} strokeWidth={1.75} />
              </div>
              <h3 className="font-heading font-semibold text-lg text-foreground mb-2">{p.label}</h3>
              <p className="text-text-secondary text-sm max-w-[220px]">{p.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
