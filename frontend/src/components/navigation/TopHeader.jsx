// src/components/navigation/TopHeader.jsx
import React, { useState, useEffect, useRef } from 'react';
import {
  Sun,
  Moon,
  Plus,
  Activity,
  Menu,
  ShieldAlert,
  User,
  Settings,
  HelpCircle,
  ChevronDown,
  LogOut,
  PhoneCall,
  ExternalLink,
} from 'lucide-react';
import { useNavigate, useParams, useLocation, NavLink } from 'react-router-dom';
import { useUser, useClerk } from '@clerk/clerk-react';
import { getSessionById, createSession } from '../../utils/chatStorage';
import { useToast } from '../../contexts/ToastContext';
import Button from '../common/Button';
import IconButton from '../common/IconButton';

const routeLabels = {
  '/app/chat': 'Clinical Intake & Triage',
  '/app/hospitals': 'Verified Facilities & Emergency SOS',
  '/app/profile': 'Patient Profile & Medical History',
  '/app/settings': 'Care Protocol & AI Sensitivity',
  '/app/help': 'Help & Safety Documentation',
};

const TopHeader = ({ isCollapsed, setIsCollapsed, onOpenMobileSidebar }) => {
  const [theme, setTheme] = useState(localStorage.getItem('blucare_theme') || 'dark');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const dropdownRef = useRef(null);

  const navigate = useNavigate();
  const location = useLocation();
  const { sessionId } = useParams();
  const { addToast } = useToast();
  const { user } = useUser();
  const { signOut } = useClerk();

  const currentSession = sessionId ? getSessionById(sessionId) : null;
  const activeLabel = routeLabels[location.pathname] || (currentSession ? currentSession.title : 'Clinical Intake & Triage');

  const displayName = user?.fullName || user?.firstName || 'Patient';
  const displayEmail = user?.primaryEmailAddress?.emailAddress || 'patient@ragblucare.ai';
  const avatarUrl = user?.imageUrl;

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('blucare_theme', theme);
  }, [theme]);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const handleNewChat = () => {
    const newSess = createSession('New Health Consultation');
    window.dispatchEvent(new Event('blucare_sessions_updated'));
    navigate(`/app/chat/${newSess.id}`);
    addToast('New consultation initialized', 'info');
  };

  const handleSignOut = async () => {
    setIsMenuOpen(false);
    addToast('Signing out of BluCare+...', 'info');
    await signOut(() => navigate('/'));
  };

  return (
    <header className="w-full h-14 shrink-0 bg-[var(--bg-app)]/90 backdrop-blur-md border-b border-[var(--border-subtle)] flex items-center justify-between px-3 sm:px-6 relative z-30">
      {/* Left: Mobile Sidebar Toggle & Location Title */}
      <div className="flex items-center gap-2.5 min-w-0">
        {/* Mobile menu button */}
        <button
          type="button"
          onClick={onOpenMobileSidebar}
          className="md:hidden p-1.5 rounded-[5px] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors cursor-pointer"
          title="Open Consultations History"
          aria-label="Open Consultations History"
        >
          <Menu size={18} />
        </button>

        {/* Current Context / Breadcrumb */}
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-2 h-2 rounded-full bg-[var(--clinical-teal)] shrink-0 hidden sm:inline-block" />
          <h1 className="text-xs sm:text-sm font-medium text-[var(--text-primary)] truncate tracking-tight">
            {activeLabel}
          </h1>
        </div>
      </div>

      {/* Right Cluster: Emergency 108, New Consultation, Theme Toggle, Profile Menu */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Emergency SOS Shortcut */}
        <a
          href="tel:108"
          className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-[5px] bg-[var(--severity-emergency)]/15 border border-[var(--severity-emergency)]/30 text-[var(--severity-emergency)] text-[11px] font-mono font-semibold hover:bg-[var(--severity-emergency)]/25 transition-colors no-underline"
          title="Direct Emergency Ambulance Dial (108)"
        >
          <PhoneCall size={12} className="animate-pulse" />
          <span>SOS 108</span>
        </a>

        {/* Quick New Chat Button (Desktop) */}
        <Button
          variant="secondary"
          size="sm"
          onClick={handleNewChat}
          icon={Plus}
          className="hidden lg:inline-flex text-xs h-8"
        >
          New Chat
        </Button>

        {/* Theme Toggle */}
        <IconButton
          icon={theme === 'light' ? Moon : Sun}
          onClick={toggleTheme}
          variant="ghost"
          size="sm"
          title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
        />

        {/* User Profile Popover */}
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="flex items-center gap-2 p-1 rounded-[6px] hover:bg-[var(--bg-elevated)] transition-colors cursor-pointer select-none"
            aria-expanded={isMenuOpen}
          >
            {avatarUrl ? (
              <img
                src={avatarUrl}
                alt={displayName}
                className="w-7 h-7 rounded-full border border-[var(--border-subtle)] object-cover shrink-0"
              />
            ) : (
              <div className="w-7 h-7 rounded-full bg-[var(--clinical-teal)]/20 text-[var(--clinical-teal)] flex items-center justify-center font-semibold text-xs shrink-0">
                {displayName.charAt(0)}
              </div>
            )}
            <ChevronDown
              size={14}
              className={`text-[var(--text-muted)] transition-transform duration-200 hidden sm:block ${
                isMenuOpen ? 'rotate-180' : ''
              }`}
            />
          </button>

          {/* Dropdown Menu */}
          {isMenuOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-[8px] bg-[var(--bg-surface)] border border-[var(--border-strong)] shadow-xl p-1.5 text-xs text-[var(--text-primary)] z-50 animate-fade-in">
              <div className="px-2.5 py-2 border-b border-[var(--border-subtle)] mb-1">
                <p className="font-medium text-[var(--text-primary)] truncate">{displayName}</p>
                <p className="text-[11px] text-[var(--text-muted)] font-mono truncate">{displayEmail}</p>
              </div>

              <NavLink
                to="/app/profile"
                onClick={() => setIsMenuOpen(false)}
                className="flex items-center gap-2 px-2.5 py-1.5 rounded-[5px] hover:bg-[var(--bg-elevated)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors no-underline"
              >
                <User size={14} />
                <span>Patient Profile</span>
              </NavLink>

              <NavLink
                to="/app/settings"
                onClick={() => setIsMenuOpen(false)}
                className="flex items-center gap-2 px-2.5 py-1.5 rounded-[5px] hover:bg-[var(--bg-elevated)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors no-underline"
              >
                <Settings size={14} />
                <span>Care Settings</span>
              </NavLink>

              <NavLink
                to="/app/help"
                onClick={() => setIsMenuOpen(false)}
                className="flex items-center gap-2 px-2.5 py-1.5 rounded-[5px] hover:bg-[var(--bg-elevated)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors no-underline"
              >
                <HelpCircle size={14} />
                <span>Help & Protocols</span>
              </NavLink>

              <div className="pt-1 mt-1 border-t border-[var(--border-subtle)]">
                <button
                  type="button"
                  onClick={handleSignOut}
                  className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-[5px] hover:bg-[var(--severity-emergency)]/15 text-[var(--severity-emergency)] transition-colors text-left cursor-pointer"
                >
                  <LogOut size={14} />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default TopHeader;
