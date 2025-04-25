// components/chat-message.tsx
import { cn } from "@/lib/utils"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

interface ChatMessageProps {
  role: 'human' | 'assistant'
  content: string
}

export function ChatMessage({ role, content }: ChatMessageProps) {
  return (
    <div
      className={cn(
        "flex w-full",
        role === "human" ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[70%] rounded-2xl px-4 py-2 glassmorphism",
          role === "human"
            ? "bg-[#4F46E5]/30 text-white"
            : "bg-[#2A2B36]/50 text-gray-200"
        )}
      >
        {/* Markdown container with your existing text size + prose styling */}
        <div className="prose prose-sm prose-invert break-words text-sm chat-message-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  )
}
