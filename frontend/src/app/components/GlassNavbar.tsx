"use client";

import { Search } from "lucide-react";
import { useState } from "react";

export default function GlassNavbar() {
  const [query, setQuery] = useState("");

  return (
    <div className="fixed top-6 left-1/2 -translate-x-1/2 z-50">
      <div className="flex items-center gap-8 px-8 py-3 rounded-full 
                      bg-black/60 backdrop-blur-2xl 
                      border border-white/10 
                      shadow-[0_10px_40px_rgba(0,0,0,0.6)]">

        {/* BRAND */}
        <div className="text-lg font-semibold tracking-tight">
          <span className="text-white">Code</span>
          <span className="text-cyan-400">Now</span>
        </div>

        {/* SEARCH */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search repository..."
            className="w-64 bg-white/5 border border-white/10 
                       pl-10 pr-4 py-2 rounded-full 
                       text-sm text-white placeholder:text-slate-500 
                       outline-none focus:border-cyan-400/40 
                       focus:ring-1 focus:ring-cyan-400/20 
                       transition-all"
          />
        </div>

        {/* RIGHT TEXT (optional like Map) */}
        <div className="text-sm text-slate-400 hover:text-white transition cursor-pointer">
          Explore
        </div>
      </div>
    </div>
  );
}