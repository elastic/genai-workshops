"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Settings, CheckCircle, AlertCircle, Info } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"

interface SettingsDialogProps {
  config: {
    url: string
    apiKey: string
  }
  onConfigChange: (config: { url: string; apiKey: string }) => void
}

export function SettingsDialog({ config, onConfigChange }: SettingsDialogProps) {
  const [open, setOpen] = useState(false)
  const [formValues, setFormValues] = useState(config)
  const [isValidating, setIsValidating] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<"none" | "connected" | "error">("none")
  const [errorMessage, setErrorMessage] = useState("")
  const [showHelp, setShowHelp] = useState(false)

  const validateElasticsearch = async (url: string, apiKey: string) => {
    try {
      const response = await fetch("/api/validate-elasticsearch", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url, apiKey }),
      })

      const data = await response.json()

      if (!response.ok || !data.success) {
        throw new Error(data.error || "Failed to validate Elasticsearch connection")
      }

      return { success: true, message: data.message }
    } catch (error) {
      console.error("Validation error:", error)

      // Provide more helpful error messages based on common issues
      let errorMsg = error instanceof Error ? error.message : "Failed to validate connection"

      if (errorMsg.includes("410")) {
        errorMsg = "The Elasticsearch endpoint is not available (410 Gone). This may be due to server configuration."
        setShowHelp(true)
      } else if (errorMsg.includes("401") || errorMsg.includes("403")) {
        errorMsg = "Invalid API key or insufficient permissions."
      } else if (errorMsg.includes("ECONNREFUSED") || errorMsg.includes("Failed to fetch")) {
        errorMsg =
          "Could not connect to the Elasticsearch server. Please check the URL and ensure the server is accessible."
      }

      return { success: false, error: errorMsg }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Basic validation
    if (!formValues.url || !formValues.apiKey) {
      setConnectionStatus("error")
      setErrorMessage("URL and API key are required")
      return
    }

    // Validate URL format
    try {
      new URL(formValues.url)
    } catch (error) {
      setConnectionStatus("error")
      setErrorMessage("Please enter a valid URL")
      return
    }

    // Ensure URL doesn't end with a slash
    const cleanUrl = formValues.url.endsWith("/") ? formValues.url.slice(0, -1) : formValues.url

    setIsValidating(true)
    setErrorMessage("")
    setShowHelp(false)

    const result = await validateElasticsearch(cleanUrl, formValues.apiKey)

    if (result.success) {
      setConnectionStatus("connected")
      onConfigChange({ ...formValues, url: cleanUrl })

      // Close dialog after a short delay to show success message
      setTimeout(() => {
        setOpen(false)
      }, 1000)
    } else {
      setConnectionStatus("error")
      setErrorMessage(result.error || "Connection failed")
    }

    setIsValidating(false)
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(newOpen) => {
        // Reset error state when opening dialog
        if (newOpen && !open) {
          setErrorMessage("")
          setShowHelp(false)
        }
        setOpen(newOpen)
      }}
    >
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="icon"
          className={
            connectionStatus === "connected"
              ? "border-green-500 text-green-500"
              : connectionStatus === "error"
                ? "border-red-500 text-red-500"
                : ""
          }
        >
          <Settings className="h-5 w-5" />
          <span className="sr-only">Settings</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px] z-[9999] bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle className="text-gray-900 dark:text-white">Elasticsearch Configuration</DialogTitle>
            <DialogDescription className="text-gray-500 dark:text-gray-400">
              Enter your Elasticsearch cluster URL and API key to connect to your data.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="elastic_url" className="text-right text-gray-700 dark:text-gray-300">
                Elasticsearch URL
              </Label>
              <Input
                id="elastic_url"
                value={formValues.url}
                onChange={(e) => setFormValues({ ...formValues, url: e.target.value })}
                className="col-span-3 bg-white dark:bg-gray-700 text-gray-900 dark:text-white border-gray-200 dark:border-gray-600"
                placeholder="https://your-cluster.es.amazonaws.com"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="elastic_api" className="text-right text-gray-700 dark:text-gray-300">
                API Key
              </Label>
              <Input
                id="elastic_api"
                type="password"
                value={formValues.apiKey}
                onChange={(e) => setFormValues({ ...formValues, apiKey: e.target.value })}
                className="col-span-3 bg-white dark:bg-gray-700 text-gray-900 dark:text-white border-gray-200 dark:border-gray-600"
                placeholder="Your Elasticsearch API key"
              />
            </div>

            {errorMessage && (
              <div className="col-span-4">
                <Alert
                  variant="destructive"
                  className="bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-300 border-red-200 dark:border-red-800"
                >
                  <AlertCircle className="h-4 w-4 mr-2" />
                  <AlertDescription>{errorMessage}</AlertDescription>
                </Alert>
              </div>
            )}

            {showHelp && (
              <div className="col-span-4">
                <Alert className="bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300 border-blue-200 dark:border-blue-800">
                  <Info className="h-4 w-4 mr-2" />
                  <AlertDescription>
                    <p className="text-sm">
                      Some Elasticsearch endpoints may be restricted. Try these troubleshooting steps:
                    </p>
                    <ul className="list-disc pl-5 text-sm mt-2">
                      <li>Ensure your API key has sufficient permissions</li>
                      <li>Check if your Elasticsearch server allows external connections</li>
                      <li>Try using a different endpoint in your URL (e.g., remove any path components)</li>
                    </ul>
                  </AlertDescription>
                </Alert>
              </div>
            )}
          </div>
          <DialogFooter className="flex items-center justify-between">
            <div>
              {connectionStatus === "connected" && (
                <span className="text-sm text-green-500 flex items-center">
                  <CheckCircle className="h-4 w-4 mr-1" />
                  Connected
                </span>
              )}
            </div>
            <Button type="submit" disabled={isValidating}>
              {isValidating ? (
                <>
                  <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"></div>
                  Validating...
                </>
              ) : (
                "Save changes"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
