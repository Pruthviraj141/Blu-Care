// src/pages/SignInPage.jsx - World-Class Authentication Portal
import React from 'react';
import { SignIn } from '@clerk/clerk-react';
import { NavLink } from 'react-router-dom';
import { Activity, ShieldCheck } from 'lucide-react';

const SignInPage = () => {
  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center bg-[var(--bg-app)] text-[var(--text-primary)] relative p-4 selection:bg-[var(--clinical-teal)]/20 selection:text-[var(--clinical-teal)]">
      {/* Main Container */}
      <div className="w-full max-w-md z-10 space-y-5">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <NavLink to="/" className="inline-flex items-center gap-2 no-underline group mb-1">
            <div className="w-9 h-9 rounded-[8px] bg-[var(--clinical-teal)]/15 border border-[var(--clinical-teal)]/30 text-[var(--clinical-teal)] flex items-center justify-center font-bold text-sm aspect-square shrink-0 group-hover:bg-[var(--clinical-teal)]/25 transition-colors">
              <Activity size={18} />
            </div>
            <span className="text-[var(--text-primary)] font-semibold text-2xl tracking-tight">
              BluCare<span className="text-[var(--clinical-teal)]">+</span>
            </span>
          </NavLink>

          <p className="text-xs text-[var(--text-muted)] font-mono uppercase tracking-wider">
            Clinical AI Healthcare Workspace
          </p>
        </div>

        {/* Clerk Sign In Card Wrapper */}
        <div className="p-3 sm:p-5 rounded-[12px] bg-[var(--bg-surface)] border border-[var(--border-strong)] shadow-xl flex justify-center">
          <SignIn
            routing="path"
            path="/sign-in"
            signUpUrl="/sign-up"
            fallbackRedirectUrl="/app/chat"
            appearance={{
              elements: {
                rootBox: 'w-full shadow-none bg-transparent',
                card: 'bg-transparent shadow-none p-2 w-full border-none',
                headerTitle: 'text-[var(--text-primary)] text-lg font-semibold font-sans',
                headerSubtitle: 'text-[var(--text-secondary)] text-xs font-sans',
                socialButtonsBlockButton: 'bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--text-primary)] hover:border-[var(--border-strong)] text-xs font-medium rounded-[6px]',
                socialButtonsBlockButtonText: 'text-[var(--text-primary)] font-medium text-xs',
                dividerLine: 'bg-[var(--border-subtle)]',
                dividerText: 'text-[var(--text-muted)] text-[10px] uppercase font-mono tracking-widest',
                formFieldLabel: 'text-[var(--text-secondary)] text-xs font-medium mb-1',
                formFieldInput: 'bg-[var(--bg-input)] border border-[var(--border-subtle)] text-[var(--text-primary)] rounded-[6px] text-sm focus:border-[var(--clinical-teal)] focus:ring-1 focus:ring-[var(--clinical-teal)] outline-none',
                formButtonPrimary: 'bg-[var(--accent-primary)] text-[#101316] font-medium text-sm py-2 rounded-[6px] hover:bg-[var(--accent-hover)] active:bg-[#607d9b] transition-all shadow-sm',
                footerActionLink: 'text-[var(--accent-primary)] hover:underline text-xs font-medium',
                footerActionText: 'text-[var(--text-muted)] text-xs',
                identityPreviewText: 'text-[var(--text-primary)] text-xs',
                identityPreviewEditButton: 'text-[var(--clinical-teal)] text-xs',
              },
            }}
          />
        </div>

        {/* Security badge */}
        <div className="flex items-center justify-center gap-1.5 text-[11px] font-mono text-[var(--text-muted)] text-center">
          <ShieldCheck size={13} className="text-[var(--clinical-teal)]" />
          <span>Encrypted HIPAA/GDPR Aligned Patient Authentication</span>
        </div>
      </div>
    </div>
  );
};

export default SignInPage;
