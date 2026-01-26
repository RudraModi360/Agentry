"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Sidebar } from "@/components/sidebar"
import { TopBar } from "@/components/top-bar"
import { MessageArea } from "@/components/message-area"
import { MessageInput } from "@/components/message-input"
import { SearchModal, MCPConfigModal, EditConfigModal, ManageModelsModal } from "@/components/modals"
import { AgentryLogo, CodeBracketIcon, LightbulbIcon } from "@/components/icons"

// Mock data
const mockChats = [
  { id: "1", title: "New Chat", date: "Jan 25", turns: 1 },
  {
    id: "2",
    title: "Understanding Linear Regression...",
    date: "Jan 25, 4:25 PM",
    turns: 3,
  },
  { id: "3", title: "Carbon Cycle Explained", date: "Jan 25", turns: 1 },
]

const mockModels = [
  { id: "claude", name: "claude-opus-4-5", provider: "Azure OpenAI", active: true },
  { id: "gpt", name: "gpt-oss:20b-cloud", provider: "Ollama" },
]

const mockAgents = [
  {
    id: "default",
    name: "Default Agent",
    description: "All tools + MCP servers for complex workflows",
    icon: <AgentryLogo className="w-5 h-5 text-foreground" />,
  },
  {
    id: "copilot",
    name: "Copilot Agent",
    description: "Coding focused with file & execution tools",
    icon: <CodeBracketIcon className="w-5 h-5 text-foreground" />,
  },
  {
    id: "smart",
    name: "Smart Agent",
    description: "Enhanced reasoning & project context",
    icon: <LightbulbIcon className="w-5 h-5 text-foreground" />,
  },
]

type Message = {
  id: string
  role: "user" | "assistant"
  content: string
  lists?: string[][]
  tables?: {
    headers: string[]
    rows: string[][]
  }[]
  codeBlocks?: {
    language: string
    code: string
  }[]
}

// Sample messages for the Linear Regression chat
const sampleMessages: Message[] = [
  {
    id: "m1",
    role: "user" as const,
    content: "linear regression",
  },
  {
    id: "m2",
    role: "assistant" as const,
    content: "What would you like to know about linear regression?",
    lists: [
      [
        "A brief explanation of the concept and when it's used.",
        "How to fit a simple linear regression model in a specific language (Python, R, MATLAB, etc.).",
        "Guidance on diagnosing assumptions or interpreting results.",
        "Example code and data for a hands-on tutorial.",
      ],
    ],
  },
  {
    id: "m3",
    role: "user" as const,
    content: "explain me this",
  },
  {
    id: "m4",
    role: "assistant" as const,
    content: "Linear Regression – Quick Primer\n\nGoal\nPredict a numeric outcome (y) from one or more explanatory variables (x_1, x_2, ..., x_p) by fitting a straight-line (in 1-D) or hyperplane (in higher-D):",
    tables: [
      {
        headers: ["Assumption", "Why it matters", "Check / Diagnose"],
        rows: [
          ["Linearity", "Relationship between (x) and (y) is linear.", "Residual vs. fitted plots"],
          ["Independence", "Errors independent of each other.", "Durbin–Watson test; check study design"],
          ["Homoscedasticity", "Constant variance.", "Residual vs. fitted (look for funnel)."],
          ["Normality", "Errors normally distributed.", "QQ-plot, Shapiro-Wilk test, residual histogram."],
          ["No perfect multicollinearity", "Predictors not linear combos of each other.", "Variance Inflation Factor (VIF) < 5-10."],
        ],
      },
    ],
    codeBlocks: [
      {
        language: "python",
        code: `import numpy as np
import pandas as pd
import statsmodels.api as sm

# Simulated data
np.random.seed(42)
n = 100
X = np.column_stack([np.random.normal(size=n), np.random.uniform(0, 10, size=n)])
y = 3 + 1.5 * X[:,0] - 0.7 * X[:,1] + np.random.normal(scale=1.0, size=n)

# Build model
X = sm.add_constant(X)        # adds intercept
model = sm.OLS(y, X).fit()

print(model.summary())`,
      },
    ],
  },
]

export default function ChatPage() {
  const router = useRouter()
  const [activeChat, setActiveChat] = useState<string | null>("2")
  const [selectedModel, setSelectedModel] = useState("claude")
  const [selectedAgent, setSelectedAgent] = useState("default")
  const [searchModalOpen, setSearchModalOpen] = useState(false)
  const [mcpModalOpen, setMCPModalOpen] = useState(false)
  const [editConfigOpen, setEditConfigOpen] = useState(false)
  const [manageModelsOpen, setManageModelsOpen] = useState(false)
  const [editingModel, setEditingModel] = useState<typeof mockModels[0] | undefined>()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [messages, setMessages] = useState<Message[]>(sampleMessages)

  const handleNewChat = () => {
    setActiveChat(null)
    setMessages([])
  }

  const handleChatSelect = (id: string) => {
    setActiveChat(id)
    // Load messages for selected chat
    if (id === "2") {
      setMessages(sampleMessages)
    } else {
      setMessages([])
    }
  }

  const handleSendMessage = (content: string) => {
    const newMessage = {
      id: `m${Date.now()}`,
      role: "user" as const,
      content,
    }
    setMessages([...messages, newMessage])

    // Simulate AI response
    setTimeout(() => {
      const aiResponse = {
        id: `m${Date.now() + 1}`,
        role: "assistant" as const,
        content: "I understand you're asking about that topic. Let me provide some insights...",
      }
      setMessages((prev) => [...prev, aiResponse])
    }, 1000)
  }

  const handleEditConfig = (model: typeof mockModels[0]) => {
    setEditingModel(model)
    setEditConfigOpen(true)
  }

  const handleManageModels = () => {
    setManageModelsOpen(true)
  }

  const handleAddNewModel = () => {
    setManageModelsOpen(false)
    router.push("/setup")
  }

  const handleEditFromManage = (model: typeof mockModels[0]) => {
    setManageModelsOpen(false)
    setEditingModel(model)
    setEditConfigOpen(true)
  }

  const handleBackToManage = () => {
    setEditConfigOpen(false)
    setManageModelsOpen(true)
  }

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        chats={mockChats}
        activeChat={activeChat}
        onChatSelect={handleChatSelect}
        onNewChat={handleNewChat}
        onSearchClick={() => setSearchModalOpen(true)}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Bar */}
        <TopBar
          models={mockModels}
          agents={mockAgents}
          selectedModel={selectedModel}
          selectedAgent={selectedAgent}
          onModelSelect={setSelectedModel}
          onAgentSelect={setSelectedAgent}
          onManageModels={handleManageModels}
          onEditConfig={handleEditConfig}
        />

        {/* Message Area */}
        <MessageArea
          messages={messages}
          isNewChat={activeChat === null || messages.length === 0}
        />

        {/* Message Input */}
        <MessageInput
          onSend={handleSendMessage}
          onToolsClick={() => setMCPModalOpen(true)}
        />
      </div>

      {/* Modals */}
      <SearchModal
        isOpen={searchModalOpen}
        onClose={() => setSearchModalOpen(false)}
        chats={mockChats}
        onChatSelect={handleChatSelect}
      />
      <MCPConfigModal isOpen={mcpModalOpen} onClose={() => setMCPModalOpen(false)} />
      <ManageModelsModal
        isOpen={manageModelsOpen}
        onClose={() => setManageModelsOpen(false)}
        models={mockModels}
        currentModelId={selectedModel}
        onModelSelect={(id) => {
          setSelectedModel(id)
          setManageModelsOpen(false)
        }}
        onEditModel={handleEditFromManage}
        onAddNewModel={handleAddNewModel}
      />
      <EditConfigModal
        isOpen={editConfigOpen}
        onClose={() => {
          setEditConfigOpen(false)
          setEditingModel(undefined)
        }}
        model={editingModel}
        onBack={manageModelsOpen ? undefined : handleBackToManage}
      />
    </div>
  )
}
