import { useState } from 'react';
import type React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { MobileNav } from './MobileNav';
import { CommandPalette } from '../ui/CommandPalette';
import type { NavigationPage } from '../../types';

export interface AppLayoutProps {
  currentPage: NavigationPage;
  onNavigate: (page: NavigationPage) => void;
  onSelectCustomer?: (customerId: string) => void;
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  currentPage,
  onNavigate,
  onSelectCustomer,
  children,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#09090D] text-[#F4F4F7]">
      {/* Desktop Sidebar */}
      <div className="hidden lg:block shrink-0">
        <Sidebar
          currentPage={currentPage}
          onNavigate={onNavigate}
          isCollapsed={isCollapsed}
          onToggleCollapse={() => setIsCollapsed(!isCollapsed)}
        />
      </div>

      {/* Mobile Slide-Over Navigation */}
      <MobileNav
        isOpen={isMobileNavOpen}
        onClose={() => setIsMobileNavOpen(false)}
        currentPage={currentPage}
        onNavigate={onNavigate}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden bg-[#09090D]">
        {/* Global Header */}
        <Header
          currentPage={currentPage}
          onOpenMobileNav={() => setIsMobileNavOpen(true)}
          onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
          onNavigate={onNavigate}
        />

        {/* Content Workspace with Page Transition */}
        <main className="flex-1 overflow-y-auto bg-[#09090D] relative">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentPage}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.18, ease: 'easeOut' }}
              className="h-full w-full"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* Global Quick Action / Command Palette (⌘K) */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onNavigate={onNavigate}
        onSelectCustomer={onSelectCustomer}
      />
    </div>
  );
};
