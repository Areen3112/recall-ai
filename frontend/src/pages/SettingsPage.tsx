import { useState } from 'react';
import type React from 'react';
import {
  Settings,
  Shield,
  Bot,
  Palette,
  Sliders,
  Check,
  Lock
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

export const SettingsPage: React.FC = () => {
  const [activeSection, setActiveSection] = useState<'workspace' | 'agent' | 'security' | 'escalation' | 'widget'>('agent');

  // Agent settings state
  const [agentName, setAgentName] = useState('Apex Support Intelligence');
  const [model, setModel] = useState('llama-3.3-70b-versatile');
  const [temperature, setTemperature] = useState(0.2);
  const [autoMemoryRetention, setAutoMemoryRetention] = useState(true);
  const [avoidFailedActions, setAvoidFailedActions] = useState(true);
  const [maxFailedAttemptsBeforeEscalate, setMaxFailedAttemptsBeforeEscalate] = useState(2);

  // Identity security settings
  const [strictTokenVerification, setStrictTokenVerification] = useState(true);
  const [workspaceId] = useState('7f81b10a-3c44-4e92-91f8-88b14e259e81');

  // Save indicator
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  const navItems = [
    { id: 'agent', label: 'Support Agent AI', icon: Bot },
    { id: 'workspace', label: 'Workspace Identity', icon: Settings },
    { id: 'security', label: 'Security & Tokens', icon: Shield },
    { id: 'escalation', label: 'Escalation Rules', icon: Sliders },
    { id: 'widget', label: 'Widget Appearance', icon: Palette },
  ];

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="pb-4 border-b border-white/[0.08]">
        <div className="flex items-center gap-2">
          <h1 className="text-xl sm:text-2xl font-bold text-[#F4F4F7] tracking-tight">
            Platform Settings & Configuration
          </h1>
          <Badge variant="violet" size="sm">
            Workspace Admin
          </Badge>
        </div>
        <p className="text-xs sm:text-sm text-[#92929F] mt-1">
          Tune persistent memory recall thresholds, Groq inference prompts, and cryptographic identity rules.
        </p>
      </div>

      <div className="flex flex-col md:flex-row gap-6">
        {/* Navigation Sidebar */}
        <div className="w-full md:w-56 shrink-0 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeSection === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id as typeof activeSection)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                  isActive
                    ? 'bg-[#9B8CFF]/15 text-[#B6A9FF] border border-[#9B8CFF]/25 font-semibold'
                    : 'text-[#92929F] hover:text-[#F4F4F7] hover:bg-white/[0.04]'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-[#9B8CFF]' : 'text-[#626270]'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Content Form Area */}
        <div className="flex-1 bg-[#12121A] rounded-2xl border border-white/[0.08] p-5 sm:p-6 shadow-md">
          <form onSubmit={handleSave} className="space-y-6">
            {activeSection === 'agent' && (
              <div className="space-y-5">
                <div>
                  <h3 className="text-sm font-semibold text-[#F4F4F7]">AI Agent Configuration</h3>
                  <p className="text-xs text-[#92929F]">Control the model, memory weighting, and prompt conditioning.</p>
                </div>

                <div className="space-y-4 text-xs">
                  <div>
                    <label className="block text-[#92929F] font-medium mb-1.5">Agent Display Name</label>
                    <input
                      type="text"
                      value={agentName}
                      onChange={(e) => setAgentName(e.target.value)}
                      className="w-full bg-[#191923] text-sm text-[#F4F4F7] border border-white/[0.08] rounded-lg p-2.5 focus:outline-none focus:border-[#9B8CFF]/50"
                    />
                  </div>

                  <div>
                    <label className="block text-[#92929F] font-medium mb-1.5">Inference Model (Groq LPU)</label>
                    <select
                      value={model}
                      onChange={(e) => setModel(e.target.value)}
                      className="w-full bg-[#191923] text-sm text-[#F4F4F7] border border-white/[0.08] rounded-lg p-2.5 focus:outline-none focus:border-[#9B8CFF]/50"
                    >
                      <option value="llama-3.3-70b-versatile">Llama 3.3 70B Versatile (Recommended)</option>
                      <option value="llama-3.1-8b-instant">Llama 3.1 8B Instant (Ultra-low latency)</option>
                      <option value="mixtral-8x7b-32768">Mixtral 8x7B (High context window)</option>
                    </select>
                  </div>

                  <div className="pt-2">
                    <div className="flex items-center justify-between mb-1">
                      <label className="text-[#92929F] font-medium">Sampling Temperature</label>
                      <span className="font-mono text-[#F4F4F7]">{temperature}</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={temperature}
                      onChange={(e) => setTemperature(parseFloat(e.target.value))}
                      className="w-full accent-[#9B8CFF] cursor-pointer"
                    />
                    <span className="text-[10px] text-[#626270]">
                      Lower values produce deterministic, factual troubleshooting answers.
                    </span>
                  </div>

                  <div className="pt-3 border-t border-white/[0.06] space-y-3">
                    <label className="flex items-start gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={avoidFailedActions}
                        onChange={(e) => setAvoidFailedActions(e.target.checked)}
                        className="mt-1 accent-[#9B8CFF] rounded"
                      />
                      <div>
                        <span className="text-[#F4F4F7] font-medium block">
                          Strict Failed-Action Avoidance
                        </span>
                        <span className="text-[#92929F] text-[11px]">
                          Inject negative constraints into prompts to forbid suggesting previously failed actions (e.g., Sarah Mitchell forget-and-pair).
                        </span>
                      </div>
                    </label>

                    <label className="flex items-start gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={autoMemoryRetention}
                        onChange={(e) => setAutoMemoryRetention(e.target.checked)}
                        className="mt-1 accent-[#9B8CFF] rounded"
                      />
                      <div>
                        <span className="text-[#F4F4F7] font-medium block">
                          Automatic Session Reflection & Retention
                        </span>
                        <span className="text-[#92929F] text-[11px]">
                          Asynchronously analyze conversations to extract new customer facts and preferences to store in Hindsight Cloud.
                        </span>
                      </div>
                    </label>
                  </div>
                </div>
              </div>
            )}

            {activeSection === 'workspace' && (
              <div className="space-y-4 text-xs">
                <div>
                  <h3 className="text-sm font-semibold text-[#F4F4F7]">Workspace Identity</h3>
                  <p className="text-[#92929F]">Multi-tenant boundaries and public UUIDs.</p>
                </div>

                <div>
                  <label className="block text-[#92929F] font-medium mb-1">Workspace ID (Public UUID)</label>
                  <input
                    type="text"
                    disabled
                    value={workspaceId}
                    className="w-full bg-[#0D0D13] text-[#92929F] font-mono border border-white/[0.06] rounded-lg p-2.5 cursor-not-allowed"
                  />
                  <span className="text-[10px] text-[#626270] mt-1 block">
                    Passed in the <code className="text-[#9B8CFF]">X-Workspace-ID</code> header with every request.
                  </span>
                </div>

                <div>
                  <label className="block text-[#92929F] font-medium mb-1">Company / Organization Name</label>
                  <input
                    type="text"
                    defaultValue="Recall Audio Labs, Inc."
                    className="w-full bg-[#191923] text-sm text-[#F4F4F7] border border-white/[0.08] rounded-lg p-2.5"
                  />
                </div>
              </div>
            )}

            {activeSection === 'security' && (
              <div className="space-y-4 text-xs">
                <div>
                  <h3 className="text-sm font-semibold text-[#F4F4F7]">Identity Token & Cryptographic Verification</h3>
                  <p className="text-[#92929F]">Configured HS256 JWT signature verification.</p>
                </div>

                <div className="p-3.5 rounded-xl bg-[#0D0D13] border border-white/[0.06] flex items-start gap-3">
                  <Lock className="w-4 h-4 text-[#10B981] shrink-0 mt-0.5" />
                  <div>
                    <span className="text-[#F4F4F7] font-semibold block">Browser Identification Rejected as Proof</span>
                    <p className="text-[#92929F] text-[11px] mt-0.5">
                      Client-provided IDs are never trusted without a cryptographically signed identity token matching workspace, subject claim, and timestamp lifetime.
                    </p>
                  </div>
                </div>

                <label className="flex items-start gap-3 cursor-pointer pt-2">
                  <input
                    type="checkbox"
                    checked={strictTokenVerification}
                    onChange={(e) => setStrictTokenVerification(e.target.checked)}
                    className="mt-1 accent-[#9B8CFF] rounded"
                  />
                  <div>
                    <span className="text-[#F4F4F7] font-medium block">
                      Enforce Strict Token Binding
                    </span>
                    <span className="text-[#92929F] text-[11px]">
                      Reject chat attempts if token expiration exceeds 24 hours or issuer claim mismatches configured trust root.
                    </span>
                  </div>
                </label>
              </div>
            )}

            {activeSection === 'escalation' && (
              <div className="space-y-4 text-xs">
                <div>
                  <h3 className="text-sm font-semibold text-[#F4F4F7]">Support Escalation Rules</h3>
                  <p className="text-[#92929F]">Configure when tickets transfer from automated AI to human engineering tier.</p>
                </div>

                <div>
                  <label className="block text-[#92929F] font-medium mb-1">
                    Failed Troubleshooting Steps Threshold
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="5"
                    value={maxFailedAttemptsBeforeEscalate}
                    onChange={(e) => setMaxFailedAttemptsBeforeEscalate(parseInt(e.target.value) || 2)}
                    className="w-32 bg-[#191923] text-sm text-[#F4F4F7] border border-white/[0.08] rounded-lg p-2.5"
                  />
                  <span className="text-[10px] text-[#626270] mt-1 block">
                    After {maxFailedAttemptsBeforeEscalate} failed attempts, agent raises ticket status to <code>escalation-pending</code>.
                  </span>
                </div>
              </div>
            )}

            {activeSection === 'widget' && (
              <div className="space-y-4 text-xs">
                <div>
                  <h3 className="text-sm font-semibold text-[#F4F4F7]">Web Support Widget Appearance</h3>
                  <p className="text-[#92929F]">Configure colors and initial welcoming message.</p>
                </div>

                <div>
                  <label className="block text-[#92929F] font-medium mb-1">Initial Greeting Message</label>
                  <input
                    type="text"
                    defaultValue="Hi there! I'm Recall AI. I remember your previous setup and tickets so you don't have to repeat yourself."
                    className="w-full bg-[#191923] text-sm text-[#F4F4F7] border border-white/[0.08] rounded-lg p-2.5"
                  />
                </div>
              </div>
            )}

            {/* Bottom Form Actions */}
            <div className="pt-4 border-t border-white/[0.06] flex items-center justify-between">
              <div>
                {saveSuccess && (
                  <span className="text-xs text-[#34D399] flex items-center gap-1.5 font-medium">
                    <Check className="w-3.5 h-3.5" /> Settings updated successfully
                  </span>
                )}
              </div>
              <Button type="submit" variant="primary">
                Save Changes
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
