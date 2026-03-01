"use client";

import { useEffect, useState, useRef } from "react";
import dynamic from "next/dynamic";
import * as d3 from "d3-hierarchy";

const ForceGraph2D = dynamic(
  () => import("react-force-graph-2d"),
  { ssr: false }
);

interface Props {
  sessionId: string;
}

export default function RepoGraph({ sessionId }: Props) {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const containerRef = useRef<HTMLDivElement>(null);
  const fgRef = useRef<any>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    async function loadGraph() {
      try {
        const response = await fetch("/api/repo-graph", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sessionId }),
        });

        if (!response.ok) throw new Error("Failed to fetch graph");

        const data = await response.json();

        console.log("API Nodes:", data.nodes);

        if (!data.nodes || data.nodes.length === 0) {
          console.warn("No nodes returned");
          return;
        }

        // -----------------------------
        // BUILD PATH-BASED TREE
        // -----------------------------
        const nodesById: Record<string, any> = {};

        // Artificial ROOT
        nodesById["ROOT"] = {
          id: "ROOT",
          label: "Repository",
          type: "folder",
          children: []
        };

        // Register all nodes
        data.nodes.forEach((n: any) => {
          nodesById[n.id] = {
            ...n,
            children: []
          };
        });

        // Attach children using path structure
        data.nodes.forEach((n: any) => {
          const parts = n.id.split("/");

          if (parts.length === 1) {
            // top-level
            nodesById["ROOT"].children.push(nodesById[n.id]);
          } else {
            const parentPath = parts.slice(0, -1).join("/");

            if (nodesById[parentPath]) {
              nodesById[parentPath].children.push(nodesById[n.id]);
            } else {
              // fallback
              nodesById["ROOT"].children.push(nodesById[n.id]);
            }
          }
        });

        const root = d3.hierarchy(nodesById["ROOT"]);

        console.log("Hierarchy size:", root.descendants().length);

        // -----------------------------
        // TREE LAYOUT
        // -----------------------------
        const treeLayout = d3.tree().nodeSize([50, 180]);
        treeLayout(root as any);

        const nodes: any[] = [];
        const links: any[] = [];

        root.descendants().forEach((d: any) => {
          nodes.push({
            id: d.data.id,
            name: d.data.id === "ROOT" ? "" : d.data.label,
            type: d.data.type,
            x: d.y,
            y: d.x,
            fx: d.y,
            fy: d.x
          });
        });

        root.links().forEach((l: any) => {
          links.push({
            source: l.source.data.id,
            target: l.target.data.id
          });
        });

        console.log("Final nodes:", nodes.length);
        console.log("Final links:", links.length);

        setGraphData({ nodes, links });

        setTimeout(() => {
          fgRef.current?.zoomToFit(400, 100);
        }, 100);

      } catch (error) {
        console.error("Graph load error:", error);
      }
    }

    if (sessionId) loadGraph();
  }, [sessionId]);

  // -----------------------------
  // Resize Handling
  // -----------------------------
  useEffect(() => {
    if (!containerRef.current) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full bg-black overflow-hidden"
    >
      {/* GLASS PANEL LAYER */}
      <div className="absolute inset-0 bg-black/30 backdrop-blur-2xl border border-white/10 rounded-none pointer-events-none" />
  
      {/* FORCE GRAPH */}
      <ForceGraph2D
        ref={fgRef}
        graphData={graphData}
        width={dimensions.width}
        height={dimensions.height}
        backgroundColor="rgba(0,0,0,0)"
        nodeLabel="name"
        linkColor={() => "rgba(255,255,255,0.15)"}
        linkWidth={1.2}
        d3AlphaDecay={1}
        d3VelocityDecay={1}
        nodeCanvasObject={(node: any, ctx, globalScale) => {
          const label = node.name;
          const isFolder = node.type === "folder";
  
          const fontSize = 14 / globalScale;
          const radius = isFolder ? 6 : 4;
  
          ctx.beginPath();
          ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
  
          if (isFolder) {
            ctx.fillStyle = "#06b6d4";
            ctx.shadowColor = "rgba(6,182,212,0.7)";
            ctx.shadowBlur = 12;
          } else {
            ctx.fillStyle = "#94a3b8";
            ctx.shadowBlur = 0;
          }
  
          ctx.fill();
          ctx.shadowBlur = 0;
  
          if (label) {
            ctx.font = `500 ${fontSize}px Inter, system-ui, sans-serif`;
            ctx.textAlign = "left";
            ctx.textBaseline = "middle";
            ctx.fillStyle = isFolder
              ? "#f1f5f9"
              : "rgba(241,245,249,0.7)";
            ctx.fillText(label, node.x + radius + 8, node.y);
          }
        }}
      />
  
      {/* SUBTLE GLASS HIGHLIGHT */}
      <div className="absolute inset-0 pointer-events-none bg-gradient-to-b from-white/5 to-transparent" />
  
      {/* SOFT GRID */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.03]"
        style={{
          backgroundImage:
            "radial-gradient(rgba(255,255,255,0.2) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />
  
      {/* VIGNETTE */}
      <div className="absolute inset-0 pointer-events-none shadow-[inset_0_0_200px_rgba(0,0,0,0.8)]" />
    </div>
  );
}