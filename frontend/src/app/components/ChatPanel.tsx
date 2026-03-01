"use client";

import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { Send, Cpu, Terminal, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

interface Props {
  sessionId: string | null;
}

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPanel({ sessionId }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  async function sendMessage() {
    if (!input.trim() || loading) return;

    if (!sessionId) {
      alert("Analyze a repository first.");
      return;
    }

    const question = input;
    setInput("");

    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
    ]);

    setLoading(true);

    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId, question }),
      });

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer || "No response received.",
        },
      ]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "⚠️ Something went wrong. Please try again.",
        },
      ]);
    }

    setLoading(false);
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="w-[420px] flex flex-col bg-black/40 backdrop-blur-2xl border-l border-white/10 shadow-2xl">

      {/* HEADER (Glass) */}
      <div className="p-4 border-b border-white/10 bg-black/30 backdrop-blur-xl flex items-center gap-2">
        <Cpu className="w-5 h-5 text-cyan-400 drop-shadow-[0_0_6px_rgba(6,182,212,0.6)]" />
        <span className="text-sm font-bold tracking-tight text-white">
          CODE ANALYST
        </span>
      </div>

      {/* MESSAGES */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin scrollbar-thumb-white/10">

        <AnimatePresence initial={false}>
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-2 opacity-50">
              <Cpu className="w-12 h-12" />
              <p className="text-xs font-mono uppercase tracking-widest">
                Awaiting Input
              </p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-3 ${
                msg.role === "user" ? "flex-row-reverse" : ""
              }`}
            >
              {/* ICON */}
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                  msg.role === "user"
                    ? "bg-white/5 border border-white/10 backdrop-blur"
                    : "bg-cyan-500/10 border border-cyan-400/20 backdrop-blur"
                }`}
              >
                {msg.role === "user" ? (
                  <Terminal className="w-4 h-4 text-slate-400" />
                ) : (
                  <Cpu className="w-4 h-4 text-cyan-400" />
                )}
              </div>

              {/* MESSAGE BUBBLE (Glass) */}
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed backdrop-blur-xl border ${
                  msg.role === "user"
                    ? "bg-white/5 border-white/10 text-slate-200"
                    : "bg-black/40 border-white/10 text-slate-300"
                }`}
              >
                {msg.role === "assistant" ? (
                  <div className="prose prose-invert prose-sm max-w-none prose-pre:bg-black/40 prose-pre:border prose-pre:border-white/10">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeHighlight]}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <div className="whitespace-pre-wrap font-sans">
                    {msg.content}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {loading && (
          <div className="flex items-center gap-2 text-slate-500 text-xs font-mono px-12">
            <Loader2 className="w-3 h-3 animate-spin" />
            <span>ANALYZING REPOSITORY...</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* INPUT (Glass) */}
      <div className="p-4 border-t border-white/10 bg-black/30 backdrop-blur-xl">
        <div className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about architecture, logic, or files..."
            className="w-full bg-white/5 backdrop-blur border border-white/10 pl-4 pr-12 py-3 rounded-xl text-sm outline-none text-slate-200 placeholder:text-slate-500 focus:border-cyan-400/40 focus:ring-1 focus:ring-cyan-400/20 transition-all"
            onKeyDown={(e) => {
              if (e.key === "Enter") sendMessage();
            }}
          />

          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="absolute right-2 p-2 bg-cyan-600 hover:bg-cyan-500 text-black rounded-lg transition-all disabled:opacity-20 disabled:grayscale"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>

        <p className="mt-2 text-[10px] text-center text-slate-500 font-mono uppercase tracking-tighter">
          Powered by AWS
        </p>
      </div>
    </div>
  );
}