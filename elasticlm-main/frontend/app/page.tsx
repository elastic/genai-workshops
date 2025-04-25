'use client'

import { useState, useRef, useEffect } from 'react'
import { nanoid } from 'nanoid'
import { Moon, Sun, Plus, Send, ChevronLeft, ChevronRight, RefreshCw, Loader2 } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogDescription,
  DialogFooter
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { FileUploadDialog } from "@/components/file-upload-dialog"
import { SourceItem } from "@/components/source-item"
import { ChatMessage } from "@/components/chat-message"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { LoadingIndicator } from "@/components/loading-indicator"
import { toast, ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import { useRouter } from 'next/navigation'

interface Source {
  id: string
  name: string
  checked: boolean
  uploadStatus: 'pending' | 'uploading' | 'success' | 'error'
  errorMessage?: string
}

interface Message {
  role: 'human' | 'assistant'
  content: string
}

export default function DocumentChat() {
  const [rightPanelOpen, setRightPanelOpen] = useState(false)
  const [isDarkMode, setIsDarkMode] = useState(true)
  const [enableCaching, setEnableCaching] = useState(false)
  const [similarityThreshold, setSimilarityThreshold] = useState(80)
  const [isConfirmDialogOpen, setIsConfirmDialogOpen] = useState(false)
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false)
  const [sources, setSources] = useState<Source[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [selectedLLM, setSelectedLLM] = useState('default-llm')
  const [isLoading, setIsLoading] = useState(false)
  const [chatId, setChatId] = useState<string | null>(null)
  const hasUploadedFiles = sources.some(source => source.checked)
  const chatContainerRef = useRef<HTMLDivElement>(null)
  const router = useRouter()

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || ''

  // Remove all userId and access_token logic

  useEffect(() => {
    // No userId logic needed, just clear state for a new session
    setSources([])
    setMessages([])
    setInputMessage('')
    setSelectedLLM('default-llm')
    setEnableCaching(false)
    setSimilarityThreshold(80)
    setChatId(null)
  }, [])

  // Remove fetchChatHistory, handleUserIdSubmit, handleNewSession, and all userId logic

  const handleFilesSelected = async (files: File[]) => {
    const newSources: Source[] = files.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      checked: false,
      uploadStatus: 'pending'
    }))
    setSources(prev => [...prev, ...newSources])
    setIsUploadDialogOpen(false)

    newSources.forEach(async (source) => {
      setSources(prev => prev.map(s => s.id === source.id ? { ...s, uploadStatus: 'uploading' } : s))
      const formData = new FormData()
      const file = files.find(f => f.name === source.name)
      if (!file) return
      formData.append('file', file)

      try {
        await fetch(`${API_BASE_URL}/upload/`, {
          method: 'POST',
          body: formData
        })
        // We do not care about the response, just start polling
      } catch (error) {
        // Swallow error, keep status as 'pending' and continue polling
      }
      // Always set to pending and poll, even if upload failed
      setSources(prev => prev.map(s => s.id === source.id ? { ...s, uploadStatus: 'pending' } : s))
      let summary = null
      let pollError = null
      for (let i = 0; i < 60; i++) {
        try {
          // Use filename as the key for polling
          const pollRes = await fetch(`${API_BASE_URL}/upload/status?filename=${encodeURIComponent(source.name)}`)
          if (pollRes.ok) {
            const pollData = await pollRes.json()
            if (pollData.status === 'done' && pollData.summary_message) {
              summary = pollData.summary_message
              break
            } else if (pollData.status === 'error') {
              pollError = pollData.detail || 'Processing failed.'
              break
            }
          }
        } catch (e) {
          pollError = e.message
          break
        }
        await new Promise(res => setTimeout(res, 2000))
      }
      if (summary) {
        setSources(prev => prev.map(s => s.id === source.id ? { ...s, uploadStatus: 'success', checked: true } : s))
        setMessages(prev => [
          ...prev,
          { role: 'assistant', content: `Summary for ${source.name}: ${summary}` }
        ])
        toast.success(`File "${source.name}" processed successfully.`)
      } else if (pollError) {
        setSources(prev => prev.map(s => s.id === source.id ? { ...s, uploadStatus: 'error', errorMessage: pollError } : s))
        toast.error(`Failed to process file "${source.name}": ${pollError}`)
      } else {
        setSources(prev => prev.map(s => s.id === source.id ? { ...s, uploadStatus: 'pending' } : s))
        // No error toast, just keep as pending
      }
    })
  }

  const toggleSourceChecked = (id: string, checked: boolean) => {
    setSources(prev => prev.map(source =>
      source.id === id ? { ...source, checked } : source
    ))
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return
    setMessages((prev) => [...prev, { role: 'human', content: inputMessage }])
    setInputMessage('')
    setIsLoading(true)

    const selectedSources = sources.filter((source) => source.checked).map((source) => source.name)

    try {
      const response = await fetch(`${API_BASE_URL}/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [...messages, { role: 'human', content: inputMessage }],
          customPrompt: '',
          enableCaching: enableCaching,
          similarityThreshold: similarityThreshold,
          ignoreCache: false,
          selectedSources: selectedSources,
        }),
      })

      if (!response.ok) {
        // Do not show error, just keep spinner/loading state
        return
      }

      const reader = response.body?.getReader()
      if (!reader) return

      const decoder = new TextDecoder('utf-8')
      let done = false
      let assistantMessage = ''

      while (!done) {
        const { value, done: doneReading } = await reader.read()
        done = doneReading
        if (value) {
          const chunk = decoder.decode(value)
          assistantMessage += chunk
          setMessages((prev) => {
            const newMessages = [...prev]
            if (newMessages.length === 0 || newMessages[newMessages.length - 1].role !== 'assistant') {
              newMessages.push({ role: 'assistant', content: chunk })
            } else {
              newMessages[newMessages.length - 1].content += chunk
            }
            return newMessages
          })
        }
      }
    } catch (error: any) {
      // Swallow error, keep spinner/loading state, do not show error toast
      return
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteSource = async (id: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/documents?document_id=${id}`, {
        method: 'DELETE'
      })
      const data = await response.json()
      if (data.message === "Document deleted successfully") {
        setSources(prev => prev.filter(source => source.id !== id))
        toast.success('Document deleted successfully.')
      } else {
        throw new Error(data.detail || 'Failed to delete document.')
      }
    } catch (error: any) {
      console.error('Error deleting document:', error)
      toast.error(error.message || 'Failed to delete document.')
    }
  }

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div className={`flex h-screen flex-col ${isDarkMode ? 'bg-gradient-to-br from-[#1A1B26] to-[#2A2B36] text-white' : 'bg-gray-100 text-black'}`}>
      {/* Title Bar */}
      <div className={`h-12 border-b border-[#3A3B46] flex items-center justify-between px-4 bg-[#25262B]/80 backdrop-blur-sm`}>
        <div className="flex items-center">
          <div className="w-8 h-8 bg-gradient-to-br from-[#4F46E5] to-[#7F9CF5] rounded-full mr-2"></div>
          <h1 className="text-xl tracking-tight">Elastic LM</h1>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="ghost" size="icon" onClick={() => {
            setSources([])
            setMessages([])
            setInputMessage('')
            setSelectedLLM('default-llm')
            setEnableCaching(false)
            setSimilarityThreshold(80)
            setChatId(null)
            toast.info('New session started.')
          }} title="Start a New Session">
            <RefreshCw className="h-5 w-5 text-gray-400 hover:text-white transition-colors" />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setIsDarkMode(!isDarkMode)}>
            {isDarkMode ? <Sun className="h-5 w-5 text-gray-400 hover:text-white transition-colors" /> : <Moon className="h-5 w-5" />}
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden p-4">
        {/* Center Panel */}
        <div className="flex-1 flex flex-col bg-[#25262B]/80 backdrop-blur-md rounded-xl overflow-hidden shadow-xl">
          <div className="flex flex-col h-full">
            {/* Chat Header */}
            <div className="p-3 border-b border-[#3A3B46] flex items-center justify-between">
              <h2 className="text-lg">Chat</h2>
              {/* Sources Upload Button */}
              <Button
                variant="outline"
                size="sm"
                className="bg-[#4F46E5]/20 text-[#A5B4FC] border-[#4F46E5]/50 hover:bg-[#4F46E5]/40 transition-all text-sm"
                onClick={() => setIsUploadDialogOpen(true)}
              >
                <Plus className="mr-2 h-4 w-4" />
                Upload Files
              </Button>
            </div>

            {/* Sources List (Minimal) */}
            {sources.length > 0 && (
              <div className="px-4 py-2 border-b border-[#3A3B46]">
                <div className="flex flex-wrap gap-2">
                  {sources.map(source => (
                    <SourceItem
                      key={source.id}
                      id={source.id}
                      name={source.name}
                      checked={source.checked}
                      uploadStatus={source.uploadStatus}
                      errorMessage={source.errorMessage}
                      onCheckedChange={(checked) => toggleSourceChecked(source.id, checked)}
                      onDelete={handleDeleteSource}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Chat Messages */}
            <div ref={chatContainerRef} className="flex-1 p-4 overflow-auto">
              <div className="flex flex-col space-y-3">
                {messages.length > 0 ? (
                  messages.map((message, index) => (
                    <ChatMessage key={index} {...message} />
                  ))
                ) : (
                  <div className="text-gray-400 text-center mt-10 text-sm">Upload files to start chatting.</div>
                )}
                {isLoading && <LoadingIndicator />}
              </div>
            </div>

            {/* Chat Input */}
            <div className="p-3 border-t border-[#3A3B46]">
              <Card className="bg-[#1C1C1E]/50 border-[#3A3B46] backdrop-blur-sm">
                <div className="flex items-center p-2 gap-2">
                  <Input
                    className="flex-1 bg-transparent border-0 focus-visible:ring-0 text-white placeholder:text-gray-400 text-sm"
                    placeholder={
                      hasUploadedFiles
                        ? "Type your message..."
                        : "Upload files to get started"
                    }
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                  />
                  <Button
                    size="icon"
                    className="h-9 w-9 rounded-full bg-gradient-to-br from-[#4F46E5] to-[#7F9CF5] hover:from-[#4338CA] hover:to-[#6B7280] transition-all"
                    onClick={handleSendMessage}
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </Card>
              <div className="text-xs text-gray-400 text-center mt-2">
                I can be inaccurate, please double-check responses.
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel */}
        <div className={`
          relative flex-shrink-0 transition-all duration-300
          ${rightPanelOpen ? 'w-72' : 'w-10'}
        `}>
          <div className={`absolute inset-0 flex flex-col bg-[#25262B]/80 backdrop-blur-md rounded-xl overflow-hidden shadow-xl`}>
            {rightPanelOpen ? (
              <div className="flex flex-col h-full">
                {/* Panel Header */}
                <div className="p-3 border-b border-[#3A3B46] flex justify-between items-center">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setRightPanelOpen(false)}
                    className="mr-2"
                  >
                    <ChevronLeft className="h-4 w-4 text-gray-400 hover:text-white transition-colors" />
                  </Button>
                  <h2 className="text-lg">Settings</h2>
                </div>

                {/* Panel Body */}
                <div className="p-4 overflow-auto">
                  <div className="space-y-5">
                    {/* Prompt Instructions Section */}
                    <div className="space-y-2">
                      <h3 className="text-base text-white">
                        Prompt Instructions
                      </h3>
                      <Textarea
                        placeholder="Enter your prompt instructions here..."
                        className="min-h-[100px] bg-[#1C1C1E]/50 border-[#3A3B46] text-white placeholder:text-gray-400 backdrop-blur-sm text-sm"
                      />
                    </div>

                    {/* Chat LLM Selection */}
                    <div className="space-y-2">
                      <Label htmlFor="chat-llm" className="text-white text-sm">
                        Chat LLM
                      </Label>
                      <Select value={selectedLLM} onValueChange={setSelectedLLM}>
                        <SelectTrigger className="bg-[#1C1C1E]/50 border-[#3A3B46] text-white text-sm">
                          <SelectValue placeholder="Select LLM" />
                        </SelectTrigger>
                        <SelectContent className="bg-[#25262B] border-[#3A3B46] text-white">
                          <SelectItem value="default-llm" className="text-sm">Default LLM</SelectItem>
                          <SelectItem value="gpt-3.5-turbo" className="text-sm">GPT-3.5 Turbo</SelectItem>
                          <SelectItem value="gpt-4" className="text-sm">GPT-4</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Chat Configs Section */}
                    <Card className="bg-[#1C1C1E]/50 border-[#3A3B46] backdrop-blur-sm">
                      <div className="p-4 space-y-4">
                        <h3 className="text-base text-white">
                          Chat Configs
                        </h3>
                        <div className="space-y-4">
                          <div className="flex items-center justify-between">
                            <Label htmlFor="enable-caching" className="text-white text-sm">
                              Enable caching
                            </Label>
                            <Switch
                              id="enable-caching"
                              checked={enableCaching}
                              onCheckedChange={setEnableCaching}
                            />
                          </div>
                          <div className="flex items-center justify-between">
                            <Label htmlFor="similarity-threshold" className="text-white text-sm">
                              Similarity threshold
                            </Label>
                            <Input
                              id="similarity-threshold"
                              type="number"
                              min="0"
                              max="99"
                              value={similarityThreshold}
                              onChange={(e) => setSimilarityThreshold(Number(e.target.value))}
                              className="w-16 text-right bg-[#1C1C1E]/50 border-[#3A3B46] text-white text-sm"
                            />
                          </div>
                        </div>
                      </div>
                    </Card>
                  </div>
                </div>
              </div>
            ) : (
              <Button
                variant="ghost"
                size="icon"
                className="h-10 w-10 text-gray-400 hover:text-white transition-colors"
                onClick={() => setRightPanelOpen(true)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* File Upload Dialog */}
      <FileUploadDialog
        open={isUploadDialogOpen}
        onOpenChange={setIsUploadDialogOpen}
        onFilesSelected={handleFilesSelected}
      />

      {/* Toast Notifications */}
      <ToastContainer />
    </div>
  )
}