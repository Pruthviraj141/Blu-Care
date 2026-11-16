// src/components/navigation/MobileNavigation.jsx
import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  MessageSquare,
  Building2,
  User,
  Settings,
  Plus,
  PhoneCall,
  Activity,
} from 'lucide-react';
import { createSession } from '../../utils/chatStorage';
import { useToast } from '../../contexts/ToastContext';

/**
 * World-Class Mobile Bottom Navigation Bar
 * Ergonomic thumb-reach for mobile viewports
 */
const MobileNavigation = () => {
  const navigate = useNavigate();
  const { addToast } = useToast();

  const handleQuickNewChat = () => {
    const newSess = createSession('New Health Consultation');
    window.dispatchEvent(new Event('blucare_sessions_updated'));
    navigate(`/app/chat/${newSess.id}`);
    addToast('New consultation initialized', 'info');
  };

  const navItems = [
    {
      to: '/app/chat',
      label: 'Consultation',
      icon: MessageSquare,
    },
    {
      to: '/app/hospitals',
      label: 'Facilities',
      icon: Building2,
    },
    {
      to: '/app/profile',
      label: 'Profile',
      icon: User,
    },
    {
      to: '/app/settings',
      label: 'Settings',
      icon: Settings,
    },
  ];

  return (
    <nav
      aria-label="Mobile Bottom Navigation"
      className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-[var(--bg-surface)]/95 backdrop-blur-md border-t border-[var(--border-subtle)] px-2 py-1 safe-area-pb"
    >
      <div className="flex items-center justify-around h-14 max-w-lg mx-auto">
        {navItems.slice(0, 2).map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center gap-1 flex-1 py-1 px-2 rounded-[6px] no-underline transition-colors ${
                  isActive
                    ? 'text-[var(--clinical-teal)] font-medium'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                }`
              }
            >
              <Icon size={18} />
              <span className="text-[10px] tracking-tight">{item.label}</span>
            </NavLink>
          );
        })}

        {/* Center Quick New Consultation Button */}
        <div className="flex items-center justify-center px-1">
          <button
            type="button"
            onClick={handleQuickNewChat}
            className="w-10 h-10 rounded-[8px] bg-[var(--accent-primary)] text-[#101316] flex items-center justify-center shadow-sm active:scale-95 transition-transform cursor-pointer"
            title="Start New Assessment"
            aria-label="Start New Assessment"
          >
            <Plus size={20} strokeWidth={2.5} />
          </button>
        </div>

        {navItems.slice(2).map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center gap-1 flex-1 py-1 px-2 rounded-[6px] no-underline transition-colors ${
                  isActive
                    ? 'text-[var(--clinical-teal)] font-medium'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                }`
              }
            >
              <Icon size={18} />
              <span className="text-[10px] tracking-tight">{item.label}</span>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
};

export default MobileNavigation;

