// src/pages/HelpPage.jsx - Help & Safety Center
import React from 'react';
import PageContainer from '../components/ui/PageContainer';
import SectionHeader from '../components/ui/SectionHeader';
import AlertBanner from '../components/ui/AlertBanner';
import Card from '../components/common/Card';
import Accordion from '../components/common/Accordion';
import { Mail, Phone, ShieldCheck, HeartPulse, HelpCircle } from 'lucide-react';

const HelpPage = () => {
  const faqs = [
    {
      q: 'How does BluCare+ ensure clinical safety during symptom assessments?',
      a: 'BluCare+ evaluates input against verified clinical practice protocols (WHO & ICD-11 standard guidelines). If high-risk indicators are detected, the system immediately prompts acute emergency care options.',
    },
    {
      q: 'Is my personal health data encrypted and HIPAA compliant?',
      a: 'Yes. All personal demographics, medical journals, and evaluation records are encrypted in transit and at rest using AES-256 GCM encryption following HIPAA standards.',
    },
    {
      q: 'Can I share my evaluation brief with my doctor?',
      a: 'Absolutely. You can visit the consultation view or export structured clinical notes formatted specifically for physician review.',
    },
    {
      q: 'What should I do if I am experiencing a medical emergency?',
      a: 'Do not rely solely on digital symptom assessments during an acute crisis. Use the Emergency SOS button in the navigation bar or call local emergency medical services immediately (108 / 911 / 112).',
    },
  ];

  return (
    <PageContainer>
      <SectionHeader
        title="Help &"
        highlightTitle="Safety Center"
        description="Clinical safety disclaimers, FAQs, and support channels."
        tag="Support Workspace"
      />

      <AlertBanner
        type="info"
        title="Important Clinical Disclaimer"
        message="BluCare+ provides clinical guidance and symptom triage support based on medical practice standards. It is designed to assist care decisions and is not a replacement for professional in-person medical diagnosis or emergency hospital treatment."
      />

      <div className="space-y-4">
        <h2 className="text-base sm:text-lg font-semibold text-[var(--text-primary)]">
          Frequently Asked Questions
        </h2>
        <div className="space-y-2.5">
          {faqs.map((faq, idx) => (
            <Accordion
              key={idx}
              title={faq.q}
              defaultOpen={idx === 0}
            >
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed pt-2">
                {faq.a}
              </p>
            </Accordion>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
        <Card elevated bordered className="space-y-2.5 p-5">
          <div className="flex items-center gap-2 text-[var(--clinical-teal)] font-semibold text-xs">
            <Mail size={16} /> Support & Medical Queries
          </div>
          <p className="text-xs text-[var(--text-muted)]">Reach our clinical support team 24/7</p>
          <a
            href="mailto:support@ragblucare.ai"
            className="text-xs sm:text-sm text-[var(--clinical-teal)] font-medium hover:underline block"
          >
            support@ragblucare.ai
          </a>
        </Card>

        <Card elevated bordered className="space-y-2.5 p-5">
          <div className="flex items-center gap-2 text-[var(--severity-emergency)] font-semibold text-xs">
            <Phone size={16} /> Direct Emergency Helpline
          </div>
          <p className="text-xs text-[var(--text-muted)]">24/7 Rapid ambulance & casualty triage</p>
          <a
            href="tel:108"
            className="text-xs sm:text-sm text-[var(--severity-emergency)] font-bold hover:underline block"
          >
            Dial 108 (India) / 112 (Unified)
          </a>
        </Card>
      </div>
    </PageContainer>
  );
};

export default HelpPage;
