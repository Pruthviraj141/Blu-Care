// src/pages/SettingsPage.jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '@clerk/clerk-react';
import PageContainer from '../components/ui/PageContainer';
import SectionHeader from '../components/ui/SectionHeader';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import { useToast } from '../contexts/ToastContext';
import { userApi } from '../utils/api';
import { Cpu, Database, Sliders, CheckCircle2, ShieldCheck, Save } from 'lucide-react';

const SettingsPage = () => {
  const { addToast } = useToast();
  const { getToken } = useAuth();
  const [selectedProtocol, setSelectedProtocol] = useState('standard-care');
  const [sensitivity, setSensitivity] = useState('85');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    async function loadSettings() {
      try {
        const data = await userApi.getSettings({ getToken });
        if (data) {
          if (data.selectedProtocol) setSelectedProtocol(data.selectedProtocol);
          if (data.sensitivity) setSensitivity(data.sensitivity);
        }
      } catch (err) {
        // Retain fallback
      }
    }
    loadSettings();
  }, [getToken]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await userApi.updateSettings({ selectedProtocol, sensitivity }, { getToken });
      addToast('Care protocol & sensitivity preferences saved successfully!', 'success');
    } catch (err) {
      addToast(`Failed to save settings: ${err.message}`, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const protocols = [
    {
      id: 'standard-care',
      title: 'Standard Evidence-Based Allopathic Triage',
      desc: 'Strict adherence to conventional clinical guidelines and emergency thresholds.',
    },
    {
      id: 'integrative-ayurveda',
      title: 'Integrative Clinical & Curated Ayurvedic Guidance',
      desc: 'Pairs conventional standard of care with validated lifestyle & Ayurvedic complements.',
    },
    {
      id: 'conservative-emergency',
      title: 'Conservative Urgent Care Escalation',
      desc: 'Lowest threshold for recommending in-person urgent clinic visits.',
    },
  ];

  return (
    <PageContainer>
      <SectionHeader
        title="Platform & Care"
        highlightTitle="Settings"
        description="Configure clinical care protocols, assessment sensitivity thresholds, and multi-agent reasoning parameters."
        tag="System Workspace"
        actions={
          <Button
            variant="primary"
            size="sm"
            onClick={handleSave}
            loading={isSaving}
            icon={Save}
          >
            Save Configuration
          </Button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-8 space-y-5">
          <Card elevated bordered className="space-y-4 p-5 sm:p-6">
            <div className="flex items-center gap-2 text-[var(--text-primary)] font-semibold text-sm border-b border-[var(--border-subtle)] pb-3">
              <Cpu size={16} className="text-[var(--clinical-teal)]" /> Clinical Reasoning Standard
            </div>

            <div className="space-y-2.5">
              {protocols.map((proto) => {
                const isSelected = selectedProtocol === proto.id;
                return (
                  <label
                    key={proto.id}
                    onClick={() => setSelectedProtocol(proto.id)}
                    className={`block p-3.5 rounded-[8px] border transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-[var(--bg-elevated)] border-[var(--clinical-teal)] text-[var(--text-primary)] shadow-sm'
                        : 'bg-[var(--bg-surface)] border-[var(--border-subtle)] hover:border-[var(--border-strong)] text-[var(--text-secondary)]'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium text-xs sm:text-sm text-[var(--text-primary)]">
                          {proto.title}
                        </p>
                        <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                          {proto.desc}
                        </p>
                      </div>
                      <input
                        type="radio"
                        name="protocol"
                        checked={isSelected}
                        onChange={() => setSelectedProtocol(proto.id)}
                        className="mt-1 accent-[var(--clinical-teal)]"
                      />
                    </div>
                  </label>
                );
              })}
            </div>
          </Card>

          <Card elevated bordered className="space-y-4 p-5 sm:p-6">
            <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
              <div className="flex items-center gap-2 text-[var(--text-primary)] font-semibold text-sm">
                <Sliders size={16} className="text-[var(--clinical-cyan)]" /> Red-Flag Sensitivity
              </div>
              <Badge variant="teal" size="sm">
                {sensitivity}% Sensitivity
              </Badge>
            </div>

            <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
              Adjusts the clinical threshold for flagging potential emergency warning signs during symptom intake. Higher sensitivity escalates subtle symptoms earlier.
            </p>

            <div className="space-y-2 pt-2">
              <input
                type="range"
                min="50"
                max="99"
                value={sensitivity}
                onChange={(e) => setSensitivity(e.target.value)}
                className="w-full h-1.5 bg-[var(--bg-input)] rounded-lg appearance-none cursor-pointer accent-[var(--clinical-teal)]"
              />
              <div className="flex justify-between text-[11px] font-mono text-[var(--text-muted)]">
                <span>50% (Standard Triage)</span>
                <span>85% (Recommended)</span>
                <span>99% (Maximum Defensive)</span>
              </div>
            </div>
          </Card>
        </div>

        <div className="lg:col-span-4 space-y-4">
          <Card elevated bordered className="space-y-3 p-5 text-xs text-[var(--text-secondary)]">
            <div className="flex items-center gap-2 text-[var(--clinical-teal)] font-semibold text-xs">
              <Database size={16} /> Knowledge Base State
            </div>
            <div className="space-y-2 pt-1 font-mono text-[11px]">
              <div className="flex justify-between py-1 border-b border-[var(--border-subtle)]">
                <span className="text-[var(--text-muted)]">Indexed Guidelines:</span>
                <span className="text-[var(--text-primary)] font-medium">1,248 Verified</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[var(--border-subtle)]">
                <span className="text-[var(--text-muted)]">Vector Store:</span>
                <span className="text-[var(--text-primary)] font-medium">Qdrant Local Active</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[var(--border-subtle)]">
                <span className="text-[var(--text-muted)]">Session Persistence:</span>
                <span className="text-[var(--severity-routine)] font-medium">SQLite Checkpointed</span>
              </div>
            </div>
          </Card>

          <Card elevated bordered className="space-y-2 p-5 text-xs text-[var(--text-secondary)]">
            <div className="flex items-center gap-2 text-[var(--clinical-teal)] font-semibold text-xs">
              <ShieldCheck size={16} /> Compliance Guarantee
            </div>
            <p className="leading-relaxed">
              Protocol changes are audited against published clinical differential algorithms and verified medical sources.
            </p>
          </Card>
        </div>
      </div>
    </PageContainer>
  );
};

export default SettingsPage;
