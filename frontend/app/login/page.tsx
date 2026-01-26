"use client"

import React from "react"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useTheme } from "next-themes"
import { AgentryLogo, ArrowLeftIcon, MoonIcon, SunIcon, UsersIcon } from "@/components/icons"

export default function LoginPage() {
  const router = useRouter()
  const { theme, setTheme } = useTheme()
  const [mode, setMode] = useState<"signin" | "signup">("signin")

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark")
  }
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Mock authentication - redirect to setup
    router.push("/setup")
  }

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Animated gradient background */}
      <div className="fixed inset-0">
        <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-purple-950/30" />
        <div className="absolute top-1/4 -left-32 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl" />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-4">
        <Link
          href="/"
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeftIcon className="w-4 h-4" />
          Back to Home
        </Link>
        <button
          type="button"
          className="p-2 rounded-full bg-secondary hover:bg-secondary/80 transition-colors"
        >
          <MoonIcon className="w-5 h-5 text-foreground" />
        </button>
      </nav>

      {/* Login Card */}
      <main className="relative z-10 flex items-center justify-center min-h-[calc(100vh-80px)] px-6">
        <div className="w-full max-w-md">
          {/* Glassmorphism card */}
          <div className="bg-card/80 backdrop-blur-xl rounded-2xl border border-border/50 p-8 shadow-2xl">
            {/* Logo */}
            <div className="flex items-center justify-center gap-3 mb-8">
              <AgentryLogo className="w-8 h-8 text-foreground" />
              <span className="text-2xl font-semibold text-foreground">Agentry</span>
            </div>

            {/* Toggle */}
            <div className="flex bg-muted rounded-lg p-1 mb-8">
              <button
                type="button"
                onClick={() => setMode("signin")}
                className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${mode === "signin"
                    ? "bg-foreground text-background transition-all duration-300 ease-in-out"
                    : "text-muted-foreground hover:text-foreground transition-all duration-300 ease-in-out"
                  }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => setMode("signup")}
                className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${mode === "signup"
                    ? "bg-foreground text-background transition-all duration-300 ease-in-out"
                    : "text-muted-foreground hover:text-foreground transition-all duration-300 ease-in-out"
                  }`}
              >
                Create Account
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label
                  htmlFor="username"
                  className="block text-sm font-medium text-foreground mb-2"
                >
                  Username
                </label>
                <input
                  type="text"
                  id="username"
                  value={formData.username}
                  onChange={(e) =>
                    setFormData({ ...formData, username: e.target.value })
                  }
                  placeholder={mode === "signup" ? "Choose a username" : "Enter your username"}
                  className="w-full px-4 py-3 bg-muted border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/50 transition-all"
                />
              </div>

              {mode === "signup" && (
                <div>
                  <label
                    htmlFor="email"
                    className="block text-sm font-medium text-foreground mb-2"
                  >
                    Email (Optional)
                  </label>
                  <input
                    type="email"
                    id="email"
                    value={formData.email}
                    onChange={(e) =>
                      setFormData({ ...formData, email: e.target.value })
                    }
                    placeholder="Enter your email for recovery"
                    className="w-full px-4 py-3 bg-muted border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/50 transition-all"
                  />
                </div>
              )}

              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-foreground mb-2"
                >
                  Password
                </label>
                <input
                  type="password"
                  id="password"
                  value={formData.password}
                  onChange={(e) =>
                    setFormData({ ...formData, password: e.target.value })
                  }
                  placeholder={mode === "signup" ? "Create a password" : "Enter your password"}
                  className="w-full px-4 py-3 bg-muted border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/50 transition-all"
                />
              </div>

              {mode === "signup" && (
                <div>
                  <label
                    htmlFor="confirmPassword"
                    className="block text-sm font-medium text-foreground mb-2"
                  >
                    Confirm Password
                  </label>
                  <input
                    type="password"
                    id="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={(e) =>
                      setFormData({ ...formData, confirmPassword: e.target.value })
                    }
                    placeholder="Confirm your password"
                    className="w-full px-4 py-3 bg-muted border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/50 transition-all"
                  />
                </div>
              )}

              <button
                type="submit"
                className="w-full flex items-center justify-center gap-2 py-3 bg-foreground text-background font-medium rounded-lg hover:bg-foreground/90 transition-colors mt-6"
              >
                <UsersIcon className="w-5 h-5" />
                {mode === "signin" ? "Sign In" : "Create Account"}
              </button>
            </form>

            {/* Divider */}
            {/* <div className="flex items-center gap-4 my-6">
              <div className="flex-1 h-px bg-border" />
            </div> */}

            {/* Back to home */}
            {/* <p className="text-center text-muted-foreground text-sm">
              <Link href="/" className="hover:text-foreground transition-colors">
                ← Back to Home
              </Link>
            </p> */}
          </div>
        </div>
      </main>
    </div>
  )
}
