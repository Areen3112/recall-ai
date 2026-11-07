import { useRef, useState } from 'react';
import type React from 'react';
import { ArrowLeft } from 'lucide-react';
import { MOCK_CONVERSATIONS } from '../data/mock/conversations';
import { MOCK_CUSTOMERS } from '../data/mock/customers';
import { MOCK_MEMORIES } from '../data/mock/memories';
import { ConversationList } from '../components/inbox/ConversationList';
import { ConversationThread } from '../components/inbox/ConversationThread';
import { CustomerIntelligencePanel } from '../components/inbox/CustomerIntelligencePanel';
import { sendDemoChatMessage } from '../services/api/demoChatClient';
import type { Conversation, Message } from '../types';

const SARAH_LEARNING_CONVERSATION_ID = 'conv-sarah-session-01';
const SARAH_RECALL_CONVERSATION_ID = 'conv-sarah-session-02';
const SARAH_SCENARIO_MESSAGES = {
  1: 'My Bluetooth headphones disconnect about every 10 minutes. Restarting Bluetooth and the headphones did not help. Please suggest one different step: forgetting these headphones in Bluetooth settings and pairing them again.',
  2: 'I followed your suggestion to forget these headphones in Bluetooth settings and pair them again. It did not help; they still disconnect after about 10 minutes.',
  3: 'My Bluetooth headphones disconnected again. Based on my previous support history, what different troubleshooting step should I try?',
} as const;

type SarahPhase = 1 | 2 | 3;

interface SarahScenarioRun {
  runId: string;
  learningSessionId: string;
  recallSessionId: string;
}

function newScenarioRun(): SarahScenarioRun {
  if (typeof crypto === 'undefined' || typeof crypto.randomUUID !== 'function') {
    throw new Error('Secure random identifier generation is unavailable in this browser.');
  }
  const runId = crypto.randomUUID();
  return {
    runId,
    learningSessionId: `sarah-dashboard-${runId}-learning`,
    recallSessionId: `sarah-dashboard-${runId}-recall`,
  };
}

function newMessageId(): string {
  if (typeof crypto === 'undefined' || typeof crypto.randomUUID !== 'function') {
    throw new Error('Secure random identifier generation is unavailable in this browser.');
  }
  return crypto.randomUUID();
}

function cleanInitialSarahConversations(conversations: Conversation[]): Conversation[] {
  return conversations.map((conversation) =>
    (conversation.id === SARAH_LEARNING_CONVERSATION_ID || conversation.id === SARAH_RECALL_CONVERSATION_ID)
      ? {
          ...conversation,
          messages: [],
          relevantMemories: [],
          sessionId: '',
          preview: 'Ready for the live backend demo.',
          lastActivity: '—',
          sentiment: 'unknown',
          status: 'open',
          unread: false,
          priority: 'normal',
        }
      : conversation
  );
}

export interface InboxPageProps {
  initialConversationId?: string;
  onNavigateToMemoryExplorer?: (customerId: string) => void;
}

export const InboxPage: React.FC<InboxPageProps> = ({
  initialConversationId = SARAH_RECALL_CONVERSATION_ID,
  onNavigateToMemoryExplorer,
}) => {
  const [conversations, setConversations] = useState<Conversation[]>(() =>
    cleanInitialSarahConversations(MOCK_CONVERSATIONS)
  );
  const [selectedId, setSelectedId] = useState<string>(initialConversationId);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'open' | 'pending' | 'resolved'>('all');
  const [completedPhases, setCompletedPhases] = useState<SarahPhase[]>([]);
  const [runningPhase, setRunningPhase] = useState<SarahPhase | null>(null);
  const [isSendingManualMessage, setIsSendingManualMessage] = useState(false);
  const [demoError, setDemoError] = useState<string | null>(null);
  const [mobileActiveView, setMobileActiveView] = useState<'list' | 'thread' | 'intelligence'>('thread');
  const requestInFlight = useRef(false);
  const scenarioRunRef = useRef<SarahScenarioRun | null>(null);
  const completedPhasesRef = useRef<Set<SarahPhase>>(new Set());

  const selectedConversation = conversations.find((conversation) => conversation.id === selectedId) || conversations[0];
  const currentCustomer =
    MOCK_CUSTOMERS.find((customer) => customer.id === selectedConversation.customerId) || MOCK_CUSTOMERS[0];
  const isSarahCustomer =
    selectedConversation.id === SARAH_LEARNING_CONVERSATION_ID ||
    selectedConversation.id === SARAH_RECALL_CONVERSATION_ID;
  const customerMemories = isSarahCustomer
    ? []
    : MOCK_MEMORIES.filter((memory) => memory.customerId === currentCustomer.id);

  const ensureScenarioRun = (): SarahScenarioRun => {
    if (scenarioRunRef.current) return scenarioRunRef.current;
    const run = newScenarioRun();
    scenarioRunRef.current = run;
    setConversations((previous) => cleanInitialSarahConversations(previous));
    return run;
  };

  const sendLiveMessage = async (
    conversationId: string,
    sessionId: string,
    text: string,
    phase?: SarahPhase
  ): Promise<boolean> => {
    if (requestInFlight.current) return false;
    requestInFlight.current = true;
    setDemoError(null);
    if (phase) setRunningPhase(phase);
    else setIsSendingManualMessage(true);

    try {
      const result = await sendDemoChatMessage({ session_id: sessionId, message: text });
      if (!result.ok) {
        setDemoError(`${phase ? `Phase ${phase}` : 'Message'}: ${result.error.message}`);
        return false;
      }

      const reply = result.data;
      const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const customerMessage: Message = {
        id: newMessageId(),
        sender: 'customer',
        text,
        timestamp,
      };
      const agentMessage: Message = {
        id: newMessageId(),
        sender: 'agent',
        text: reply.response,
        timestamp,
        sentiment: reply.sentiment,
        memoryRetrieved: reply.memory_retrieved,
        memoriesUsed: reply.memories_used,
        escalationRequired: reply.escalation_required,
        escalationReason: reply.escalation_reason,
      };

      setConversations((previous) => previous.map((conversation) =>
        conversation.id === conversationId
          ? {
              ...conversation,
              sessionId: reply.session_id,
              preview: text,
              lastActivity: 'Just now',
              sentiment: reply.sentiment,
              status: reply.escalation_required ? 'pending' : 'open',
              unread: false,
              messages: [...conversation.messages, customerMessage, agentMessage],
            }
          : conversation
      ));

      if (phase) {
        const responseIsComplete =
          result.status === 200 &&
          result.workflowStatus === 'complete' &&
          result.memoryStatus === 'stored';
        if (responseIsComplete) {
          completedPhasesRef.current.add(phase);
          setCompletedPhases([...completedPhasesRef.current]);
        } else {
          setDemoError(
            `Phase ${phase}: the backend returned a saved but incomplete workflow. The phase is not marked complete.`
          );
        }
      }
      return true;
    } finally {
      requestInFlight.current = false;
      setRunningPhase(null);
      setIsSendingManualMessage(false);
    }
  };

  const handleSendMessage = async (text: string): Promise<boolean> => {
    if (!isSarahCustomer) {
      setDemoError('The live demo endpoint is available only for Sarah Mitchell.');
      return false;
    }
    try {
      const run = ensureScenarioRun();
      const useRecallSession =
        selectedConversation.id === SARAH_RECALL_CONVERSATION_ID && completedPhasesRef.current.has(3);
      const conversationId = useRecallSession
        ? SARAH_RECALL_CONVERSATION_ID
        : SARAH_LEARNING_CONVERSATION_ID;
      const sessionId = useRecallSession ? run.recallSessionId : run.learningSessionId;
      setSelectedId(conversationId);
      setMobileActiveView('thread');
      return await sendLiveMessage(conversationId, sessionId, text);
    } catch (error) {
      setDemoError(error instanceof Error ? error.message : 'Could not start the live demo.');
      return false;
    }
  };

  const handleRunSarahPhase = async (phase: SarahPhase): Promise<void> => {
    if (
      requestInFlight.current ||
      completedPhasesRef.current.has(phase) ||
      (phase === 2 && !completedPhasesRef.current.has(1)) ||
      (phase === 3 && (!completedPhasesRef.current.has(1) || !completedPhasesRef.current.has(2)))
    ) return;

    try {
      const run = ensureScenarioRun();
      const isRecallPhase = phase === 3;
      const conversationId = isRecallPhase ? SARAH_RECALL_CONVERSATION_ID : SARAH_LEARNING_CONVERSATION_ID;
      const sessionId = isRecallPhase ? run.recallSessionId : run.learningSessionId;
      setSelectedId(conversationId);
      setMobileActiveView('thread');
      await sendLiveMessage(conversationId, sessionId, SARAH_SCENARIO_MESSAGES[phase], phase);
    } catch (error) {
      setDemoError(error instanceof Error ? error.message : `Phase ${phase} could not start.`);
    }
  };

  return (
    <div className="h-full flex flex-col overflow-hidden bg-[#09090D]">
      <div className="lg:hidden flex items-center justify-between px-4 py-2 bg-[#0D0D13] border-b border-white/[0.07] text-xs shrink-0">
        <div className="flex items-center gap-1">
          {mobileActiveView !== 'list' && (
            <button
              onClick={() => setMobileActiveView('list')}
              className="p-1 rounded text-[#92929F] hover:text-[#F4F4F7] flex items-center gap-1 cursor-pointer mr-2"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>
          )}
          <span className="font-semibold text-[#F4F4F7] truncate max-w-[160px]">{selectedConversation.customerName}</span>
        </div>
        <div className="flex items-center gap-1 bg-[#12121A] p-0.5 rounded-lg border border-white/[0.05]">
          {(['list', 'thread', 'intelligence'] as const).map((view) => (
            <button
              key={view}
              onClick={() => setMobileActiveView(view)}
              className={`px-2 py-1 rounded text-[11px] font-medium transition-colors cursor-pointer ${
                mobileActiveView === view ? 'bg-[#191923] text-[#F4F4F7]' : 'text-[#92929F]'
              }`}
            >
              {view === 'thread' ? 'Chat' : view === 'intelligence' ? 'Memory' : 'List'}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className={`w-full lg:w-72 xl:w-80 shrink-0 h-full ${mobileActiveView === 'list' ? 'block' : 'hidden lg:block'}`}>
          <ConversationList
            conversations={conversations}
            selectedId={selectedConversation.id}
            onSelect={(id) => {
              setSelectedId(id);
              setMobileActiveView('thread');
              setDemoError(null);
            }}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            statusFilter={statusFilter}
            onStatusFilterChange={setStatusFilter}
          />
        </div>

        <div className={`flex-1 h-full min-w-0 ${mobileActiveView === 'thread' ? 'block' : 'hidden lg:block'}`}>
          <ConversationThread
            conversation={selectedConversation}
            onSendMessage={handleSendMessage}
            onRunSarahPhase={handleRunSarahPhase}
            runningPhase={runningPhase}
            completedPhases={completedPhases}
            isSendingManualMessage={isSendingManualMessage}
            errorMessage={demoError}
            isLiveDemoCustomer={isSarahCustomer}
          />
        </div>

        <div className={`w-full lg:w-72 xl:w-80 shrink-0 h-full ${mobileActiveView === 'intelligence' ? 'block' : 'hidden lg:block'}`}>
          <CustomerIntelligencePanel
            customer={currentCustomer}
            memories={customerMemories}
            onNavigateToMemoryExplorer={onNavigateToMemoryExplorer}
            isLiveDemoCustomer={isSarahCustomer}
          />
        </div>
      </div>
    </div>
  );
};
