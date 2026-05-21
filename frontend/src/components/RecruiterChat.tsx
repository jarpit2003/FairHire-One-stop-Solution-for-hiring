import { useState, useRef, useEffect } from "react";
import { X, Send } from "lucide-react";
import { chatService } from "../services/api";
import { useJobs } from "../context/JobContext";

interface Message { role: "user" | "assistant"; content: string; }

const SUGGESTION_GROUPS = [
  { label: "Candidates", chips: ["Who are the top candidates?", "Which candidates to shortlist?", "Show hiring decisions", "Why were candidates rejected?"] },
  { label: "Pipeline",   chips: ["Show pipeline breakdown", "How many candidates applied?", "Show upcoming interviews", "Common skill gaps?"] },
  { label: "Templates",  chips: ["Write interview questions for a React developer", "Draft offer letter", "How to improve resumes?"] },
];

function renderMarkdown(text: string) {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let key = 0;
  for (const line of lines) {
    if (!line.trim()) { elements.push(<div key={key++} className="h-2" />); continue; }
    const num = line.match(/^(\d+)\.\s+(.*)/);
    if (num) { elements.push(<div key={key++} className="flex gap-2 text-sm leading-relaxed"><span className="font-bold flex-shrink-0 w-5" style={{ color: "#64748b" }}>{num[1]}.</span><span>{renderInline(num[2])}</span></div>); continue; }
    const bullet = line.match(/^[-•]\s+(.*)/);
    if (bullet) { elements.push(<div key={key++} className="flex gap-2 text-sm leading-relaxed"><span className="flex-shrink-0 mt-0.5" style={{ color: "#94a3b8" }}>•</span><span>{renderInline(bullet[1])}</span></div>); continue; }
    elements.push(<p key={key++} className="text-sm leading-relaxed">{renderInline(line)}</p>);
  }
  return <div className="space-y-0.5">{elements}</div>;
}

function renderInline(text: string): React.ReactNode {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith("**") && part.endsWith("**")
      ? <strong key={i} className="font-semibold" style={{ color: "#0f172a" }}>{part.slice(2, -2)}</strong>
      : <span key={i}>{part}</span>
  );
}

export default function RecruiterChat() {
  const { activeJob } = useJobs();
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hi, I'm your QuantumLogic assistant. Ask me anything about your candidates, pipeline, or hiring decisions." },
  ]);
  const [loading, setLoading] = useState(false);
  const [activeGroup, setActiveGroup] = useState(0);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesRef = useRef<HTMLDivElement>(null);

  // Stop Lenis from hijacking wheel events inside the messages area
  useEffect(() => {
    const el = messagesRef.current;
    if (!el) return;
    const stop = (e: WheelEvent) => e.stopPropagation();
    el.addEventListener("wheel", stop, { passive: true });
    return () => el.removeEventListener("wheel", stop);
  }, []);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, open, loading]);
  useEffect(() => { if (open) setTimeout(() => inputRef.current?.focus(), 100); }, [open]);

  const send = async (text: string) => {
    const msg = text.trim();
    if (!msg || loading) return;
    setInput("");
    const updated: Message[] = [...messages, { role: "user", content: msg }];
    setMessages(updated);
    setLoading(true);
    try {
      const { data } = await chatService.send(msg, updated.slice(-12).map((m) => ({ role: m.role, content: m.content })), activeJob?.id);
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Something went wrong. Please try again." }]);
    } finally { setLoading(false); }
  };

  return (
    <>
      {/* Floating button — matches btn-glass-dark: #131313 bg */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="fixed bottom-6 right-6 z-50 h-14 w-14 rounded-full flex items-center justify-center transition-all"
        style={{
          background: "#131313",
          boxShadow: "inset 0 0 12px rgba(255,255,255,1), 0px 0px 2px rgba(0,0,0,0.1), 0 4px 16px rgba(0,0,0,0.18)",
        }}
        title="AI Assistant"
      >
        {open
          ? <X className="h-5 w-5" style={{ color: "#fff" }} />
          : <img src="/message.png" alt="chat" className="h-7 w-7" style={{ filter: "brightness(0) invert(1)" }} />
        }
      </button>

      {/* Chat window */}
      {open && (
        <div
          className="fixed right-6 z-50 flex flex-col"
          style={{
            width: "min(400px, calc(100vw - 24px))",
            bottom: "80px",
            height: "min(560px, calc(100vh - 100px))",
            background: "rgba(255,255,255,0.92)",
            backdropFilter: "blur(24px)",
            WebkitBackdropFilter: "blur(24px)",
            border: "1px solid rgba(0,0,0,0.08)",
            borderRadius: "24px",
            boxShadow: "0px 0px 1px rgba(0,0,0,0.08), 0 8px 32px rgba(0,0,0,0.12)",
            overflow: "hidden",
          }}
        >
          {/* Header */}
          <div
            className="flex items-center justify-between px-4 py-3 flex-shrink-0"
            style={{ borderBottom: "1px solid rgba(0,0,0,0.07)", background: "rgba(255,255,255,0.6)" }}
          >
            <div>
              <p className="text-sm font-bold" style={{ color: "#0f172a" }}>QuantumLogic Assistant</p>
              <p className="text-xs" style={{ color: "#94a3b8" }}>{activeJob ? activeJob.title : "AI hiring co-pilot"}</p>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="p-1.5 rounded-lg transition-colors"
              style={{ color: "#94a3b8" }}
              onMouseEnter={e => (e.currentTarget.style.background = "rgba(0,0,0,0.05)")}
              onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Messages */}
          <div
            ref={messagesRef}
            data-lenis-prevent
            className="flex-1 overflow-y-auto p-4 space-y-3"
            style={{ minHeight: 0, overscrollBehavior: "contain", WebkitOverflowScrolling: "touch" }}
          >
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-2.5 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                <div
                  className="max-w-[85%] px-3.5 py-2.5 text-sm"
                  style={msg.role === "assistant"
                    ? {
                        background: "#f8fafc",
                        border: "1px solid rgba(0,0,0,0.07)",
                        color: "#334155",
                        borderRadius: "16px",
                        borderTopLeftRadius: "4px",
                      }
                    : {
                        background: "#131313",
                        boxShadow: "inset 0 0 12px rgba(255,255,255,0.6)",
                        color: "#ffffff",
                        borderRadius: "16px",
                        borderTopRightRadius: "4px",
                      }
                  }
                >
                  {msg.role === "assistant" ? renderMarkdown(msg.content) : msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-2">
                <div
                  className="px-4 py-3 flex items-center gap-1.5"
                  style={{ background: "#f8fafc", border: "1px solid rgba(0,0,0,0.07)", borderRadius: "16px", borderTopLeftRadius: "4px" }}
                >
                  <span className="h-1.5 w-1.5 rounded-full animate-bounce" style={{ background: "#94a3b8", animationDelay: "0ms" }} />
                  <span className="h-1.5 w-1.5 rounded-full animate-bounce" style={{ background: "#94a3b8", animationDelay: "150ms" }} />
                  <span className="h-1.5 w-1.5 rounded-full animate-bounce" style={{ background: "#94a3b8", animationDelay: "300ms" }} />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Suggestions */}
          {messages[messages.length - 1]?.role === "assistant" && !loading && (
            <div
              className="flex-shrink-0 px-3 pt-2 pb-2"
              style={{ borderTop: "1px solid rgba(0,0,0,0.06)", background: "rgba(248,250,252,0.8)" }}
            >
              {/* Group tabs */}
              <div className="flex gap-1 mb-2">
                {SUGGESTION_GROUPS.map((g, idx) => (
                  <button
                    key={g.label}
                    onClick={() => setActiveGroup(idx)}
                    className="text-xs px-2.5 py-1 rounded-full font-medium transition-colors"
                    style={activeGroup === idx
                      ? { background: "#131313", color: "#ffffff", boxShadow: "inset 0 0 12px rgba(255,255,255,0.8)" }
                      : { background: "#f1f5f9", color: "#64748b", boxShadow: "inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)" }
                    }
                  >
                    {g.label}
                  </button>
                ))}
              </div>
              {/* Chips */}
              <div className="flex flex-wrap gap-1.5">
                {SUGGESTION_GROUPS[activeGroup].chips.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="text-xs px-2.5 py-1 rounded-full text-left transition-colors"
                    style={{ background: "#f1f5f9", color: "#475569", boxShadow: "inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)" }}
                    onMouseEnter={e => { e.currentTarget.style.background = "#e2e8f0"; }}
                    onMouseLeave={e => { e.currentTarget.style.background = "#f1f5f9"; }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div
            className="px-3 py-3 flex gap-2 flex-shrink-0"
            style={{ borderTop: "1px solid rgba(0,0,0,0.07)" }}
          >
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send(input)}
              placeholder="Ask anything about hiring…"
              className="flex-1 rounded-xl px-3 py-2 text-sm focus:outline-none"
              style={{
                background: "#f1f5f9",
                border: "none",
                boxShadow: "inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)",
                color: "#0f172a",
              }}
              disabled={loading}
            />
            {/* Send button — matches btn-glass-dark exactly */}
            <button
              onClick={() => send(input)}
              disabled={!input.trim() || loading}
              className="h-9 w-9 rounded-xl flex items-center justify-center flex-shrink-0 disabled:opacity-40 transition-all"
              style={{
                background: "#131313",
                boxShadow: "inset 0 0 12px rgba(255,255,255,1), 0px 0px 2px rgba(0,0,0,0.1)",
              }}
              onMouseEnter={e => (e.currentTarget.style.opacity = "0.88")}
              onMouseLeave={e => (e.currentTarget.style.opacity = "1")}
            >
              <Send className="h-4 w-4" style={{ color: "#fff" }} />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
