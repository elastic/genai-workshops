import { Loader2 } from 'lucide-react'

export function LoadingIndicator() {
  return (
    <div className="flex items-center justify-center p-4">
      <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
    </div>
  )
}

