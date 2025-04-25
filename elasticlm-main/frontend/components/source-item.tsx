// frontend/components/source-item.tsx

import { Trash, Loader2, AlertTriangle } from 'lucide-react'
import { Checkbox } from "@/components/ui/checkbox"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import Tooltip from '@mui/material/Tooltip' // Ensure @mui/material is installed or use your preferred tooltip library
import { FC } from 'react'

interface SourceItemProps {
  id: string
  name: string
  checked: boolean
  uploadStatus: 'pending' | 'uploading' | 'success' | 'error'
  errorMessage?: string
  onCheckedChange: (checked: boolean) => void
  onDelete: (id: string) => void
}

export const SourceItem: FC<SourceItemProps> = ({
  id,
  name,
  checked,
  uploadStatus,
  errorMessage,
  onCheckedChange,
  onDelete
}) => {
  // Debugging: Log the props received
  console.log(`Rendering SourceItem: id=${id}, name=${name}, checked=${checked}, uploadStatus=${uploadStatus}, errorMessage=${errorMessage}`)

  return (
    <div className="flex items-center justify-between mt-2">
      <div className="flex items-center">
        {/* Display loader when uploading */}
        {uploadStatus === 'uploading' && (
          <Loader2 className="animate-spin h-4 w-4 text-blue-500 mr-2" />
        )}

        {/* Display error icon with tooltip on error */}
        {uploadStatus === 'error' && (
          <Tooltip title={errorMessage || 'Error uploading file'}>
            <AlertTriangle className="text-red-500 h-4 w-4 mr-2" />
          </Tooltip>
        )}

        {/* Display checkbox on success */}
        {uploadStatus === 'success' && (
          <Checkbox
            id={`source-${id}`}
            checked={checked}
            onCheckedChange={(val) => onCheckedChange(val)}
            disabled={uploadStatus !== 'success'}
          />
        )}

        {/* Display placeholder when pending */}
        {uploadStatus === 'pending' && (
          <div className="h-4 w-4 mr-2 bg-gray-300 rounded-full"></div>
        )}

        {/* Label for the source name */}
        <Label htmlFor={`source-${id}`} className="ml-2 text-sm">
          {name}
        </Label>
      </div>

      {/* Delete Button */}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => onDelete(id)}
        disabled={uploadStatus === 'uploading'} // Disable delete during upload
        title="Delete Source"
      >
        <Trash className="h-4 w-4 text-red-500" />
      </Button>
    </div>
  )
}
