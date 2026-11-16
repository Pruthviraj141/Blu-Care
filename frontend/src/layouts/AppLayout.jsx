// src/layouts/AppLayout.jsx
import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/navigation/Sidebar';
import TopHeader from '../components/navigation/TopHeader';
import MobileNavigation from '../components/navigation/MobileNavigation';

const AppLayout = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  return (
    <div className="workspace-root flex h-screen w-screen bg-[var(--bg-app)] text-[var(--text-primary)] font-sans overflow-hidden relative antialiased selection:bg-[var(--accent-primary)]/20 selection:text-[var(--accent-primary)]">
      {/* Sidebar Navigation Shell (Desktop + Mobile Drawer) */}
      <Sidebar
        isCollapsed={isCollapsed}
        setIsCollapsed={setIsCollapsed}
        isMobileOpen={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
      />

      {/* Main Workspace Column */}
      <div className="flex-1 flex flex-col h-full min-w-0 overflow-hidden relative z-10">
        {/* Top Navigation Header */}
        <TopHeader
          isCollapsed={isCollapsed}
          setIsCollapsed={setIsCollapsed}
          onOpenMobileSidebar={() => setIsMobileSidebarOpen(true)}
        />

        {/* Scrollable Main Workspace Content Canvas */}
        <main className="flex-1 overflow-y-auto px-3 sm:px-6 md:px-8 pt-4 pb-20 md:pb-8">
          <div className="w-full max-w-6xl mx-auto">
            <Outlet />
          </div>
        </main>

        {/* Ergonomic Mobile Bottom Navigation Bar */}
        <MobileNavigation />
      </div>
    </div>
  );
};

export default AppLayout;
