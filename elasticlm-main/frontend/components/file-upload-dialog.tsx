'use client'

import { useState, useRef } from 'react'
import { Upload } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

interface FileUploadDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onFilesSelected: (files: File[]) => void
}

export function FileUploadDialog({ 
  open, 
  onOpenChange,
  onFilesSelected 
}: FileUploadDialogProps) {
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const files = Array.from(e.dataTransfer.files)
    onFilesSelected(files)
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    onFilesSelected(files)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-center">Upload sources</DialogTitle>
        </DialogHeader>
        <div
          className={`
            mt-4 flex flex-col items-center justify-center rounded-lg border-2 border-dashed
            p-12 text-center transition-colors
            ${isDragging ? 'border-blue-500 bg-blue-500/10' : 'border-gray-700'}
          `}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="mb-4 rounded-full bg-blue-500/20 p-3">
            <Upload className="h-6 w-6 text-blue-500" />
          </div>
          <div className="mb-2 text-lg">
            Drag & drop or{' '}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="text-blue-500 hover:underline focus:outline-none"
            >
              choose file
            </button>{' '}
            to upload
          </div>
          <p className="text-sm text-gray-500">
            Supported file types: PDF, .txt, Markdown
          </p>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={handleFileInput}
            accept=".pdf,.txt,.md,.markdown"
          />
        </div>
      </DialogContent>
    </Dialog>
  )
}
