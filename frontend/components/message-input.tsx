"use client"

import React from "react"

import { useState } from "react"
import { PlusIcon, SendIcon, ImageIcon } from "@/components/icons"

interface MessageInputProps {
  onSend: (message: string) => void
  onToolsClick: () => void
}

export function MessageInput({ onSend, onToolsClick }: MessageInputProps) {
  const [message, setMessage] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim()) {
      onSend(message.trim())
      setMessage("")
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const selectFile = () => {
    const input = document.createElement("input")
    input.type = "file"
    input.accept = "image/*"
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (file) {
        const reader = new FileReader()
        reader.onload = (e) => {
          const result = e.target?.result as string
          onSend(result)
        }
        // reader.readAsDataURL(file)
      }
    }
    input.click()
  }

  return (
    <div className="p-6">
      <form
        onSubmit={handleSubmit}
        className="max-w-4xl mx-auto flex items-center gap-3"
      >
        {/* Plus/Tools Button */}
        <button
          type="button"
          onClick={onToolsClick}
          className="p-2 text-muted-foreground hover:text-foreground hover:bg-secondary rounded-lg transition-colors"
        >
          <PlusIcon className="w-5 h-5" />
        </button>

        {/* Input Container */}
        <div className="flex-1 relative">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message Agentry..."
            className="w-full px-4 py-3 bg-card border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/50 transition-all"
          />
          {/* Image attachment */}
          <button
            type="button"
            onClick={() => selectFile()}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-muted-foreground hover:text-foreground rounded-lg transition-colors"
          >
            <ImageIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Send Button */}
        <button
          type="submit"
          disabled={!message.trim()}
          className="p-3 bg-foreground text-background rounded-xl hover:bg-foreground/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          <SendIcon className="w-5 h-5" />
        </button>
      </form>
    </div>
  )
}
