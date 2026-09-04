"use client";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

export function FAQ() {
  const faqs = [
    {
      q: "What is Sagarvani?",
      a: "Sagarvani is a conversational marine decision-intelligence platform that combines ocean, weather, geospatial, and risk information through ORCA's collaborative agent architecture."
    },
    {
      q: "What is ORCA?",
      a: "ORCA is Sagarvani's orchestration and reasoning architecture. It coordinates specialist marine agents, combines their outputs, checks evidence for contradictions, and supports a validated, explainable response."
    },
    {
      q: "What data sources does Sagarvani use?",
      a: "The project design references INCOIS, IMD, ISRO Bhuvan/NRSC, Bhoonidhi, MOSDAC, BHASHINI and Sarvam AI, alongside supporting geospatial, weather and technology infrastructure."
    },
    {
      q: "Who is Sagarvani for?",
      a: "The primary focus is fishermen/coastal crews, maritime operators, researchers and disaster-management/coastal-safety users. The broader stakeholder model also includes aquaculture, tourism, offshore energy and policy/conservation."
    },
    {
      q: "How does it work without a smartphone?",
      a: "The product is designed around multiple access paths, including a helpline and low-bandwidth communication portal. Full production IVR integration is planned in subsequent phases beyond the current web MVP."
    },
    {
      q: "Does Sagarvani support voice?",
      a: "Yes. Voice input is included in the MVP interface, with the architecture prepared for BHASHINI/Sarvam-based multilingual speech services."
    },
    {
      q: "How does Sagarvani handle conflicting data?",
      a: "Conflicting or low-confidence outputs trigger a visible re-check/re-planning state. The system exposes the validation result rather than silently hiding uncertainty or picking a single source arbitrarily."
    },
    {
      q: "Does Sagarvani replace official authorities?",
      a: "No. It is a decision-support platform designed to synthesize evidence and explain recommendations. Official warnings and authorities (such as IMD cyclone bulletins and INCOIS high-wave advisories) remain essential sources of operational truth."
    },
    {
      q: "What problem statement is it built for?",
      a: "Smart India Hackathon 2026, SIH26176 — ORCA: Marine Ecosystem Reasoning with Collaborative Agents, under the Disaster Management theme / Software category, developed by Team Helios Luna (Dayananda Sagar University)."
    }
  ];

  return (
    <section id="faq" className="py-24 md:py-32 px-6 lg:px-12 bg-bg-sunken border-b border-border">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <span className="text-primary text-xs font-heading font-bold uppercase tracking-widest bg-primary/10 border border-primary/20 px-3.5 py-1 rounded-full">
            Questions & Answers
          </span>
          <h2 className="font-heading font-bold text-3xl md:text-5xl text-foreground mt-4">
            Frequently Asked Questions
          </h2>
          <p className="mt-3 text-text-secondary text-base">
            Everything you need to know about Sagarvani and the ORCA architecture.
          </p>
        </div>

        <Accordion className="w-full space-y-4">
          {faqs.map((faq, idx) => (
            <AccordionItem 
              key={idx} 
              value={`item-${idx}`} 
              className="bg-bg-elevated/70 border border-border rounded-xl px-6 data-[state=open]:border-primary/50 transition-colors shadow-sm"
            >
              <AccordionTrigger className="text-base md:text-lg font-heading font-semibold hover:no-underline hover:text-primary py-5 text-left text-foreground">
                {faq.q}
              </AccordionTrigger>
              <AccordionContent className="text-text-secondary text-sm md:text-base leading-relaxed pb-6">
                {faq.a}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
}
