import { useState } from 'react';
import type React from 'react';
import {
  Send,
  Paperclip,
  Sparkles,
  Brain,
  ShieldAlert,
  ArrowRight,
  LoaderCircle,
  AlertCircle,
} from 'lucide-react';
import type { Conversation } from '../../types';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { MarkdownRenderer } from '../ui/MarkdownRenderer';

export interface ConversationThreadProps {
  conversation: Conversation;
  onSendMessage: (text: string) => Promise<boolean>;
  onRunSarahPhase: (phase: 1 | 2 | 3) => void;
  runningPhase: 1 | 2 | 3 | null;
  completedPhases: (1 | 2 | 3)[];
  isSendingManualMessage: boolean;
  errorMessage: string | null;
  isLiveDemoCustomer: boolean;
}

export const ConversationThread: React.FC<ConversationThreadProps> = ({
  conversation,
  onSendMessage,
  onRunSarahPhase,
  runningPhase,
  completedPhases,
  isSendingManualMessage,
  errorMessage,
  isLiveDemoCustomer,
}) => {
  const [inputText, setInputText] = useState('');
  const isBusy = runningPhase !== null || isSendingManualMessage;

  const handleSend = async () => {
    const message = inputText;
    if (!message.trim() || isBusy || !isLiveDemoCustomer) return;
    const sent = await onSendMessage(message);
    if (sent) setInputText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isSarahConversation = isLiveDemoCustomer;

  return (
    <div className="h-full flex flex-col bg-[#09090D] overflow-hidden">
      {/* Thread Header */}
      <div className="h-16 px-4 sm:px-6 border-b border-white/[0.07] bg-[#0D0D13] flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <img
            src={conversation.customerAvatar}
            alt={conversation.customerName}
            className="w-9 h-9 rounded-full object-cover border border-white/[0.1]"
          />
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-[#F4F4F7]">
                {conversation.customerName}
              </h3>
              <Badge variant="outline" size="sm">
                Session: {conversation.sessionId ? `${conversation.sessionId.slice(0, 16)}...` : 'Not started'}
              </Badge>
            </div>
            <p className="text-xs text-[#92929F] truncate max-w-sm sm:max-w-md">
              {conversation.title}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge
            variant={
              conversation.status === 'open'
                ? 'emerald'
                : conversation.status === 'pending'
                ? 'amber'
                : 'neutral'
            }
            size="sm"
            dot
          >
            {conversation.status.toUpperCase()}
          </Badge>
        </div>
      </div>

      {/* Demo Scenario Quick-Sim Banner (Sarah Mitchell scenario) */}
      {isSarahConversation && (
        <div className="bg-[#12121A] border-b border-white/[0.08] px-4 py-2.5 sm:px-6 flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2 text-[#B6A9FF]">
            <Sparkles className="w-3.5 h-3.5 text-[#9B8CFF]" />
            <span className="font-semibold">Interactive Sarah Demo Scenario:</span>
            <span className="text-[#92929F] hidden sm:inline">
              Send the three ordered interactions to the live backend
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            {([1, 2, 3] as const).map((phase) => {
              const completed = completedPhases.includes(phase);
              const locked = phase === 2
                ? !completedPhases.includes(1)
                : phase === 3
                  ? !completedPhases.includes(2)
                  : false;
              const labels = { 1: 'Propose Step', 2: 'Report Failure', 3: 'Cross-Session Recall' };
              return (
                <button
                  key={phase}
                  type="button"
                  onClick={() => onRunSarahPhase(phase)}
                  disabled={isBusy || locked || completed}
                  className={`px-2 py-1 rounded border text-[11px] font-medium transition-colors flex items-center gap-1 ${
                    phase === 3
                      ? 'bg-[#9B8CFF]/20 text-[#B6A9FF] border-[#9B8CFF]/40'
                      : phase === 2
                        ? 'bg-[#191923] text-[#FB7185] border-[#F43F5E]/30'
                        : 'bg-[#191923] text-[#92929F] border-white/[0.08]'
                  } ${isBusy || locked || completed ? 'opacity-45 cursor-not-allowed' : 'hover:bg-white/[0.08] cursor-pointer'}`}
                  title={locked ? 'Complete the previous phase first.' : completed ? 'This phase is complete for this run.' : `Run phase ${phase}`}
                >
                  {runningPhase === phase && <LoaderCircle className="w-3 h-3 animate-spin" />}
                  <span>{phase}: {completed ? 'Completed' : labels[phase]}</span>
                  {phase === 3 && !completed && <ArrowRight className="w-3 h-3" />}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5">
        {conversation.messages.map((msg) => {
          const isCustomer = msg.sender === 'customer';
          return (
            <div
              key={msg.id}
              className={`flex flex-col ${isCustomer ? 'items-end' : 'items-start'}`}
            >
              {/* Sender Name & Timestamp Header */}
              <div className="flex items-center gap-2 mb-1 px-1 text-[11px] text-[#626270]">
                {isCustomer ? (
                  <>
                    <span>{conversation.customerName}</span>
                    <span>•</span>
                    <span className="font-mono">{msg.timestamp}</span>
                  </>
                ) : (
                  <>
                    <div className="flex items-center gap-1 text-[#9B8CFF] font-medium">
                      <Sparkles className="w-3 h-3" />
                      <span>{isSarahConversation ? 'RECALL Agent (Live Demo)' : 'RECALL Agent (Sample)'}</span>
                    </div>
                    <span>•</span>
                    <span className="font-mono">{msg.timestamp}</span>
                  </>
                )}
              </div>

              {/* Message Bubble */}
              <div
                className={`max-w-[88%] sm:max-w-[80%] rounded-2xl p-4 text-xs sm:text-sm leading-relaxed ${
                  isCustomer
                    ? 'bg-[#191923] text-[#F4F4F7] border border-white/[0.08] rounded-tr-sm shadow-sm'
                    : 'bg-[#12121A] text-[#F4F4F7] border border-white/[0.09] rounded-tl-sm shadow-md'
                }`}
              >
                {/* Render with MarkdownRenderer for rich lists, code, bold, headings */}
                <MarkdownRenderer content={msg.text} />

                {/* Agent Intelligence Metadata Footnote */}
                {!isCustomer && (
                  <div className="mt-3.5 pt-3 border-t border-white/[0.07] space-y-2 text-xs">
                    {/* Memory Retrieved Pill */}
                    {msg.memoryRetrieved && (
                      <div className="flex items-center gap-1.5 text-[11px] text-[#B6A9FF]">
                        <Brain className="w-3.5 h-3.5 text-[#9B8CFF] shrink-0" />
                        <span className="font-medium">Persistent memory retrieved by backend:</span>
                      </div>
                    )}

                    {/* Memories used list */}
                    {msg.memoriesUsed && msg.memoriesUsed.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {msg.memoriesUsed.map((mem, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#9B8CFF]/10 text-[#B6A9FF] border border-[#9B8CFF]/20"
                          >
                            {mem}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Escalation alert */}
                    {msg.escalationRequired && (
                      <div className="mt-1 flex items-center gap-1.5 text-[11px] text-[#FBBF24] bg-[#F59E0B]/10 border border-[#F59E0B]/20 px-2.5 py-1.5 rounded-lg">
                        <ShieldAlert className="w-3.5 h-3.5 shrink-0" />
                        <span>Escalation Work Pending: {msg.escalationReason}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
        {isBusy && (
          <div className="flex items-center gap-2 text-xs text-[#B6A9FF]" role="status" aria-live="polite">
            <LoaderCircle className="w-4 h-4 animate-spin" />
            <span>RECALL Agent is generating a response…</span>
          </div>
        )}
        {errorMessage && (
          <div className="flex items-start gap-2 rounded-lg border border-[#F43F5E]/25 bg-[#F43F5E]/10 p-3 text-xs text-[#FDA4AF]" role="alert">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage} You can try again.</span>
          </div>
        )}
      </div>

      {/* Composer Area */}
      <div className="p-3 sm:p-4 bg-[#0D0D13] border-t border-white/[0.07] shrink-0 space-y-2">
        <div className="flex items-center justify-between text-[11px] text-[#626270]">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#9B8CFF]" />
            {isSarahConversation ? 'Live Backend • Persistent Memory' : 'Select Sarah Mitchell for the live backend demo'}
          </span>
          <span className="font-mono hidden sm:inline">Enter to send • Shift+Enter for newline</span>
        </div>

        <div className="relative flex items-end gap-2 bg-[#12121A] border border-white/[0.08] focus-within:border-[#9B8CFF]/50 rounded-xl p-2 transition-all shadow-inner">
          <textarea
            rows={2}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!isSarahConversation || isBusy}
            placeholder={`Reply to ${conversation.customerName}...`}
            className="flex-1 bg-transparent text-sm text-[#F4F4F7] placeholder-[#626270] focus:outline-none resize-none px-2 py-1"
          />

          <div className="flex items-center gap-1 shrink-0 pb-1">
            <button
              type="button"
              className="p-1.5 text-[#626270] hover:text-[#92929F] rounded-lg hover:bg-white/[0.04] transition-colors cursor-pointer"
              title="Attach diagnostic file (Mock presentational)"
            >
              <Paperclip className="w-4 h-4" />
            </button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleSend}
              disabled={!inputText.trim() || !isSarahConversation || isBusy}
              icon={<Send className="w-3.5 h-3.5" />}
            >
              Send
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
