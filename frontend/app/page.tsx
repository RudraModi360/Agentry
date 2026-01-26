"use client"

import React from "react"

import { useState } from "react"
import Link from "next/link"
import { useTheme } from "next-themes"
import {
  AgentryLogo,
  PlayIcon,
  GitHubIcon,
  MoonIcon,
  SunIcon,
  GridIcon,
  FileIcon,
  WrenchIcon,
  MailIcon,
  CopyIcon,
} from "@/components/icons"

export default function LandingPage() {
  const { theme, setTheme } = useTheme()
  const [copied, setCopied] = useState(false)

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark")
  }

  const codeSnippet = `from agentry import Agent

agent = Agent(llm="ollama", model="llama3.2")
agent.load_default_tools()

response = await agent.chat("Hello!")
print(response)`

  const handleCopy = () => {
    navigator.clipboard.writeText(codeSnippet)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Subtle gradient background */}
      <div className="fixed inset-0 bg-gradient-to-br from-background via-background to-emerald-950/20 pointer-events-none" />

      {/* Navigation */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-4 max-w-7xl mx-auto">
        <Link href="/" className="flex items-center gap-2">
          <AgentryLogo className="w-7 h-7 text-foreground" />
          <span className="text-xl font-semibold text-foreground">Agentry</span>
        </Link>
        <div className="flex items-center gap-6">
          <Link
            href="/chat"
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            Chat
          </Link>
          <Link
            href="https://github.com"
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            GitHub
          </Link>
          <button
            type="button"
            onClick={toggleTheme}
            className="p-2 rounded-full bg-secondary hover:bg-secondary/80 transition-colors"
          >
            {theme === "dark" ? (
              <MoonIcon className="w-5 h-5 text-foreground" />
            ) : (
              <SunIcon className="w-5 h-5 text-foreground" />
            )}
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 max-w-7xl mx-auto px-6 pt-16 pb-24">
        <div className="grid lg:grid-cols-2 gap-16 items-start">
          {/* Left Column - Hero */}
          <div className="pt-8">
            <h1 className="text-5xl lg:text-6xl font-bold text-foreground leading-tight tracking-tight text-balance">
              Build Real-World AI Agents from Scratch
            </h1>
            <p className="mt-6 text-lg text-muted-foreground leading-relaxed max-w-lg">
              A clean, Python-first framework for building AI agents with
              sessions, tools, and multiple LLM providers.
            </p>
            <div className="mt-10 flex items-center gap-4">
              <Link
                href="/login"
                className="group flex items-center gap-2 px-6 py-3 bg-foreground text-background rounded-lg font-medium hover:bg-foreground/90 transition-all shadow-lg shadow-foreground/10"
              >
                <PlayIcon className="w-4 h-4" />
                Get Started
              </Link>
              <Link
                href="https://github.com"
                className="flex items-center gap-2 px-6 py-3 bg-secondary text-foreground rounded-lg font-medium hover:bg-secondary/80 transition-colors"
              >
                <GitHubIcon className="w-5 h-5" />
                View on GitHub
              </Link>
            </div>
          </div>

          {/* Right Column - Code + Features */}
          <div className="space-y-8">
            {/* Quick Start Label */}
            <p className="text-emerald-400 text-sm font-medium tracking-wider uppercase">
              Quick Start
            </p>

            {/* Code Block */}
            <div className="bg-card rounded-xl border border-border overflow-hidden">
              {/* macOS-style header */}
              <div className="flex items-center justify-between px-4 py-3 bg-muted/50">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500" />
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                </div>
                <button
                  type="button"
                  onClick={handleCopy}
                  className="flex items-center gap-2 px-3 py-1 text-sm text-muted-foreground hover:text-foreground bg-secondary/50 rounded-md transition-colors"
                >
                  <CopyIcon className="w-4 h-4" />
                  {copied ? "Copied!" : "Copy"}
                </button>
              </div>
              {/* Code Content */}
              <div className="p-6 font-mono text-sm leading-relaxed overflow-x-auto">
                <div>
                  <span className="text-purple-400">from</span>{" "}
                  <span className="text-foreground">agentry</span>{" "}
                  <span className="text-purple-400">import</span>{" "}
                  <span className="text-foreground">Agent</span>
                </div>
                <div className="mt-4">
                  <span className="text-foreground">agent</span>{" "}
                  <span className="text-muted-foreground">=</span>{" "}
                  <span className="text-foreground">Agent</span>
                  <span className="text-muted-foreground">(</span>
                  <span className="text-foreground">llm</span>
                  <span className="text-muted-foreground">=</span>
                  <span className="text-emerald-400">{'"ollama"'}</span>
                  <span className="text-muted-foreground">,</span>{" "}
                  <span className="text-foreground">model</span>
                  <span className="text-muted-foreground">=</span>
                  <span className="text-emerald-400">{'"llama3.2"'}</span>
                  <span className="text-muted-foreground">)</span>
                </div>
                <div>
                  <span className="text-foreground">agent</span>
                  <span className="text-muted-foreground">.</span>
                  <span className="text-foreground">load_default_tools</span>
                  <span className="text-muted-foreground">()</span>
                </div>
                <div className="mt-4">
                  <span className="text-foreground">response</span>{" "}
                  <span className="text-muted-foreground">=</span>{" "}
                  <span className="text-purple-400">await</span>{" "}
                  <span className="text-foreground">agent</span>
                  <span className="text-muted-foreground">.</span>
                  <span className="text-yellow-400">chat</span>
                  <span className="text-muted-foreground">(</span>
                  <span className="text-emerald-400">{'"Hello!"'}</span>
                  <span className="text-muted-foreground">)</span>
                </div>
                <div>
                  <span className="text-yellow-400">print</span>
                  <span className="text-muted-foreground">(</span>
                  <span className="text-foreground">response</span>
                  <span className="text-muted-foreground">)</span>
                </div>
              </div>
            </div>

            {/* Features Label */}
            <p className="text-emerald-400 text-sm font-medium tracking-wider uppercase pt-4">
              Features
            </p>

            {/* Feature Cards */}
            <div className="space-y-3">
              <FeatureCard
                icon={<GridIcon className="w-5 h-5" />}
                title="Unified Architecture"
                description="One API across Standard, MCP, and Copilot modes."
              />
              <FeatureCard
                icon={<FileIcon className="w-5 h-5" />}
                title="Persistent Sessions"
                description="Sessions saved with full history and metadata."
              />
              <FeatureCard
                icon={<WrenchIcon className="w-5 h-5" />}
                title="Custom Tools"
                description="Create tools from any Python function."
              />
              <FeatureCard
                icon={<MailIcon className="w-5 h-5" />}
                title="Multiple Providers"
                description="Works with Ollama, Groq, Gemini, and Azure."
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <div className="flex items-start gap-4 p-4 bg-card/50 rounded-xl border border-border/50 hover:border-border transition-colors">
      <div className="p-2 bg-secondary rounded-lg text-muted-foreground">
        {icon}
      </div>
      <div>
        <h3 className="font-semibold text-foreground">{title}</h3>
        <p className="text-sm text-muted-foreground mt-0.5">{description}</p>
      </div>
    </div>
  )
}
