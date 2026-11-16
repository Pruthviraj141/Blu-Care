// src/pages/ProfilePage.jsx
import React, { useState, useEffect } from 'react';
import { useAuth, useUser } from '@clerk/clerk-react';
import PageContainer from '../components/ui/PageContainer';
import SectionHeader from '../components/ui/SectionHeader';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import { userApi } from '../utils/api';
import { Phone, AlertCircle, CheckCircle2, Edit3, User, ShieldCheck } from 'lucide-react';

const ProfilePage = () => {
  const { getToken } = useAuth();
  const { user } = useUser();
  const [profile, setProfile] = useState({
    name: user?.fullName || 'Patient',
    email: user?.primaryEmailAddress?.emailAddress || 'patient@ragblucare.ai',
    phone: '+91 94038 71129',
    dob: 'October 14, 1998',
    bloodGroup: 'O Positive (O+)',
    allergies: 'Penicillin, Dust Mites',
    emergencyContact: 'Sanket K. (+91 98765 43210)',
  });

  useEffect(() => {
    async function loadProfile() {
      try {
        const data = await userApi.getProfile({ getToken });
        if (data) setProfile((prev) => ({ ...prev, ...data }));
      } catch (err) {
        // Retain fallback
      }
    }
    loadProfile();
  }, [getToken]);

  return (
    <PageContainer>
      <SectionHeader
        title="Patient Identity &"
        highlightTitle="Profile"
        description="Personal medical demographics, emergency contacts, and medical safety flags."
        tag="Account Workspace"
        actions={
          <Button variant="secondary" size="sm" icon={Edit3}>
            Edit Profile
          </Button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-8 space-y-5">
          <Card elevated bordered className="space-y-5 p-5 sm:p-6">
            <div className="flex items-center gap-4 pb-5 border-b border-[var(--border-subtle)]">
              {user?.imageUrl ? (
                <img
                  src={user.imageUrl}
                  alt={profile.name}
                  className="w-16 h-16 rounded-[10px] border border-[var(--border-subtle)] object-cover"
                />
              ) : (
                <div className="w-16 h-16 rounded-[10px] bg-[var(--clinical-teal)]/15 border border-[var(--clinical-teal)]/30 text-[var(--clinical-teal)] font-semibold text-2xl flex items-center justify-center">
                  {profile.name.charAt(0)}
                </div>
              )}
              <div>
                <h2 className="text-xl font-semibold text-[var(--text-primary)]">{profile.name}</h2>
                <p className="text-xs text-[var(--text-muted)] font-mono">Patient ID: BLU-2026-8902</p>
                <div className="inline-flex items-center gap-1.5 px-2 py-0.5 mt-2 rounded-[4px] bg-[var(--severity-routine)]/15 border border-[var(--severity-routine)]/30 text-[var(--severity-routine)] text-[11px] font-mono">
                  <CheckCircle2 size={11} /> HIPAA Encrypted Record
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-[6px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-1">
                <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-mono">Email Address</span>
                <p className="text-[var(--text-primary)] font-medium text-xs sm:text-sm">{profile.email}</p>
              </div>
              <div className="p-3 rounded-[6px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-1">
                <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-mono">Phone Number</span>
                <p className="text-[var(--text-primary)] font-medium text-xs sm:text-sm">{profile.phone}</p>
              </div>
              <div className="p-3 rounded-[6px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-1">
                <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-mono">Date of Birth</span>
                <p className="text-[var(--text-primary)] font-medium text-xs sm:text-sm">{profile.dob}</p>
              </div>
              <div className="p-3 rounded-[6px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-1">
                <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-mono">Blood Group</span>
                <p className="text-[var(--clinical-teal)] font-medium text-xs sm:text-sm">{profile.bloodGroup}</p>
              </div>
            </div>
          </Card>

          <Card elevated bordered className="space-y-3 p-5">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
              <AlertCircle size={16} className="text-[var(--severity-emergency)]" /> Allergies & Medical Safety Alerts
            </h3>
            <div className="p-3.5 rounded-[6px] bg-[var(--severity-emergency)]/10 border border-[var(--severity-emergency)]/25 text-xs space-y-1">
              <span className="font-semibold text-[var(--severity-emergency)]">Known Drug Allergies</span>
              <p className="text-[var(--text-secondary)]">{profile.allergies}</p>
            </div>
          </Card>
        </div>

        <div className="lg:col-span-4 space-y-4">
          <Card elevated bordered className="space-y-3 p-5">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
              <Phone size={16} className="text-[var(--clinical-teal)]" /> Primary Emergency Contact
            </h3>
            <div className="p-3.5 rounded-[6px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-1 text-xs">
              <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-mono">Kin / Contact</span>
              <p className="font-medium text-[var(--text-primary)]">{profile.emergencyContact}</p>
            </div>
            <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
              This contact is automatically notified if an emergency SOS event is triggered during triage.
            </p>
          </Card>

          <Card elevated bordered className="space-y-2.5 p-5 text-xs text-[var(--text-secondary)]">
            <div className="flex items-center gap-2 text-[var(--clinical-teal)] font-semibold text-xs">
              <ShieldCheck size={16} /> Privacy & Data Rights
            </div>
            <p className="leading-relaxed">
              Your patient demographics are retained strictly for clinical context within your private triage sessions. No third-party data tracking.
            </p>
          </Card>
        </div>
      </div>
    </PageContainer>
  );
};

export default ProfilePage;
