"use client";

import { useState, useRef, useEffect, type FormEvent } from "react";
import { streamChat } from "./api";

const SUGGESTIONS = [
  {
    title: "Collect Payment",
    desc: "₹5,000 from Mohit for March",
    text: "Collect ₹5,000 from Mohit for March subscription",
  },
  {
    title: "Show Contacts",
    desc: "List everyone in CRM",
    text: "Show me all my contacts",
  },
  {
    title: "Send Reminder",
    desc: "To pending client",
    text: "Send a reminder to ankit.sheth1@gmail.com",
  },
  {
    title: "View Pending",
    desc: "Check unpaid invoices",
    text: "What payments are pending?",
  },
];

function generateId() {
  return Math.random().toString(36).slice(2, 10);
}

type Interaction = {
  id: string;
  userPrompt: string;
  agentLogs: string[];
  agentResult: string;
  isStreaming: boolean;
};

export default function AgentPage() {
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeTab, setActiveTab] = useState<number | null>(null);

  // Chat History mapped as Agent Interactions
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [threadId, setThreadId] = useState<string>("");

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Generate the initial threadId on the client to avoid SSR hydration mismatches
    setThreadId(`thread-${generateId()}`);
  }, []);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
      if (input === "") {
        textareaRef.current.style.height = "60px";
      }
    }
  }, [input]);

  // Auto-scroll
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [interactions]);

  const handleSuggestionClick = (index: number) => {
    setActiveTab(index);
    setInput(SUGGESTIONS[index].text);
    if (textareaRef.current) textareaRef.current.focus();
  };

  const runAgent = async () => {
    if (!input.trim() || isStreaming) return;

    const query = input.trim();
    const interactionId = generateId();
    
    setInput("");
    setIsStreaming(true);
    setActiveTab(null);

    setInteractions((prev) => [
      ...prev,
      {
        id: interactionId,
        userPrompt: query,
        agentLogs: [],
        agentResult: "",
        isStreaming: true,
      },
    ]);

    try {
      for await (const event of streamChat(query, threadId)) {
        setInteractions((prev) =>
          prev.map((interaction) => {
            if (interaction.id !== interactionId) return interaction;

            if (event.type === "tool_start" && event.tool) {
              const formattedTool = event.tool
                .replace(/_tool$/, "")
                .replace(/_/g, " ");
              return {
                ...interaction,
                agentLogs: [...interaction.agentLogs, `Running: ${formattedTool}...`],
              };
            } else if (event.type === "content" && event.data) {
              return {
                ...interaction,
                agentResult: interaction.agentResult + event.data,
              };
            } else if (event.type === "error") {
              return {
                ...interaction,
                agentResult: interaction.agentResult + `\n\nError: ${event.message}`,
              };
            }
            return interaction;
          })
        );
      }
    } catch (err) {
      setInteractions((prev) =>
        prev.map((interaction) =>
          interaction.id === interactionId
            ? { ...interaction, agentResult: interaction.agentResult + "\nConnection error." }
            : interaction
        )
      );
    } finally {
      setIsStreaming(false);
      setInteractions((prev) =>
        prev.map((interaction) =>
          interaction.id === interactionId
            ? {
                ...interaction,
                isStreaming: false,
                agentLogs: [...interaction.agentLogs, "Task completed."],
              }
            : interaction
        )
      );
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      runAgent();
    }
  };

  return (
    <div className="min-h-dvh flex flex-col items-center pt-12 px-6 pb-20">
      {/* Header Area */}
      <div className="w-full max-w-5xl mb-12 flex flex-col md:flex-row items-start md:items-center justify-between gap-8 animate-fade-in">
        <div className="max-w-xl">
          <h1 className="text-4xl md:text-5xl font-medium tracking-tight mb-4 text-[var(--text-primary)]">
            The intelligent payment <br /> ops agent
          </h1>
          <p className="text-[var(--text-secondary)] text-lg leading-relaxed">
            Powering small businesses with AI. Type what you need done — FlowPay
            handles CRM lookups, Razorpay links, and email follow-ups automatically.
          </p>
        </div>
        <div className="flex gap-4">
          <button className="px-6 py-2.5 rounded-full font-medium text-sm transition-colors bg-[var(--button-dark)] text-white hover:opacity-90 min-w-[160px]">
            {threadId ? `Current Thread: ${threadId.slice(0, 10)}` : "Initializing..."}
          </button>
        </div>
      </div>

      {/* Main Control Panel */}
      <div
        className="w-full max-w-5xl rounded-3xl p-2 sm:p-4 mb-4 shadow-sm animate-fade-in"
        style={{ background: "var(--bg-container)", animationDelay: "0.1s" }}
      >
        <div className="flex flex-col md:flex-row gap-0 bg-[var(--bg-card)] rounded-2xl overflow-hidden border border-[var(--border)] h-[600px] md:h-[650px]">
          
          {/* Left Sidebar: Templates */}
          <div className="w-full md:w-72 border-b md:border-b-0 md:border-r border-[var(--border)] p-4 flex flex-col gap-2 overflow-y-auto shrink-0 bg-[var(--bg-page)]">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-2 px-3 pt-2">
              Quick Tasks
            </h2>
            {SUGGESTIONS.map((s, i) => (
              <button
                key={i}
                onClick={() => handleSuggestionClick(i)}
                className={`text-left px-4 py-3 rounded-xl transition-colors cursor-pointer flex flex-col gap-1 ${
                  activeTab === i
                    ? "bg-[var(--bg-surface-active)]"
                    : "hover:bg-[var(--bg-surface-hover)]"
                }`}
              >
                <div className="flex items-center justify-between pointer-events-none">
                  <span className="text-sm font-medium text-[var(--text-primary)]">
                    {s.title}
                  </span>
                  {activeTab === i && (
                    <span className="w-2 h-2 rounded-full bg-[var(--success)]" />
                  )}
                </div>
                <span className="text-xs text-[var(--text-muted)] pointer-events-none">
                  {s.desc}
                </span>
              </button>
            ))}
          </div>

          {/* Right Area: Input & Output */}
          <div className="flex-1 flex flex-col relative bg-white">
            
            {/* Scrollable Chat Feed */}
            <div className="flex-1 overflow-y-auto p-6 sm:p-8 flex flex-col gap-6">
              {interactions.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center opacity-60">
                  <div className="w-16 h-16 bg-[var(--border)] rounded-2xl mb-4 flex items-center justify-center">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-[var(--text-primary)]">Agent Ready</h3>
                  <p className="text-sm text-[var(--text-secondary)]">Type an instruction below to begin.</p>
                </div>
              ) : (
                interactions.map((interaction) => (
                  <div key={interaction.id} className="flex flex-col gap-4 bg-[var(--bg-container)] rounded-2xl p-5 border border-[var(--border)]">
                    {/* User Prompt */}
                    <div className="flex flex-col gap-1">
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                        Instruction
                      </span>
                      <p className="text-[var(--text-primary)] font-medium text-base">
                        {interaction.userPrompt}
                      </p>
                    </div>

                    {(interaction.agentLogs.length > 0 || interaction.agentResult) && (
                      <div className="h-px bg-[var(--border)] w-full my-1 opacity-80" />
                    )}

                    {/* Status stream */}
                    {interaction.agentLogs.length > 0 && (
                      <div className="flex flex-col gap-1.5">
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                          Agent Status
                        </span>
                        <div className="flex flex-col gap-1.5">
                          {interaction.agentLogs.map((log, i) => (
                            <div key={i} className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
                              {i === interaction.agentLogs.length - 1 && interaction.isStreaming ? (
                                <span className="w-1.5 h-1.5 rounded-full bg-[var(--button-dark)] animate-pulse" />
                              ) : (
                                <span className="w-1 h-1 rounded-full bg-[var(--text-muted)]" />
                              )}
                              <span className="capitalize">{log}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Final Result */}
                    {interaction.agentResult && (
                      <div className="flex flex-col gap-1.5 animate-fade-in mt-1">
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                          Result
                        </span>
                        <p className="text-[var(--text-primary)] text-sm leading-relaxed whitespace-pre-wrap">
                          {interaction.agentResult}
                        </p>
                      </div>
                    )}
                  </div>
                ))
              )}
              <div ref={bottomRef} />
            </div>

            {/* Sticky Input Area */}
            <div className="p-4 sm:px-8 sm:pb-8 bg-gradient-to-t from-white via-white to-transparent">
              <div className="relative border border-[var(--border-focus)] rounded-3xl bg-white shadow-sm hover:shadow-md transition-shadow focus-within:ring-2 focus-within:ring-[var(--border-focus)] flex items-end px-3 py-2">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => {
                    setInput(e.target.value);
                    setActiveTab(null);
                  }}
                  onKeyDown={handleKeyDown}
                  placeholder="E.g., What is Mohit's email address?"
                  disabled={isStreaming}
                  className="w-full bg-transparent text-base text-[var(--text-primary)] placeholder-[var(--text-muted)] outline-none resize-none pt-2.5 pb-2 px-2 max-h-[150px]"
                  rows={1}
                />
                
                <button
                  onClick={runAgent}
                  disabled={isStreaming || !input.trim()}
                  className="mb-1 ml-2 p-3 rounded-full transition-transform hover:scale-105 active:scale-95 disabled:opacity-40 disabled:hover:scale-100 bg-[var(--button-dark)] text-white shadow-sm flex items-center justify-center cursor-pointer shrink-0"
                  title="Execute Task"
                >
                  {isStreaming ? (
                    <svg className="animate-spin-slow w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <path strokeLinecap="round" d="M12 4v2m0 12v2m8-8h-2M6 12H4m13.66-5.66l-1.42 1.42m-11.31 11.31l-1.42-1.42m0-11.31l1.42 1.42m11.31 11.31l1.42-1.42" />
                    </svg>
                  ) : (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <polygon points="5 3 19 12 5 21 5 3"></polygon>
                    </svg>
                  )}
                </button>
              </div>
            </div>

          </div>
        </div>
      </div>
      
      {/* Footer minimal text */}
      <p className="text-sm text-[var(--text-muted)] text-center max-w-lg mt-auto pb-4">
        FlowPay requires connection to Google Sheets and Razorpay test mode to function correctly.
      </p>
    </div>
  );
}
