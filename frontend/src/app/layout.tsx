import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "CodeSaarthi",
    template: "%s | CodeSaarthi",
  },
  description:
    "AI-powered repository intelligence and architectural analysis platform.",
  keywords: [
    "AI",
    "Code Analysis",
    "Repository Visualization",
    "Developer Tools",
    "Architecture Explorer",
  ],
  authors: [{ name: "CodeSaarthi Team" }],
  metadataBase: new URL("https://codesaarthi.app"), // change if needed
  themeColor: "#0b1120",
  openGraph: {
    title: "CodeSaarthi",
    description:
      "Visualize and analyze repositories with AI-powered intelligence.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body
        className={`
          ${inter.variable} 
          ${jetbrainsMono.variable}
          bg-[#0b1120] 
          text-slate-200 
          antialiased
          font-sans
        `}
      >
        {children}
      </body>
    </html>
  );
}