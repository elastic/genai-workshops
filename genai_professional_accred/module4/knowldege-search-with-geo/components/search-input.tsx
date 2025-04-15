"use client"

import type { KeyboardEvent } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search } from "lucide-react"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"

interface SearchInputProps {
  value: string
  onChange: (value: string) => void
  onSearch: () => void
  isLoading?: boolean
  mapLocationOnly: boolean
  onMapLocationOnlyChange: (value: boolean) => void
}

export function SearchInput({
  value,
  onChange,
  onSearch,
  isLoading = false,
  mapLocationOnly,
  onMapLocationOnlyChange,
}: SearchInputProps) {
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      onSearch()
    }
  }

  return (
    <div className="flex flex-col w-full gap-2">
      <div className="flex w-full items-center space-x-2">
        <div className="relative flex-1">
          <Input
            type="text"
            placeholder="Search WikiVoyage or ask a question..."
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            className="pl-4 pr-10 py-6 text-lg rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white border-gray-200 dark:border-gray-700"
            disabled={isLoading}
          />
        </div>
        <Button onClick={onSearch} disabled={isLoading} className="px-6 py-6 h-auto">
          {isLoading ? (
            <div className="animate-spin h-5 w-5 border-2 border-current border-t-transparent rounded-full" />
          ) : (
            <>
              <Search className="mr-2 h-5 w-5" />
              Search
            </>
          )}
        </Button>
      </div>

      <div className="flex items-center space-x-2">
        <Checkbox
          id="map-location-only"
          checked={mapLocationOnly}
          onCheckedChange={(checked) => onMapLocationOnlyChange(checked === true)}
        />
        <Label htmlFor="map-location-only" className="text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
          Restrict to pages with map location information
        </Label>
      </div>
    </div>
  )
}
