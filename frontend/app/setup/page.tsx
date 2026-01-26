"use client"

import React from "react"
import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useTheme } from "next-themes"
import { AgentryLogo, MoonIcon, SunIcon, CheckIcon, ArrowLeftIcon, ComputerIcon, CloudIcon, ToolsIcon } from "@/components/icons"

type Provider = "ollama" | "groq" | "gemini" | "azure"
type OllamaMode = "local" | "cloud"
type SetupStep = "provider" | "config" | "model"

interface ProviderConfig {
  id: Provider
  name: string
  description: string
  badge: string
  badgeColor: string
  icon: React.ReactNode
}

interface OllamaModel {
  id: string
  name: string
  size: string
  hasTools: boolean
}

const providers: ProviderConfig[] = [
  {
    id: "ollama",
    name: "Ollama",
    description: "Run models locally on your machine or use free cloud models for learning.",
    badge: "Local + Cloud",
    badgeColor: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    icon: (
      <div className="w-12 h-12 bg-secondary rounded-lg flex items-center justify-center">
        <svg viewBox="0 0 24 24" className="w-7 h-7 text-foreground" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
        </svg>
      </div>
    ),
  },
  {
    id: "groq",
    name: "Groq",
    description: "Ultra-fast inference powered by LPU technology. Requires API key.",
    badge: "Cloud API",
    badgeColor: "bg-orange-500/20 text-orange-400 border-orange-500/30",
    icon: (
      <div className="w-12 h-12 bg-orange-600 rounded-lg flex items-center justify-center">
        <span className="text-xl font-bold text-white">9</span>
      </div>
    ),
  },
  {
    id: "gemini",
    name: "Google Gemini",
    description: "Google's most capable AI models with advanced reasoning.",
    badge: "Cloud API",
    badgeColor: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    icon: (
      <div className="w-12 h-12 bg-secondary rounded-lg flex items-center justify-center">
        <svg viewBox="0 0 24 24" className="w-7 h-7 text-blue-400" fill="currentColor">
          <path d="M12 2L9.19 8.63L2 9.24l5.46 4.73L5.82 21L12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2z" />
        </svg>
      </div>
    ),
  },
  {
    id: "azure",
    name: "Azure OpenAI",
    description: "Enterprise-grade AI. Requires Endpoint and API Key.",
    badge: "Cloud API",
    badgeColor: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    icon: (
      <div className="w-12 h-12 bg-secondary rounded-lg flex items-center justify-center">
        <span className="text-2xl font-bold text-blue-500">A</span>
      </div>
    ),
  },
]

const ollamaModels: OllamaModel[] = [
  { id: "qwen3-embedding", name: "qwen3-embedding:0.6b", size: "0.6GB", hasTools: true },
  { id: "qwen3-coder", name: "qwen3-coder:480b-cloud", size: "0.0GB", hasTools: true },
  { id: "gpt-oss-20b", name: "gpt-oss:20b-cloud", size: "0.0GB", hasTools: true },
  { id: "gpt-oss-120b", name: "gpt-oss:120b-cloud", size: "0.0GB", hasTools: true },
]

export default function SetupPage() {
  const router = useRouter()
  const { theme, setTheme } = useTheme()
  const [step, setStep] = useState<SetupStep>("provider")
  const [selectedProvider, setSelectedProvider] = useState<Provider>("azure")
  const [ollamaMode, setOllamaMode] = useState<OllamaMode>("cloud")
  const [ollamaApiKey, setOllamaApiKey] = useState("")
  const [selectedOllamaModel, setSelectedOllamaModel] = useState<string>("")
  const [customModel, setCustomModel] = useState("")
  const [currentProvider] = useState<Provider>("azure")

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark")
  }

  const handleContinue = () => {
    if (step === "provider") {
      if (selectedProvider === "ollama") {
        setStep("config")
      } else {
        // For other providers, go directly to chat
        router.push("/chat")
      }
    } else if (step === "config") {
      if (selectedProvider === "ollama") {
        setStep("model")
      } else {
        router.push("/chat")
      }
    } else {
      router.push("/chat")
    }
  }

  const handleBack = () => {
    if (step === "model") {
      setStep("config")
    } else if (step === "config") {
      setStep("provider")
    }
  }

  const handleSkip = () => {
    router.push("/chat")
  }

  const handleLogout = () => {
    router.push("/login")
  }

  const getStepIndicator = () => {
    if (selectedProvider === "ollama") {
      return (
        <div className="flex items-center justify-center gap-2 mb-8">
          <div className={`w-3 h-3 rounded-full ${step === "provider" ? "bg-foreground" : "bg-muted"}`} />
          <div className={`w-3 h-3 rounded-full ${step === "config" ? "bg-foreground" : "bg-muted"}`} />
          <div className={`w-3 h-3 rounded-full ${step === "model" ? "bg-foreground" : "bg-muted"}`} />
        </div>
      )
    }
    return (
      <div className="flex items-center justify-center gap-2 mb-8">
        <div className="w-3 h-3 rounded-full bg-foreground" />
        <div className="w-3 h-3 rounded-full bg-muted" />
        <div className="w-3 h-3 rounded-full bg-muted" />
      </div>
    )
  }

  const renderProviderStep = () => (
    <>
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-foreground">
          Configure Your AI Provider
        </h1>
        <p className="mt-3 text-muted-foreground text-lg">
          Choose how you want to power your AI assistant
        </p>
      </div>

      {getStepIndicator()}

      {/* Current Provider Banner */}
      <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg px-6 py-3 mb-8 text-center">
        <p className="text-emerald-400">
          {"You're currently using Azure. You can reconfigure or skip to chat."}
        </p>
      </div>

      {/* Provider Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {providers.map((provider) => (
          <button
            key={provider.id}
            type="button"
            onClick={() => setSelectedProvider(provider.id)}
            className={`relative p-6 text-left rounded-xl border transition-all ${
              selectedProvider === provider.id
                ? "bg-card border-foreground/50 ring-1 ring-foreground/20"
                : "bg-card/50 border-border hover:border-border/80"
            }`}
          >
            {/* Selected checkmark */}
            {selectedProvider === provider.id && (
              <div className="absolute top-4 right-4 w-6 h-6 rounded-full bg-foreground flex items-center justify-center">
                <CheckIcon className="w-4 h-4 text-background" />
              </div>
            )}

            {/* Icon */}
            <div className="mb-4">{provider.icon}</div>

            {/* Content */}
            <h3 className="text-lg font-semibold text-foreground mb-2">
              {provider.name}
            </h3>
            <p className="text-sm text-muted-foreground mb-4 leading-relaxed">
              {provider.description}
            </p>

            {/* Badge */}
            <span
              className={`inline-block px-3 py-1 text-xs font-medium rounded-full border ${provider.badgeColor}`}
            >
              {provider.badge}
            </span>
          </button>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-center gap-4">
        <button
          type="button"
          onClick={handleSkip}
          className="px-8 py-3 bg-secondary text-foreground font-medium rounded-lg hover:bg-secondary/80 transition-colors"
        >
          {"Skip -> Go to Chat"}
        </button>
        <button
          type="button"
          onClick={handleLogout}
          className="flex items-center gap-2 px-8 py-3 bg-secondary text-foreground font-medium rounded-lg hover:bg-secondary/80 transition-colors"
        >
          <ArrowLeftIcon className="w-4 h-4" />
          Logout
        </button>
        <button
          type="button"
          onClick={handleContinue}
          className="flex items-center gap-2 px-8 py-3 bg-foreground text-background font-medium rounded-lg hover:bg-foreground/90 transition-colors"
        >
          {"Continue ->"}
        </button>
      </div>
    </>
  )

  const renderOllamaConfigStep = () => (
    <>
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-foreground">
          Provider Configuration
        </h1>
        <p className="mt-3 text-muted-foreground text-lg">
          Set up your provider settings and API key
        </p>
      </div>

      {getStepIndicator()}

      {/* Ollama Mode Selection */}
      <div className="bg-card border border-border rounded-xl p-6 mb-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">
          Choose Ollama Mode
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            type="button"
            onClick={() => setOllamaMode("local")}
            className={`p-4 text-left rounded-lg border transition-all ${
              ollamaMode === "local"
                ? "bg-secondary border-foreground/50"
                : "bg-card/50 border-border hover:border-border/80"
            }`}
          >
            <div className="flex items-center gap-3 mb-2">
              <ComputerIcon className="w-5 h-5 text-blue-400" />
              <span className="font-medium text-foreground">Local Models</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Run models on your machine. No API key required.
            </p>
          </button>
          <button
            type="button"
            onClick={() => setOllamaMode("cloud")}
            className={`p-4 text-left rounded-lg border transition-all ${
              ollamaMode === "cloud"
                ? "bg-secondary border-foreground/50"
                : "bg-card/50 border-border hover:border-border/80"
            }`}
          >
            <div className="flex items-center gap-3 mb-2">
              <CloudIcon className="w-5 h-5 text-blue-400" />
              <span className="font-medium text-foreground">Cloud Models</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Use free cloud models for learning. Requires Ollama API key.
            </p>
          </button>
        </div>
      </div>

      {/* API Key Input (for cloud mode) */}
      {ollamaMode === "cloud" && (
        <div className="bg-card border border-border rounded-xl p-6 mb-6">
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Ollama API Key
          </h3>
          <p className="text-sm text-muted-foreground mb-4">
            Required for cloud models. (Your saved key is pre-filled)
          </p>
          <input
            type="password"
            value={ollamaApiKey}
            onChange={(e) => setOllamaApiKey(e.target.value)}
            placeholder="Enter your Ollama API key"
            className="w-full px-4 py-3 bg-input border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/50"
          />
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-center gap-4">
        <button
          type="button"
          onClick={handleBack}
          className="flex items-center gap-2 px-8 py-3 bg-secondary text-foreground font-medium rounded-lg hover:bg-secondary/80 transition-colors"
        >
          <ArrowLeftIcon className="w-4 h-4" />
          Back
        </button>
        <button
          type="button"
          onClick={handleContinue}
          className="flex items-center gap-2 px-8 py-3 bg-foreground text-background font-medium rounded-lg hover:bg-foreground/90 transition-colors"
        >
          {"Continue ->"}
        </button>
      </div>
    </>
  )

  const renderModelSelectionStep = () => (
    <>
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-foreground">
          Select Your Model
        </h1>
        <p className="mt-3 text-muted-foreground text-lg">
          Choose the AI model you want to use
        </p>
      </div>

      {getStepIndicator()}

      {/* Model Selection */}
      <div className="bg-card border border-border rounded-xl p-6 mb-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">
          Select a Ollama Model
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {ollamaModels.map((model) => (
            <button
              key={model.id}
              type="button"
              onClick={() => setSelectedOllamaModel(model.id)}
              className={`p-4 text-left rounded-lg border transition-all ${
                selectedOllamaModel === model.id
                  ? "bg-secondary border-foreground/50"
                  : "bg-card/50 border-border hover:border-border/80"
              }`}
            >
              <p className="font-medium text-foreground mb-1">{model.name}</p>
              <p className="text-xs text-muted-foreground mb-3">Size: {model.size}</p>
              {model.hasTools && (
                <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded">
                  <ToolsIcon className="w-3 h-3" />
                  TOOLS
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Custom Model Input */}
      <div className="bg-card border border-border rounded-xl p-6 mb-8">
        <h3 className="text-lg font-semibold text-foreground mb-4">
          Or run the other Ollama model
        </h3>
        <input
          type="text"
          value={customModel}
          onChange={(e) => setCustomModel(e.target.value)}
          placeholder="e.g. qwen2.5-coder:7b"
          className="w-full px-4 py-3 bg-input border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/50"
        />
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-center gap-4">
        <button
          type="button"
          onClick={handleBack}
          className="flex items-center gap-2 px-8 py-3 bg-secondary text-foreground font-medium rounded-lg hover:bg-secondary/80 transition-colors"
        >
          <ArrowLeftIcon className="w-4 h-4" />
          Back
        </button>
        <button
          type="button"
          onClick={handleContinue}
          className="px-8 py-3 bg-foreground text-background font-medium rounded-lg hover:bg-foreground/90 transition-colors"
        >
          Complete Setup
        </button>
      </div>
    </>
  )

  return (
    <div className="min-h-screen bg-background">
      {/* Subtle gradient */}
      <div className="fixed inset-0 bg-gradient-to-b from-background via-background to-blue-950/10 pointer-events-none" />

      {/* Navigation */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-4 max-w-7xl mx-auto">
        <Link href="/" className="flex items-center gap-2">
          <AgentryLogo className="w-7 h-7 text-foreground" />
          <span className="text-xl font-semibold text-foreground">Agentry</span>
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
      </nav>

      {/* Main Content */}
      <main className="relative z-10 max-w-5xl mx-auto px-6 py-12">
        {step === "provider" && renderProviderStep()}
        {step === "config" && selectedProvider === "ollama" && renderOllamaConfigStep()}
        {step === "model" && selectedProvider === "ollama" && renderModelSelectionStep()}
      </main>
    </div>
  )
}
