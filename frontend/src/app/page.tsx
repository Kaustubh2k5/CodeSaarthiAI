"use client";

import { useState, useRef, useEffect } from "react";
import RepoGraph from "./components/RepoGraph";
import ChatPanel from "./components/ChatPanel";
import {
  Github,
  Search,
  Activity,
  Loader2,
  AlertCircle,
  CheckCircle2
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import Image from "next/image";

export default function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("IDLE");
  const [loading, setLoading] = useState(false);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const storedSession = localStorage.getItem("codesaathi-session");
    const storedRepo = localStorage.getItem("codesaathi-repo");
    const storedStatus = localStorage.getItem("codesaathi-status");

    if (storedSession) setSessionId(storedSession);
    if (storedRepo) setRepoUrl(storedRepo);
    if (storedStatus) setStatus(storedStatus);
  }, []);

  async function handleAnalyze() {
    if (!repoUrl.trim()) return;

    try {
      setLoading(true);
      setStatus("CREATING_SESSION");

      const createRes = await fetch("/api/create-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repoUrl }),
      });

      if (!createRes.ok) throw new Error("Failed to create session");

      const createData = await createRes.json();
      const newSessionId = createData.sessionId;

      setSessionId(newSessionId);
      localStorage.setItem("codesaathi-session", newSessionId);
      localStorage.setItem("codesaathi-repo", repoUrl);
      localStorage.setItem("codesaathi-status", "INGESTING");

      setStatus("INGESTING");

      const ingestRes = await fetch("/api/ingest-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId: newSessionId, repoUrl }),
      });

      if (!ingestRes.ok) throw new Error("Failed to start ingestion");

      pollingRef.current = setInterval(async () => {
        const statusRes = await fetch("/api/session-status", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sessionId: newSessionId }),
        });

        if (!statusRes.ok) return;

        const statusData = await statusRes.json();

        if (statusData.status === "READY") {
          setStatus("READY");
          setLoading(false);
          localStorage.setItem("codesaathi-status", "READY");
          clearInterval(pollingRef.current!);
        }

        if (statusData.status === "FAILED") {
          setStatus("FAILED");
          setLoading(false);
          localStorage.setItem("codesaathi-status", "FAILED");
          clearInterval(pollingRef.current!);
        }
      }, 3000);

    } catch (error) {
      console.error(error);
      setStatus("FAILED");
      setLoading(false);
    }
  }

  return (
    <div className="h-screen bg-black text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30">

      {/* HEADER */}
      <header className="h-14 border-b border-white/10 flex items-center justify-between px-4 bg-black/40 backdrop-blur-xl sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="relative w-16 h-16 rounded-xl bg-white/5  backdrop-blur-md flex items-center justify-center">
            <Image
              src="/icon.svg"
              alt="CodeSaarthi Logo"
              fill
              className="object-contain p-1"
              priority
            />
          </div>
          <span className="font-bold tracking-tighter text-lg">
            CodeSaarthi
          </span>
        </div>

        <div className="flex items-center gap-4 flex-1 max-w-2xl px-8">
          <div className="relative flex-1">
            <Github className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="https://github.com/username/repository"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              className="w-full bg-white/5 border border-white/10 pl-10 pr-4 py-1.5 rounded-full text-sm outline-none focus:border-cyan-400/40"
            />
          </div>
          <button
            onClick={handleAnalyze}
            disabled={loading || !repoUrl}
            className="bg-slate-100 text-black px-6 py-1.5 rounded-full text-sm font-semibold disabled:opacity-20 flex items-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            {loading ? "Analyzing" : "Analyze"}
          </button>
        </div>
      </header>

      {/* MAIN */}
      <div className="flex flex-1 overflow-hidden">

        <main className="flex-1 flex flex-col bg-black relative">

          {/* STATUS BAR */}
          <div className="h-10 border-b border-white/10 flex items-center px-4 bg-black/30 backdrop-blur-md">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                status === "READY"
                  ? "bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.5)]"
                  : status === "FAILED"
                  ? "bg-red-500"
                  : "bg-amber-500 animate-pulse"
              }`} />
              <span className="text-xs font-mono uppercase tracking-widest text-slate-400">
                {status}
              </span>
            </div>
          </div>

          {/* GRAPH */}
          <div className="flex-1 relative overflow-hidden">
            <AnimatePresence mode="wait">
              {status === "READY" && sessionId && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="w-full h-full"
                >
                  <RepoGraph sessionId={sessionId} />
                </motion.div>
              )}

              {status === "FAILED" && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="absolute inset-0 flex flex-col items-center justify-center text-red-500"
                >
                  <AlertCircle className="w-12 h-12 mb-4" />
                  <h2 className="text-lg font-medium mb-2">
                    Analysis Failed
                  </h2>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </main>

        <ChatPanel sessionId={sessionId} />
      </div>

      {/* FOOTER */}
      <footer className="h-6 border-t border-white/10 bg-black/40 backdrop-blur-md flex items-center px-4 justify-between text-[9px] font-mono text-slate-500 uppercase">
        <div className="flex items-center gap-1">
          <CheckCircle2 className="w-2.5 h-2.5 text-cyan-400" />
          SYSTEM READY
        </div>
        <div>SESSION: {sessionId || "NULL"}</div>
      </footer>
    </div>
  );
}