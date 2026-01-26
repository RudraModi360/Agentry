"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import {
  AgentryLogo,
  PenIcon,
  SearchIcon,
  ImageIcon,
  FolderIcon,
  MessageIcon,
  SidebarIcon,
  LogoutIcon,
} from "@/components/icons"

interface Chat {
  id: string
  title: string
  date: string
  turns: number
  active?: boolean
}

interface SidebarProps {
  chats: Chat[]
  activeChat: string | null
  onChatSelect: (id: string) => void
  onNewChat: () => void
  onSearchClick: () => void
  collapsed: boolean
  onToggleCollapse: () => void
}

export function Sidebar({
  chats,
  activeChat,
  onChatSelect,
  onNewChat,
  onSearchClick,
  collapsed,
  onToggleCollapse,
}: SidebarProps) {
  const router = useRouter()
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  const handleSignOut = () => {
    setUserMenuOpen(false)
    router.push("/login")
  }

  if (collapsed) {
    return (
      <aside className="w-16 h-screen bg-sidebar border-r border-sidebar-border flex flex-col">
        {/* Navigation Icons */}
        <nav className="flex-1 px-2 space-y-1 pt-3">
          <button
            type="button"
            onClick={onToggleCollapse}
            className="flex items-center justify-center w-full p-3 text-muted-foreground hover:bg-secondary hover:text-foreground rounded-lg transition-colors"
            title="Expand sidebar"
          >
            <SidebarIcon className="w-5 h-5" />
          </button>
          <button
            type="button"
            onClick={onNewChat}
            className="flex items-center justify-center w-full p-3 text-muted-foreground hover:bg-secondary hover:text-foreground rounded-lg transition-colors"
            title="New chat"
          >
            <PenIcon className="w-5 h-5" />
          </button>
          <button
            type="button"
            onClick={onSearchClick}
            className="flex items-center justify-center w-full p-3 text-muted-foreground hover:bg-secondary hover:text-foreground rounded-lg transition-colors"
            title="Search chats"
          >
            <SearchIcon className="w-5 h-5" />
          </button>
          <button
            type="button"
            className="flex items-center justify-center w-full p-3 text-muted-foreground hover:bg-secondary hover:text-foreground rounded-lg transition-colors"
            title="Images"
          >
            <ImageIcon className="w-5 h-5" />
          </button>
          <button
            type="button"
            className="flex items-center justify-center w-full p-3 text-muted-foreground hover:bg-secondary hover:text-foreground rounded-lg transition-colors"
            title="Projects"
          >
            <FolderIcon className="w-5 h-5" />
          </button>
        </nav>

        {/* User Profile */}
        <div className="relative p-2 border-t border-sidebar-border">
          <button
            type="button"
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="flex items-center justify-center w-full p-2 hover:bg-secondary rounded-lg transition-colors"
          >
            <div className="w-8 h-8 bg-secondary rounded-full flex items-center justify-center text-sm font-medium text-foreground">
              K
            </div>
          </button>

          {/* User Menu Popover */}
          {userMenuOpen && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setUserMenuOpen(false)}
              />
              <div className="absolute bottom-full left-2 mb-2 w-56 bg-popover border border-border rounded-xl shadow-xl z-50 overflow-hidden">
                <div className="p-4 border-b border-border">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-secondary rounded-full flex items-center justify-center text-sm font-medium text-foreground">
                      K
                    </div>
                    <div>
                      <p className="font-medium text-foreground">Ketul</p>
                      <p className="text-xs text-muted-foreground">ketul@example.com</p>
                    </div>
                  </div>
                </div>
                <div className="p-2">
                  <button
                    type="button"
                    onClick={handleSignOut}
                    className="flex items-center gap-3 w-full px-3 py-2 text-sm text-destructive hover:bg-secondary rounded-lg transition-colors"
                  >
                    <LogoutIcon className="w-4 h-4" />
                    Sign out
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </aside>
    )
  }

  return (
    <aside className="w-72 h-screen bg-sidebar border-r border-sidebar-border flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-4">
        <AgentryLogo className="w-6 h-6 text-foreground" />
        <div className="text-lg font-semibold text-foreground">
          Agentry
        </div>
        <button
          type="button"
          onClick={onToggleCollapse}
          className="p-2 hover:bg-secondary rounded-lg transition-colors"
          aria-label="Toggle sidebar"
        >
          <SidebarIcon className="w-5 h-5 text-muted-foreground" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="px-3 space-y-1">
        <button
          type="button"
          onClick={onNewChat}
          className="flex items-center gap-3 w-full px-3 py-2 text-muted-foreground hover:bg-secondary hover:text-foreground rounded-lg transition-colors"
        >
          <PenIcon className="w-5 h-5" />
          <span className="text-sm">New chat</span>
        </button>
        <button
          type="button"
          onClick={onSearchClick}
          className="flex items-center gap-3 w-full px-3 py-2 text-muted-foreground hover:bg-secondary hover:text-foreground rounded-lg transition-colors"
        >
          <SearchIcon className="w-5 h-5" />
          <span className="text-sm">Search chats</span>
        </button>
        <button
          type="button"
          className="flex items-center gap-3 w-full px-3 py-2 text-muted-foreground hover:bg-secondary hover:text-foreground rounded-lg transition-colors"
        >
          <ImageIcon className="w-5 h-5" />
          <span className="text-sm">Images</span>
          <span className="ml-auto px-2 py-0.5 text-xs bg-emerald-500/20 text-emerald-400 rounded">
            NEW
          </span>
        </button>
        <button
          type="button"
          className="flex items-center gap-3 w-full px-3 py-2 text-muted-foreground hover:bg-secondary hover:text-foreground rounded-lg transition-colors"
        >
          <FolderIcon className="w-5 h-5" />
          <span className="text-sm">Projects</span>
        </button>
      </nav>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto mt-6">
        <div className="px-4 mb-2">
          <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Your Chats
          </h3>
        </div>
        <div className="px-2 space-y-0.5">
          {chats.map((chat) => (
            <button
              key={chat.id}
              type="button"
              onClick={() => onChatSelect(chat.id)}
              className={`group flex items-start gap-3 w-full px-3 py-2.5 rounded-lg transition-colors text-left ${
                activeChat === chat.id
                  ? "bg-secondary"
                  : "hover:bg-secondary/50"
              }`}
            >
              <MessageIcon
                className={`w-4 h-4 mt-0.5 flex-shrink-0 ${
                  activeChat === chat.id ? "text-foreground" : "text-muted-foreground"
                }`}
              />
              <div className="flex-1 min-w-0">
                <p
                  className={`text-sm truncate ${
                    activeChat === chat.id ? "text-foreground" : "text-foreground"
                  }`}
                >
                  {chat.title}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {chat.date} · {chat.turns} turns
                </p>
              </div>
              {activeChat === chat.id && (
                <button
                  type="button"
                  onClick={() => onChatSelect(chat.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-secondary rounded transition-opacity"
                >
                  <span className="text-muted-foreground">:</span>
                </button>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* User Profile */}
      <div className="relative p-3 border-t border-sidebar-border">
        <button
          type="button"
          onClick={() => setUserMenuOpen(!userMenuOpen)}
          className="flex items-center gap-3 w-full px-3 py-2 hover:bg-secondary rounded-lg transition-colors"
        >
          <div className="w-8 h-8 bg-secondary rounded-full flex items-center justify-center text-sm font-medium text-foreground">
            K
          </div>
          <span className="text-sm text-foreground">Ketul</span>
        </button>

        {/* User Menu Popover */}
        {userMenuOpen && (
          <>
            <div
              className="fixed inset-0 z-40"
              onClick={() => setUserMenuOpen(false)}
            />
            <div className="absolute bottom-full left-3 mb-2 w-64 bg-popover border border-border rounded-xl shadow-xl z-50 overflow-hidden">
              <div className="p-4 border-b border-border">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-secondary rounded-full flex items-center justify-center text-sm font-medium text-foreground">
                    K
                  </div>
                  <div>
                    <p className="font-medium text-foreground">Ketul</p>
                    <p className="text-xs text-muted-foreground">ketul@example.com</p>
                  </div>
                </div>
              </div>
              <div className="p-2">
                <button
                  type="button"
                  onClick={handleSignOut}
                  className="flex items-center gap-3 w-full px-3 py-2 text-sm text-destructive hover:bg-secondary rounded-lg transition-colors"
                >
                  <LogoutIcon className="w-4 h-4" />
                  Sign out
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </aside>
  )
}
