"use client"

import { useState } from "react"
import { useTheme } from "next-themes"
import { useRouter } from "next/navigation"
import Image from "next/image"
import {
  SearchIcon,
  MessageIcon,
  AgentryLogo,
  RefreshIcon,
  ArrowLeftIcon,
  CheckIcon,
  EyeIcon,
  EyeOffIcon,
  PlusIcon,
  EditIcon,
  TrashIcon,
} from "@/components/icons"

interface Chat {
  id: string
  title: string
  date: string
  turns: number
}

interface SearchModalProps {
  isOpen: boolean
  onClose: () => void
  chats: Chat[]
  onChatSelect: (id: string) => void
}

export function SearchModal({ isOpen, onClose, chats, onChatSelect }: SearchModalProps) {
  const [searchQuery, setSearchQuery] = useState("")

  if (!isOpen) return null

  const filteredChats = chats.filter((chat) =>
    chat.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-background/80 backdrop-blur-sm"
        onClick={onClose}
        onKeyDown={(e) => e.key === "Escape" && onClose()}
        aria-label="Close modal"
      />

      {/* Modal */}
      <div className="relative w-full max-w-2xl bg-popover border border-border rounded-xl shadow-2xl overflow-hidden">
        {/* Search Input */}
        <div className="flex items-center gap-3 px-4 py-4 border-b border-border">
          <SearchIcon className="w-5 h-5 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search your chats..."
            className="flex-1 bg-transparent text-foreground placeholder-muted-foreground focus:outline-none"
            autoFocus
          />
        </div>

        {/* Results */}
        <div className="max-h-80 overflow-y-auto p-2">
          {filteredChats.map((chat) => (
            <button
              key={chat.id}
              type="button"
              onClick={() => {
                onChatSelect(chat.id)
                onClose()
              }}
              className="flex items-center gap-3 w-full px-4 py-3 rounded-lg hover:bg-secondary transition-colors text-left"
            >
              <MessageIcon className="w-5 h-5 text-muted-foreground" />
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">{chat.title}</p>
                <p className="text-xs text-muted-foreground">
                  {chat.date} · {chat.turns} turns
                </p>
              </div>
            </button>
          ))}
          {filteredChats.length === 0 && (
            <p className="text-center text-muted-foreground py-8">No chats found</p>
          )}
        </div>
      </div>
    </div>
  )
}

interface MCPConfigModalProps {
  isOpen: boolean
  onClose: () => void
}

export function MCPConfigModal({ isOpen, onClose }: MCPConfigModalProps) {
  const [config, setConfig] = useState('{\n  "mcpServers": {}\n}')
  const { resolvedTheme } = useTheme()
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-background/80 backdrop-blur-sm"
        onClick={onClose}
        onKeyDown={(e) => e.key === "Escape" && onClose()}
        aria-label="Close modal"
      />

      {/* Modal */}
      <div className="relative w-full max-w-2xl bg-popover border border-border rounded-xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-3">
            {/* <MCPIcon className="w-5 h-5 text-muted-foreground" /> */}
            {resolvedTheme === "light" ? (
              <Image src="mcp-dark.svg" alt="MCP" width={20} height={20} />
            ) : (
              <Image src="mcp.svg" alt="MCP" width={20} height={20} />
            )}
            <h2 className="text-lg font-semibold text-foreground">
              MCP Server Configuration
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 text-muted-foreground hover:text-foreground transition-colors"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* JSON Editor */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <svg className="w-4 h-4 text-muted-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
              <span className="text-sm text-foreground">
                MCP Servers Configuration (JSON)
              </span>
            </div>
            <textarea
              value={config}
              onChange={(e) => setConfig(e.target.value)}
              className="w-full h-40 px-4 py-3 bg-card border border-border rounded-lg font-mono text-sm text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/50 resize-none"
            />
          </div>

          {/* Server Status */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <MessageIcon className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium text-foreground">
                  Server Status
                </span>
              </div>
              <button
                type="button"
                className="flex items-center gap-2 px-3 py-1.5 text-sm text-muted-foreground bg-secondary rounded-lg hover:bg-secondary/80 transition-colors"
              >
                <RefreshIcon className="w-4 h-4" />
                Refresh Status
              </button>
            </div>
            <div className="bg-card/50 border border-border rounded-lg p-6 text-center">
              <p className="text-muted-foreground">No MCP servers configured</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end px-6 py-4 border-t border-border">
          <button
            type="button"
            onClick={onClose}
            className="px-6 py-2.5 bg-accent text-accent-foreground font-medium rounded-lg hover:bg-accent/90 transition-colors"
          >
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  )
}

interface Model {
  id: string
  name: string
  provider: string
  active?: boolean
}

interface ManageModelsModalProps {
  isOpen: boolean
  onClose: () => void
  models: Model[]
  currentModelId: string
  onModelSelect: (id: string) => void
  onEditModel: (model: Model) => void
  onAddNewModel: () => void
}

export function ManageModelsModal({
  isOpen,
  onClose,
  models,
  currentModelId,
  onModelSelect,
  onEditModel,
  onAddNewModel,
}: ManageModelsModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-background/80 backdrop-blur-sm"
        onClick={onClose}
        onKeyDown={(e) => e.key === "Escape" && onClose()}
        aria-label="Close modal"
      />

      {/* Modal */}
      <div className="relative w-full max-w-lg bg-popover border border-border rounded-xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-3">
            <AgentryLogo className="w-5 h-5 text-amber-400" />
            <h2 className="text-lg font-semibold text-foreground">
              Manage Models
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 text-muted-foreground hover:text-foreground transition-colors"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <p className="text-sm text-muted-foreground">
            Previously used models. Click to switch, or use the buttons to edit/remove.
          </p>

          {/* Models List */}
          <div className="space-y-2">
            {models.map((model) => (
              <div
                key={model.id}
                className={`flex items-center gap-3 p-3 rounded-lg border transition-colors cursor-pointer ${currentModelId === model.id
                  ? "bg-secondary border-accent"
                  : "bg-card border-border hover:border-border/80"
                  }`}
                onClick={() => onModelSelect(model.id)}
              >
                <div className="w-10 h-10 bg-secondary rounded-lg flex items-center justify-center">
                  <svg viewBox="0 0 24 24" className="w-6 h-6 text-muted-foreground" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="font-medium text-foreground">{model.name}</p>
                  <p className="text-xs text-muted-foreground">{model.provider}</p>
                </div>
                {currentModelId === model.id && (
                  <span className="px-2 py-1 text-xs font-medium bg-accent text-accent-foreground rounded">
                    Current
                  </span>
                )}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    onEditModel(model)
                  }}
                  className="p-1.5 hover:bg-secondary rounded-lg transition-colors"
                  title="Edit model"
                >
                  <EditIcon className="w-4 h-4 text-muted-foreground" />
                </button>
                <button
                  type="button"
                  onClick={(e) => e.stopPropagation()}
                  className="p-1.5 hover:bg-secondary rounded-lg transition-colors"
                  title="Delete model"
                >
                  <TrashIcon className="w-4 h-4 text-muted-foreground" />
                </button>
              </div>
            ))}
          </div>

          {/* Add New Model Button */}
          <button
            type="button"
            onClick={onAddNewModel}
            className="flex items-center justify-center gap-2 w-full px-4 py-3 bg-accent text-accent-foreground font-medium rounded-lg hover:bg-accent/90 transition-colors"
          >
            <PlusIcon className="w-5 h-5" />
            Add New Model
          </button>
        </div>
      </div>
    </div>
  )
}

interface EditConfigModalProps {
  isOpen: boolean
  onClose: () => void
  model?: {
    id?: string
    name: string
    provider: string
  }
  onBack?: () => void
}

export function EditConfigModal({ isOpen, onClose, model, onBack }: EditConfigModalProps) {
  const [apiKey, setApiKey] = useState("sk-ant-1234567890abcdef1234567890abcdef")
  const [endpoint, setEndpoint] = useState(
    "https://anydoctransform-resource.services.ai.azure.com/anthropic/v1/me"
  )
  const [modelName, setModelName] = useState(model?.name || "claude-opus-4-5")
  const [showKey, setShowKey] = useState(false)

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-background/80 backdrop-blur-sm"
        onClick={onClose}
        onKeyDown={(e) => e.key === "Escape" && onClose()}
        aria-label="Close modal"
      />

      {/* Modal */}
      <div className="relative w-full max-w-lg bg-popover border border-border rounded-xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-3">
            <AgentryLogo className="w-5 h-5 text-amber-400" />
            <h2 className="text-lg font-semibold text-foreground">
              Edit Configuration
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 text-muted-foreground hover:text-foreground transition-colors"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5">
          {/* Back to list */}
          {onBack && (
            <button
              type="button"
              onClick={onBack}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-muted-foreground bg-secondary rounded-lg hover:bg-secondary/80 transition-colors"
            >
              <ArrowLeftIcon className="w-4 h-4" />
              Back to list
            </button>
          )}

          {/* Model Info */}
          <div className="bg-card border border-border rounded-lg p-4 flex items-center gap-4">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center text-sm font-bold text-white">
              A
            </div>
            <div>
              <p className="font-medium text-foreground">
                {model?.name || "claude-opus-4-5"}
              </p>
              <p className="text-sm text-muted-foreground">
                {model?.provider || "Azure OpenAI"}
              </p>
            </div>
          </div>

          {/* API Key */}
          <div>
            <label htmlFor="api-key" className="block text-sm font-medium text-foreground mb-2">
              API Key
            </label>
            <div className="relative">
              <input
                type={showKey ? "text" : "password"}
                id="api-key"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full px-4 py-3 pr-12 bg-card border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/50"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showKey ? (
                  <EyeOffIcon className="w-5 h-5" />
                ) : (
                  <EyeIcon className="w-5 h-5" />
                )}
              </button>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Leave blank to keep your existing key
            </p>
          </div>

          {/* Endpoint URL */}
          <div>
            <label htmlFor="endpoint" className="block text-sm font-medium text-foreground mb-2">
              Endpoint URL
            </label>
            <input
              type="text"
              id="endpoint"
              value={endpoint}
              onChange={(e) => setEndpoint(e.target.value)}
              className="w-full px-4 py-3 bg-card border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/50"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Your Azure resource endpoint URL
            </p>
          </div>

          {/* Model Name */}
          <div>
            <label htmlFor="model-name" className="block text-sm font-medium text-foreground mb-2">
              Model / Deployment Name
            </label>
            <input
              type="text"
              id="model-name"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              className="w-full px-4 py-3 bg-card border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/50"
            />
            <p className="text-xs text-muted-foreground mt-1">
              The model or deployment name to use
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 px-6 py-4 border-t border-border">
          <button
            type="button"
            onClick={onClose}
            className="px-6 py-2.5 text-foreground bg-secondary font-medium rounded-lg hover:bg-secondary/80 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onClose}
            className="flex items-center gap-2 px-6 py-2.5 bg-accent text-accent-foreground font-medium rounded-lg hover:bg-accent/90 transition-colors"
          >
            <CheckIcon className="w-4 h-4" />
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  )
}
