"use client"

import React from "react"
import { useState } from "react"
import Image from "next/image"
import { useTheme } from "next-themes"
import {
  AgentryLogo,
  ChevronDownIcon,
  ChevronUpIcon,
  MoonIcon,
  SunIcon,
  LogoutIcon,
  CheckIcon,
  ExternalLinkIcon,
  SettingsIcon,
  EditIcon,
} from "@/components/icons"
import router from "next/router"
import { MCPConfigModal } from "./modals"

interface Model {
  id: string
  name: string
  provider: string
  active?: boolean
}

interface Agent {
  id: string
  name: string
  description?: string
  icon: React.ReactNode
}

interface TopBarProps {
  models: Model[]
  agents: Agent[]
  selectedModel: string
  selectedAgent: string
  onModelSelect: (id: string) => void
  onAgentSelect: (id: string) => void
  onManageModels: () => void
  onEditConfig: (model: Model) => void
}

export function TopBar({
  models,
  agents,
  selectedModel,
  selectedAgent,
  onModelSelect,
  onAgentSelect,
  onManageModels,
  onEditConfig,
}: TopBarProps) {
  const { theme, setTheme } = useTheme()
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false)
  const [agentDropdownOpen, setAgentDropdownOpen] = useState(false)
  const [hoveredAgent, setHoveredAgent] = useState<string | null>(null)

  const currentModel = models.find((m) => m.id === selectedModel)
  const currentAgent = agents.find((a) => a.id === selectedAgent)

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark")
  }

  const handleSignOut = () => {
    router.push("/login")
  }

  const [mcpModalOpen, setMCPModalOpen] = useState(false)

  const onMCPClick = () => {
    setMCPModalOpen(true)
  }

  return (
    <header className="h-14 border-b border-border flex items-center justify-between px-4">
      {/* Left side - Model selector */}
      <div className="flex items-center gap-4">
        {/* Brand Name with Dropdown */}
        <div className="relative">
          <button
            type="button"
            onClick={() => {
              setModelDropdownOpen(!modelDropdownOpen)
              setAgentDropdownOpen(false)
            }}
            className="flex items-center gap-2 text-foreground font-semibold hover:bg-secondary px-3 py-2 rounded-lg transition-colors"
          >
            <span className="text-lg">Agentry</span>
            {modelDropdownOpen ? (
              <ChevronUpIcon className="w-4 h-4" />
            ) : (
              <ChevronDownIcon className="w-4 h-4" />
            )}
          </button>

          {/* Model Dropdown */}
          {modelDropdownOpen && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setModelDropdownOpen(false)}
              />
              <div className="absolute top-full left-0 mt-1 w-80 bg-popover border border-border rounded-xl shadow-xl z-50 overflow-hidden">
                <div className="px-4 py-3 border-b border-border">
                  <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Select Provider
                  </h4>
                </div>
                <div className="p-2">
                  {models.map((model) => (
                    <div
                      key={model.id}
                      className={`flex items-center gap-3 w-full px-3 py-3 rounded-lg transition-colors ${
                        selectedModel === model.id
                          ? "bg-secondary"
                          : "hover:bg-secondary/50"
                      }`}
                    >
                      <button
                        type="button"
                        onClick={() => {
                          onModelSelect(model.id)
                          setModelDropdownOpen(false)
                        }}
                        className="flex items-center gap-3 flex-1"
                      >
                        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-sm font-bold text-white">
                          A
                        </div>
                        <div className="flex-1 text-left">
                          <p className="text-sm font-medium text-foreground">
                            {model.name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {model.provider}
                          </p>
                        </div>
                        {/* {selectedModel === model.id && (
                          <CheckIcon className="w-5 h-5 text-emerald-400" />
                        )} */}
                      </button>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          onEditConfig(model)
                          setModelDropdownOpen(false)
                        }}
                        className="p-1.5 hover:bg-secondary rounded-lg transition-colors"
                        title="Edit configuration"
                      >
                        <EditIcon className="w-4 h-4 text-muted-foreground" />
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => {
                      onManageModels()
                      setModelDropdownOpen(false)
                    }}
                    className="flex items-center gap-3 w-full px-3 py-3 rounded-lg hover:bg-secondary/50 transition-colors mt-1"
                  >
                    <div className="w-8 h-8 bg-secondary rounded-lg flex items-center justify-center">
                      <SettingsIcon className="w-4 h-4 text-muted-foreground" />
                    </div>
                    <span className="text-sm text-foreground">Manage Models</span>
                  </button>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Model Name */}
        <span className="text-muted-foreground text-sm border-l border-border pl-4">
          {currentModel?.name || "claude-opus-4-5"}
        </span>
      </div>

      {/* Center - Agent selector */}
      <div className="relative">
        <button
          type="button"
          onClick={() => {
            setAgentDropdownOpen(!agentDropdownOpen)
            setModelDropdownOpen(false)
          }}
          className="flex items-center gap-2 px-4 py-2 bg-secondary rounded-full hover:bg-secondary/80 transition-colors"
        >
          <AgentryLogo className="w-4 h-4 text-foreground" />
          <span className="text-sm font-medium text-foreground">
            {currentAgent?.name || "Default Agent"}
          </span>
          {agentDropdownOpen ? (
            <ChevronUpIcon className="w-4 h-4" />
          ) : (
            <ChevronDownIcon className="w-4 h-4" />
          )}
        </button>

        {/* Agent Dropdown */}
        {agentDropdownOpen && (
          <>
            <div
              className="fixed inset-0 z-40"
              onClick={() => setAgentDropdownOpen(false)}
            />
            <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1 w-80 bg-popover border border-border rounded-xl shadow-xl z-50 overflow-hidden">
              <div className="p-2">
                {agents.map((agent) => (
                  <button
                    key={agent.id}
                    type="button"
                    onClick={() => {
                      onAgentSelect(agent.id)
                      setAgentDropdownOpen(false)
                    }}
                    onMouseEnter={() => setHoveredAgent(agent.id)}
                    onMouseLeave={() => setHoveredAgent(null)}
                    className={`flex items-start gap-3 w-full px-3 py-3 rounded-lg transition-colors ${
                      selectedAgent === agent.id
                        ? "bg-secondary"
                        : "hover:bg-secondary/50"
                    }`}
                  >
                    <div className="mt-0.5">{agent.icon}</div>
                    <div className="flex-1 text-left">
                      <p className="text-sm font-medium text-foreground">
                        {agent.name}
                      </p>
                      {(hoveredAgent === agent.id || selectedAgent === agent.id) && agent.description && (
                        <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                          {agent.description}
                        </p>
                      )}
                    </div>
                    {selectedAgent === agent.id && (
                      <CheckIcon className="w-5 h-5 text-emerald-400" />
                    )}
                  </button>
                ))}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Right side - Status & Actions */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          className="p-2 hover:bg-secondary rounded-lg transition-colors">
            {theme === "dark" ? (
              <Image src="/mcp.svg" onClick={onMCPClick} alt="MCP" width={20} height={20} />
            ) : (
              <Image src="/mcp-dark.svg" onClick={onMCPClick} alt="MCP" width={20} height={20} />
            )}
          <MCPConfigModal isOpen={mcpModalOpen} onClose={() => setMCPModalOpen(false)} />
        </button>
        <button
          type="button"
          onClick={toggleTheme}
          className="p-2 hover:bg-secondary rounded-lg transition-colors"
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
        >
          {theme === "dark" ? (
            <MoonIcon className="w-5 h-5 text-muted-foreground" />
          ) : (
            <SunIcon className="w-5 h-5 text-muted-foreground" />
          )}
        </button>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div className="w-2 h-2 rounded-full bg-emerald-500" />
          <span>Connected</span>
        </div>

        <button type="button" onClick={handleSignOut} className="p-2 hover:bg-secondary rounded-lg transition-colors">
          <LogoutIcon className="w-5 h-5 text-muted-foreground" />
        </button>
      </div>
    </header>
  )
}
