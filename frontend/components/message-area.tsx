"use client"

import { useEffect, useState } from "react"
import { CopyIcon, ChevronDownIcon } from "@/components/icons"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  codeBlocks?: CodeBlock[]
  tables?: TableData[]
  lists?: string[][]
}

interface CodeBlock {
  language: string
  code: string
}

interface TableData {
  headers: string[]
  rows: string[][]
}

interface MessageAreaProps {
  messages: Message[]
  isNewChat: boolean
}

export function MessageArea({ messages, isNewChat }: MessageAreaProps) {
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  const formatTime = (date: Date, timezone: string) => {
    return date.toLocaleTimeString("en-US", {
      timeZone: timezone,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    })
  }

  const formatDate = (date: Date) => {
    return date.toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
    })
  }

  // Determine greeting based on time
  const getGreeting = () => {
    const hour = currentTime.getHours()
    if (hour < 12) return "Good Morning"
    if (hour < 18) return "Good Afternoon"
    return "Good Evening"
  }

  if (isNewChat || messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        <h1 className="text-4xl font-semibold text-foreground mb-8">
          {getGreeting()}
        </h1>

        {/* Time Display */}
        <div className="flex items-center gap-6">
          <div className="bg-card/50 border border-border/50 rounded-2xl px-10 py-6 text-center">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
              India (IST)
            </p>
            <p className="text-5xl font-light text-foreground tracking-wide font-mono">
              {formatTime(currentTime, "Asia/Kolkata")}
            </p>
          </div>
          <div className="bg-card/50 border border-border/50 rounded-2xl px-10 py-6 text-center">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
              California (PST)
            </p>
            <p className="text-5xl font-light text-foreground tracking-wide font-mono">
              {formatTime(currentTime, "America/Los_Angeles")}
            </p>
          </div>
        </div>

        <p className="text-muted-foreground mt-6">{formatDate(currentTime)}</p>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {messages.map((message) => (
          <div key={message.id}>
            {message.role === "user" ? (
              <div className="flex justify-end">
                <div className="max-w-xl bg-secondary rounded-2xl px-5 py-3">
                  <p className="text-foreground">{message.content}</p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Text Content */}
                <div className="text-foreground leading-relaxed whitespace-pre-wrap">
                  {message.content}
                </div>

                {/* Lists */}
                {message.lists?.map((list, listIndex) => (
                  <ul key={`list-${listIndex}`} className="list-disc pl-6 space-y-2">
                    {list.map((item, itemIndex) => (
                      <li key={`item-${itemIndex}`} className="text-foreground">
                        {item}
                      </li>
                    ))}
                  </ul>
                ))}

                {/* Code Blocks */}
                {message.codeBlocks?.map((block, index) => (
                  <CodeBlockComponent key={`code-${index}`} {...block} />
                ))}

                {/* Tables */}
                {message.tables?.map((table, index) => (
                  <TableComponent key={`table-${index}`} {...table} />
                ))}

                {/* Copy/Delete actions */}
                <div className="flex items-center gap-2 mt-2">
                  <button
                    type="button"
                    onClick={() => navigator.clipboard.writeText(message.content)}
                    className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-secondary rounded transition-colors"
                  >
                    <CopyIcon className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-secondary rounded transition-colors"
                  >
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
                    </svg>
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Scroll to bottom button */}
        <div className="fixed bottom-32 right-8">
          <button
            type="button"
            onClick={(e) => {
              const container = e.currentTarget.closest(".overflow-y-auto")
              container?.scrollTo({ top: container.scrollHeight, behavior: "smooth" })
            }}
            className="p-3 bg-secondary hover:bg-secondary/80 rounded-full shadow-lg transition-colors"
          >
            <ChevronDownIcon className="w-5 h-5 text-foreground" />
          </button>
        </div>
      </div>
    </div>
  )
}

function CodeBlockComponent({ language, code }: CodeBlock) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Simple syntax highlighting
  const highlightCode = (code: string, lang: string) => {
    if (lang === "python") {
      return code
        .split("\n")
        .map((line, i) => {
          let highlighted = line
          // Keywords
          highlighted = highlighted.replace(
            /\b(import|from|as|def|class|return|if|else|elif|for|while|try|except|with|await|async|print|True|False|None)\b/g,
            '<span class="text-purple-400">$1</span>'
          )
          // Strings
          highlighted = highlighted.replace(
            /(["'])(.*?)\1/g,
            '<span class="text-emerald-400">$1$2$1</span>'
          )
          // Numbers
          highlighted = highlighted.replace(
            /\b(\d+\.?\d*)\b/g,
            '<span class="text-orange-400">$1</span>'
          )
          // Comments
          highlighted = highlighted.replace(
            /(#.*$)/g,
            '<span class="text-muted-foreground">$1</span>'
          )
          // Function calls
          highlighted = highlighted.replace(
            /(\w+)(\()/g,
            '<span class="text-yellow-400">$1</span>$2'
          )
          return highlighted
        })
        .join("\n")
    }
    return code
  }

  return (
    <div className="bg-card rounded-xl border border-border overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-muted/30 border-b border-border">
        <span className="text-sm text-muted-foreground">{language}</span>
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-2 px-3 py-1 text-sm text-muted-foreground hover:text-foreground bg-secondary/50 rounded transition-colors"
        >
          <CopyIcon className="w-4 h-4" />
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <div className="p-4 overflow-x-auto font-mono text-sm leading-relaxed">
        <pre
          // biome-ignore lint: dangerouslySetInnerHTML is needed for syntax highlighting
          dangerouslySetInnerHTML={{
            __html: highlightCode(code, language),
          }}
        />
      </div>
    </div>
  )
}

function TableComponent({ headers, rows }: TableData) {
  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full">
        <thead>
          <tr className="bg-muted/30">
            {headers.map((header, i) => (
              <th
                key={`header-${i}`}
                className="px-4 py-3 text-left text-sm font-medium text-amber-400 border-b border-border"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={`row-${rowIndex}`} className="border-b border-border last:border-0">
              {row.map((cell, cellIndex) => (
                <td
                  key={`cell-${rowIndex}-${cellIndex}`}
                  className="px-4 py-3 text-sm text-foreground"
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
