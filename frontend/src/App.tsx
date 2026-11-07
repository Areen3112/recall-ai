import { useState } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import type { NavigationPage } from './types';

// Pages
import { OverviewPage } from './pages/OverviewPage';
import { InboxPage } from './pages/InboxPage';
import { CustomersPage } from './pages/CustomersPage';
import { MemoryExplorerPage } from './pages/MemoryExplorerPage';
import { ActivityPage } from './pages/ActivityPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { KnowledgeBasePage } from './pages/KnowledgeBasePage';
import { IntegrationsPage } from './pages/IntegrationsPage';
import { SettingsPage } from './pages/SettingsPage';

export function App() {
  const [currentPage, setCurrentPage] = useState<NavigationPage>('overview');
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>('cust-sarah-mitchell-01');
  const [selectedConversationId, setSelectedConversationId] = useState<string>('conv-sarah-session-02');

  const handleNavigateToMemoryExplorer = (customerId?: string) => {
    if (customerId) setSelectedCustomerId(customerId);
    setCurrentPage('memory-explorer');
  };

  const handleOpenConversation = (convId: string) => {
    setSelectedConversationId(convId);
    setCurrentPage('inbox');
  };

  const handleSelectCustomer = (customerId: string) => {
    setSelectedCustomerId(customerId);
    setCurrentPage('customers');
  };

  return (
    <AppLayout
      currentPage={currentPage}
      onNavigate={setCurrentPage}
      onSelectCustomer={handleSelectCustomer}
    >
      {currentPage === 'overview' && (
        <OverviewPage
          onNavigate={setCurrentPage}
          onSelectConversation={handleOpenConversation}
        />
      )}

      {currentPage === 'inbox' && (
        <InboxPage
          initialConversationId={selectedConversationId}
          onNavigateToMemoryExplorer={handleNavigateToMemoryExplorer}
        />
      )}

      {currentPage === 'customers' && (
        <CustomersPage
          initialCustomerId={selectedCustomerId}
          onOpenConversation={handleOpenConversation}
          onNavigateToMemoryExplorer={handleNavigateToMemoryExplorer}
        />
      )}

      {currentPage === 'memory-explorer' && (
        <MemoryExplorerPage
          initialCustomerId={selectedCustomerId}
        />
      )}

      {currentPage === 'activity' && (
        <ActivityPage onOpenConversation={handleOpenConversation} />
      )}

      {currentPage === 'analytics' && <AnalyticsPage />}

      {currentPage === 'knowledge-base' && <KnowledgeBasePage />}

      {currentPage === 'integrations' && <IntegrationsPage />}

      {currentPage === 'settings' && <SettingsPage />}
    </AppLayout>
  );
}

export default App;
