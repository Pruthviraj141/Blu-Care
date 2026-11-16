// src/components/navigation/Sidebar.jsx
import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate, useParams, useLocation } from 'react-router-dom';
import { useUser } from '@clerk/clerk-react';
import {
  Plus,
  MessageSquare,
  Pencil,
  Trash2,
  Check,
  X,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Sparkles,
  Activity,
} from 'lucide-react';
import {
  getSessions,
  createSession,
  renameSession,
  deleteSession,
  groupSessionsByDate,
  setActiveSessionId,
} from '../../utils/chatStorage';
import { useToast } from '../../contexts/ToastContext';

/**
 * World-Class Sidebar Navigation
 * Refero & Linear standard with responsive desktop collapse & clean graphite tokens
 */
const Sidebar = ({ isCollapsed, setIsCollapsed, isMobileOpen, onCloseMobile }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { sessionId } = useParams();
  const { addToast } = useToast();
  const { user } = useUser();

  const [sessions, setSessions] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [editingTitle, setEditingTitle] = useState('');

  const loadSessions = () => {
    const list = getSessions();
    setSessions(list);
  };

  useEffect(() => {
    loadSessions();

    const handleStorageChange = () => loadSessions();
    window.addEventListener('blucare_sessions_updated', handleStorageChange);
    return () => window.removeEventListener('blucare_sessions_updated', handleStorageChange);
  }, [location.pathname]);

  const handleCreateNewChat = () => {
    const newSess = createSession('New Health Consultation');
    loadSessions();
    window.dispatchEvent(new Event('blucare_sessions_updated'));
    navigate(`/app/chat/${newSess.id}`);
    if (onCloseMobile) onCloseMobile();
    addToast('New conversation initialized', 'info');
  };

  const handleStartRename = (e, sess) => {
    e.stopPropagation();
    e.preventDefault();
    setEditingId(sess.id);
    setEditingTitle(sess.title);
  };

  const handleSaveRename = (e, id) => {
    e.stopPropagation();
    e.preventDefault();
    if (editingTitle.trim()) {
      renameSession(id, editingTitle.trim());
      loadSessions();
      window.dispatchEvent(new Event('blucare_sessions_updated'));
      addToast('Conversation renamed', 'success');
    }
    setEditingId(null);
  };

  const handleCancelRename = (e) => {
    e.stopPropagation();
    e.preventDefault();
    setEditingId(null);
  };

  const handleDelete = (e, id, title) => {
    e.stopPropagation();
    e.preventDefault();
    deleteSession(id);
    loadSessions();
    window.dispatchEvent(new Event('blucare_sessions_updated'));
    addToast(`Deleted "${title || 'Chat'}"`, 'info');

    if (sessionId === id) {
      navigate('/app/chat');
    }
  };

  const grouped = groupSessionsByDate(sessions);

  const renderSessionItem = (sess) => {
    const isActive = location.pathname === `/app/chat/${sess.id}` || location.pathname === `/chat/${sess.id}`;
    const isEditing = editingId === sess.id;

    if (isEditing) {
      return (
        <div key={sess.id} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-[6px] bg-[var(--bg-elevated)] border border-[var(--clinical-teal)]/40">
          <input
            type="text"
            autoFocus
            value={editingTitle}
            onChange={(e) => setEditingTitle(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSaveRename(e, sess.id);
              if (e.key === 'Escape') handleCancelRename(e);
            }}
            className="flex-1 bg-transparent text-xs text-[var(--text-primary)] outline-none min-w-0 font-sans"
          />
          <button
            type="button"
            onClick={(e) => handleSaveRename(e, sess.id)}
            className="p-1 text-[var(--clinical-teal)] hover:bg-[var(--clinical-teal)]/10 rounded cursor-pointer"
            title="Save"
          >
            <Check size={13} />
          </button>
          <button
            type="button"
            onClick={handleCancelRename}
            className="p-1 text-[var(--text-muted)] hover:bg-white/5 rounded cursor-pointer"
            title="Cancel"
          >
            <X size={13} />
          </button>
        </div>
      );
    }

    return (
      <NavLink
        key={sess.id}
        to={`/app/chat/${sess.id}`}
        onClick={() => {
          setActiveSessionId(sess.id);
          if (onCloseMobile) onCloseMobile();
        }}
        title={isCollapsed ? sess.title : undefined}
        className={`group relative flex items-center justify-between gap-2 px-2.5 py-2 rounded-[6px] text-xs font-medium transition-all no-underline ${
          isActive
            ? 'bg-[var(--bg-elevated)] text-[var(--text-primary)] border border-[var(--border-strong)]'
            : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]/60 border border-transparent'
        }`}
      >
        {isActive && (
          <span className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r-full bg-[var(--clinical-teal)]" />
        )}

        <div className="flex items-center gap-2 min-w-0 flex-1 pl-1">
          <MessageSquare
            size={14}
            className={`shrink-0 ${isActive ? 'text-[var(--clinical-teal)]' : 'text-[var(--text-muted)] group-hover:text-[var(--text-secondary)]'}`}
          />
          {!isCollapsed && <span className="truncate">{sess.title}</span>}
        </div>

        {!isCollapsed && (
          <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
            <button
              type="button"
              onClick={(e) => handleStartRename(e, sess)}
              className="p-1 rounded text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-white/5 transition-colors cursor-pointer"
              title="Rename"
            >
              <Pencil size={11} />
            </button>
            <button
              type="button"
              onClick={(e) => handleDelete(e, sess.id, sess.title)}
              className="p-1 rounded text-[var(--text-muted)] hover:text-[var(--severity-emergency)] hover:bg-[var(--severity-emergency)]/10 transition-colors cursor-pointer"
              title="Delete"
            >
              <Trash2 size={11} />
            </button>
          </div>
        )}
      </NavLink>
    );
  };

  const sidebarContent = (
    <aside
      role="navigation"
      aria-label="Main Navigation"
      aria-expanded={!isCollapsed}
      className={`h-full shrink-0 z-40 bg-[var(--bg-subtle)] border-r border-[var(--border-subtle)] transition-[width] duration-200 ease-in-out flex flex-col justify-between ${
        isCollapsed ? 'w-16' : 'w-60'
      }`}
    >
      {/* Top Section */}
      <div className="flex flex-col h-full overflow-hidden">
        {/* Brand Header */}
        <div className="h-14 flex items-center justify-between px-3 border-b border-[var(--border-subtle)] shrink-0">
          <NavLink
            to="/"
            className="flex items-center gap-2 no-underline shrink-0 group focus-visible:outline-2 focus-visible:outline-[var(--border-focus)] rounded-[6px]"
            title="BluCare+ Home"
          >
            <div className="w-7 h-7 rounded-[6px] bg-[var(--clinical-teal)]/15 border border-[var(--clinical-teal)]/30 text-[var(--clinical-teal)] flex items-center justify-center font-bold text-xs aspect-square shrink-0 group-hover:bg-[var(--clinical-teal)]/25 transition-colors">
              <Activity size={15} />
            </div>

            <div
              className={`transition-all duration-200 flex items-center ${
                isCollapsed
                  ? 'opacity-0 -translate-x-2 w-0 overflow-hidden pointer-events-none'
                  : 'opacity-100 translate-x-0 w-auto'
              }`}
            >
              <span className="text-[var(--text-primary)] font-semibold text-sm tracking-tight whitespace-nowrap">
                BluCare<span className="text-[var(--clinical-teal)]">+</span>
              </span>
            </div>
          </NavLink>

          <button
            type="button"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="hidden md:flex p-1.5 rounded-[5px] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors cursor-pointer shrink-0"
            title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
            aria-label={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {isCollapsed ? <ChevronRight size={15} /> : <ChevronLeft size={15} />}
          </button>
        </div>

        {/* New Consultation CTA Button */}
        <div className="p-2.5 shrink-0">
          <button
            type="button"
            onClick={handleCreateNewChat}
            className={`w-full flex items-center justify-center gap-2 h-9 rounded-[6px] bg-[var(--accent-primary)] text-[#101316] font-medium text-xs transition-all hover:bg-[var(--accent-hover)] active:bg-[#607d9b] cursor-pointer shadow-sm ${
              isCollapsed ? 'px-2' : 'px-3'
            }`}
            title="Start New Health Consultation"
          >
            <Plus size={15} className="shrink-0" />
            {!isCollapsed && <span className="font-sans">New Consultation</span>}
          </button>
        </div>

        {/* Chronological Chat History List */}
        <div className="flex-1 overflow-y-auto px-2 py-1 space-y-3 scrollbar-thin">
          {/* Today */}
          {grouped.today.length > 0 && (
            <div className="space-y-0.5">
              {!isCollapsed && (
                <p className="px-2 text-[10px] font-mono uppercase tracking-wider text-[var(--text-muted)] mb-1">
                  Today
                </p>
              )}
              {grouped.today.map(renderSessionItem)}
            </div>
          )}

          {/* Yesterday */}
          {grouped.yesterday.length > 0 && (
            <div className="space-y-0.5">
              {!isCollapsed && (
                <p className="px-2 text-[10px] font-mono uppercase tracking-wider text-[var(--text-muted)] mb-1">
                  Yesterday
                </p>
              )}
              {grouped.yesterday.map(renderSessionItem)}
            </div>
          )}

          {/* Previous 7 Days */}
          {grouped.last7Days.length > 0 && (
            <div className="space-y-0.5">
              {!isCollapsed && (
                <p className="px-2 text-[10px] font-mono uppercase tracking-wider text-[var(--text-muted)] mb-1">
                  Previous 7 Days
                </p>
              )}
              {grouped.last7Days.map(renderSessionItem)}
            </div>
          )}

          {/* Older */}
          {grouped.older.length > 0 && (
            <div className="space-y-0.5">
              {!isCollapsed && (
                <p className="px-2 text-[10px] font-mono uppercase tracking-wider text-[var(--text-muted)] mb-1">
                  Older
                </p>
              )}
              {grouped.older.map(renderSessionItem)}
            </div>
          )}

          {sessions.length === 0 && !isCollapsed && (
            <div className="py-6 text-center text-[var(--text-muted)] space-y-1.5">
              <Sparkles size={16} className="mx-auto text-[var(--text-muted)]/50" />
              <p className="text-xs">No previous consultations</p>
            </div>
          )}
        </div>
      </div>

      {/* Footer Profile & Status */}
      {!isCollapsed && (
        <div className="p-2.5 border-t border-[var(--border-subtle)] shrink-0">
          <div className="p-2 rounded-[6px] bg-[var(--bg-elevated)]/60 border border-[var(--border-subtle)] flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 min-w-0">
              {user?.imageUrl ? (
                <img
                  src={user.imageUrl}
                  alt={user?.fullName || 'User'}
                  className="w-6 h-6 rounded-full border border-[var(--border-subtle)] object-cover shrink-0"
                />
              ) : (
                <div className="w-6 h-6 rounded-full bg-[var(--clinical-teal)]/20 text-[var(--clinical-teal)] flex items-center justify-center font-semibold text-[11px] shrink-0">
                  {(user?.fullName || user?.firstName || 'P').charAt(0)}
                </div>
              )}
              <div className="min-w-0">
                <p className="font-medium text-[var(--text-primary)] text-xs truncate">
                  {user?.fullName || user?.firstName || 'Patient'}
                </p>
                <p className="text-[10px] font-mono text-[var(--text-muted)] truncate">AI Clinical Active</p>
              </div>
            </div>
            <ShieldCheck size={14} className="text-[var(--clinical-teal)] shrink-0" />
          </div>
        </div>
      )}
    </aside>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <div className="hidden md:flex h-full shrink-0">
        {sidebarContent}
      </div>

      {/* Mobile Off-Canvas Drawer */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden animate-fade-in flex">
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm"
            onClick={onCloseMobile}
            aria-hidden="true"
          />
          <div className="relative z-50 w-72 h-full bg-[var(--bg-subtle)] shadow-2xl">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
};

export default Sidebar;
