"use client"

import { useState, useEffect, useCallback } from "react"
import { SearchInput } from "@/components/search-input"
import { MapView } from "@/components/map-view"
import { ResultsList } from "@/components/results-list"
import { SettingsDialog } from "@/components/settings-dialog"
import { ThemeToggle } from "@/components/theme-toggle"
import { searchElasticsearch, searchWithGeoBoundingBox } from "@/lib/elasticsearch"
import { Logo } from "@/components/logo"
import { useTheme } from "next-themes"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle } from "lucide-react"

export default function Home() {
  const [searchQuery, setSearchQuery] = useState("")
  const [results, setResults] = useState<any[]>([])
  const [isMapExpanded, setIsMapExpanded] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mapLocationOnly, setMapLocationOnly] = useState(false)
  const [elasticConfig, setElasticConfig] = useState({
    url: "",
    apiKey: "",
  })
  const [mapKey, setMapKey] = useState(0) // Add a key to force map re-render
  const [isAutoFilterActive, setIsAutoFilterActive] = useState(false)
  const { resolvedTheme } = useTheme()

  // Load Leaflet CSS
  useEffect(() => {
    // Add Leaflet CSS
    const link = document.createElement("link")
    link.rel = "stylesheet"
    link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    link.integrity = "sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
    link.crossOrigin = ""
    document.head.appendChild(link)

    return () => {
      // Make sure we don't remove the link if it's not in the document anymore
      if (document.head.contains(link)) {
        document.head.removeChild(link)
      }
    }
  }, [])

  // Apply theme class to document
  useEffect(() => {
    if (resolvedTheme === "dark") {
      document.documentElement.classList.add("dark")
    } else {
      document.documentElement.classList.remove("dark")
    }
  }, [resolvedTheme])

  const handleSearch = useCallback(
    async (query: string = searchQuery) => {
      if (!query.trim() || !elasticConfig.url || !elasticConfig.apiKey) {
        if (!elasticConfig.url || !elasticConfig.apiKey) {
          setError("Please configure Elasticsearch settings first")
        }
        return
      }

      setIsLoading(true)
      setError(null)

      try {
        const searchResults = await searchElasticsearch(query, elasticConfig, mapLocationOnly)
        setResults(searchResults)
        // Force map to re-render
        setMapKey((prev) => prev + 1)
      } catch (error) {
        console.error("Search error:", error)
        setError(error instanceof Error ? error.message : "An error occurred during search")
        setResults([])
      } finally {
        setIsLoading(false)
      }
    },
    [searchQuery, elasticConfig, mapLocationOnly],
  )

  const handleGeoSearch = useCallback(
    async (bbox: [number, number, number, number]) => {
      if (!elasticConfig.url || !elasticConfig.apiKey) {
        setError("Please configure Elasticsearch settings first")
        return
      }

      setIsLoading(true)
      setError(null)

      try {
        const searchResults = await searchWithGeoBoundingBox(bbox, elasticConfig)
        setResults(searchResults)
        // Force map to re-render
        setMapKey((prev) => prev + 1)
      } catch (error) {
        console.error("Geo search error:", error)
        setError(error instanceof Error ? error.message : "An error occurred during geo search")
        setResults([])
      } finally {
        setIsLoading(false)
      }
    },
    [elasticConfig],
  )

  const handleViewportChange = useCallback(
    async (bbox: [number, number, number, number]) => {
      if (!elasticConfig.url || !elasticConfig.apiKey) {
        setError("Please configure Elasticsearch settings first")
        return
      }

      setIsLoading(true)
      setError(null)

      try {
        const searchResults = await searchWithGeoBoundingBox(bbox, elasticConfig)
        setResults(searchResults)
      } catch (error) {
        console.error("Viewport search error:", error)
        setError(error instanceof Error ? error.message : "An error occurred during map viewport search")
        setResults([])
      } finally {
        setIsLoading(false)
      }
    },
    [elasticConfig],
  )

  const handleMapLocationOnlyChange = useCallback(
    (checked: boolean) => {
      setMapLocationOnly(checked)
      if (searchQuery.trim()) {
        // Re-run the search with the new filter setting
        handleSearch(searchQuery)
      }
    },
    [searchQuery, handleSearch],
  )

  // Log results for debugging
  useEffect(() => {
    if (results.length > 0) {
      console.log(`Rendering ${results.length} results`)

      // Log the first result with coordinates
      const resultWithCoords = results.find((r) => r.fields?.coordinates?.[0]?.coord?.[0]?.coordinates)

      if (resultWithCoords) {
        const coords = resultWithCoords.fields.coordinates[0].coord[0].coordinates
        console.log(`Example coordinates: [${coords}]`)
      }
    }
  }, [results])

  return (
    <main className="container mx-auto px-4 py-6 min-h-screen bg-white dark:bg-gray-900 transition-colors duration-200">
      <div className="flex justify-between items-center mb-8">
        <div className="flex items-center gap-4">
          <Logo />
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">WikiVoyage Search</h1>
        </div>
        <div className="flex items-center gap-4">
          <SettingsDialog config={elasticConfig} onConfigChange={setElasticConfig} />
          <ThemeToggle />
        </div>
      </div>

      <SearchInput
        value={searchQuery}
        onChange={setSearchQuery}
        onSearch={() => handleSearch()}
        isLoading={isLoading}
        mapLocationOnly={mapLocationOnly}
        onMapLocationOnlyChange={handleMapLocationOnlyChange}
      />

      {error && (
        <Alert variant="destructive" className="mt-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="my-6">
        <MapView
          key={mapKey} // Force re-render when results change
          results={results}
          isExpanded={isMapExpanded}
          onToggleExpand={() => setIsMapExpanded(!isMapExpanded)}
          onBoundingBoxSelect={handleGeoSearch}
          onViewportChange={handleViewportChange}
          isAutoFilterActive={isAutoFilterActive}
        />
      </div>

      <div className={`mt-6 ${isMapExpanded ? "mt-6" : "mt-6"}`}>
        <ResultsList results={results} />
      </div>
    </main>
  )
}

