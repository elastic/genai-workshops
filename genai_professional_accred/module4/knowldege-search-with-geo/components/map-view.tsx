"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Maximize2, Minimize2, Filter } from "lucide-react"
import { useTheme } from "next-themes"

// Add a debounce function after the imports
function debounce(func: Function, wait: number) {
  let timeout: NodeJS.Timeout | null = null
  return (...args: any[]) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

interface MapViewProps {
  results: any[]
  isExpanded: boolean
  onToggleExpand: () => void
  onBoundingBoxSelect: (bbox: [number, number, number, number]) => void
  onViewportChange?: (bbox: [number, number, number, number]) => void
  isAutoFilterActive?: boolean
}

export function MapView({
  results,
  isExpanded,
  onToggleExpand,
  onBoundingBoxSelect,
  onViewportChange,
  isAutoFilterActive = false,
}: MapViewProps) {
  const mapRef = useRef<HTMLDivElement>(null)
  const leafletMap = useRef<any>(null)
  const [selectionMode, setSelectionMode] = useState(false)
  const [selectionRect, setSelectionRect] = useState<any>(null)
  const [isMapInitialized, setIsMapInitialized] = useState(false)
  const markersRef = useRef<any[]>([])
  const { resolvedTheme } = useTheme()
  const [markersCount, setMarkersCount] = useState(0)
  const [L, setL] = useState<any>(null)
  const [autoFilter, setAutoFilter] = useState(false)
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)
  const isAutoFilteringRef = useRef(false)
  const [isFilteringActive, setIsFilteringActive] = useState(false)
  const currentViewRef = useRef<{ center: [number, number]; zoom: number } | null>(null)

  // Selection state variables
  const startPointRef = useRef<any>(null)
  const rectRef = useRef<any>(null)
  const isDraggingRef = useRef(false)

  // Load Leaflet
  useEffect(() => {
    if (typeof window === "undefined") return

    const loadLeaflet = async () => {
      try {
        const leaflet = await import("leaflet")
        setL(leaflet.default)
      } catch (error) {
        console.error("Failed to load Leaflet:", error)
      }
    }

    loadLeaflet()
  }, [])

  // Initialize the map
  useEffect(() => {
    if (!L || typeof window === "undefined" || !mapRef.current) return

    // Clean up existing map if it exists
    if (leafletMap.current) {
      leafletMap.current.remove()
      leafletMap.current = null
    }

    // Make sure the map container is empty
    if (mapRef.current) mapRef.current.innerHTML = ""

    // Initialize the map
    const map = L.map(mapRef.current).setView([20, 0], 2)

    // Choose tile layer based on theme
    const isDark = resolvedTheme === "dark"

    // Use OpenStreetMap tiles for light mode and CartoDB Dark Matter for dark mode
    const tileUrl = isDark
      ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      : "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"

    const attribution = isDark
      ? '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
      : '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'

    L.tileLayer(tileUrl, {
      attribution: attribution,
      maxZoom: 19,
    }).addTo(map)

    // Store the map instance
    leafletMap.current = map
    setIsMapInitialized(true)

    // Track map view changes
    map.on("moveend", () => {
      if (map) {
        const center = map.getCenter()
        currentViewRef.current = {
          center: [center.lat, center.lng],
          zoom: map.getZoom(),
        }
      }
    })

    // Force a resize event to ensure the map renders correctly
    setTimeout(() => {
      map.invalidateSize()
    }, 100)
  }, [L, resolvedTheme])

  // Set up selection mode event handlers
  useEffect(() => {
    if (!leafletMap.current || !L) return

    const map = leafletMap.current

    // Clean up any existing handlers
    map.off("mousedown")
    map.off("mousemove")
    map.off("mouseup")

    if (selectionMode) {
      console.log("Selection mode activated")

      // Disable map dragging in selection mode
      map.dragging.disable()

      // Change cursor to crosshair
      if (mapRef.current) {
        mapRef.current.style.cursor = "crosshair"
      }

      // Set up event handlers for selection
      map.on("mousedown", (e) => {
        console.log("Mouse down in selection mode")
        startPointRef.current = e.latlng
        isDraggingRef.current = true

        // Create rectangle
        rectRef.current = L.rectangle(
          [
            [startPointRef.current.lat, startPointRef.current.lng],
            [startPointRef.current.lat, startPointRef.current.lng],
          ],
          {
            color: "#3b82f6",
            weight: 2,
            fillOpacity: 0.2,
          },
        ).addTo(map)

        setSelectionRect(rectRef.current)
      })

      map.on("mousemove", (e) => {
        if (!isDraggingRef.current || !startPointRef.current || !rectRef.current) return

        // Update rectangle bounds
        const bounds = L.latLngBounds(startPointRef.current, e.latlng)
        rectRef.current.setBounds(bounds)
      })

      map.on("mouseup", (e) => {
        if (!isDraggingRef.current || !startPointRef.current || !rectRef.current) return

        console.log("Mouse up in selection mode")
        isDraggingRef.current = false

        // Get bounds
        const bounds = rectRef.current.getBounds()
        const sw = bounds.getSouthWest()
        const ne = bounds.getNorthEast()

        // Submit search
        onBoundingBoxSelect([sw.lng, sw.lat, ne.lng, ne.lat])

        // Clean up
        map.removeLayer(rectRef.current)
        startPointRef.current = null
        rectRef.current = null
        setSelectionRect(null)
      })
    } else {
      // Re-enable map dragging when not in selection mode
      map.dragging.enable()

      // Reset cursor
      if (mapRef.current) {
        mapRef.current.style.cursor = ""
      }
    }

    return () => {
      // Clean up event handlers
      if (map) {
        map.off("mousedown")
        map.off("mousemove")
        map.off("mouseup")
      }
    }
  }, [selectionMode, L, onBoundingBoxSelect])

  // Update autoFilter state when isAutoFilterActive prop changes
  useEffect(() => {
    setAutoFilter(isAutoFilterActive)
  }, [isAutoFilterActive])

  // Add this after the useEffect that initializes the map
  useEffect(() => {
    if (!L || !leafletMap.current || !onViewportChange || !autoFilter) return

    // Create a debounced version of the viewport change handler
    const handleViewportChange = () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }

      setIsFilteringActive(true)

      debounceTimerRef.current = setTimeout(() => {
        const bounds = leafletMap.current.getBounds()
        const sw = bounds.getSouthWest()
        const ne = bounds.getNorthEast()

        // Set flag to indicate we're auto-filtering
        isAutoFilteringRef.current = true

        // Pass the current viewport bounds to the parent
        onViewportChange([sw.lng, sw.lat, ne.lng, ne.lat])

        // Reset filtering indicator after a short delay
        setTimeout(() => {
          setIsFilteringActive(false)
        }, 500)
      }, 500) // 500ms debounce
    }

    // Add event listener for map movement
    leafletMap.current.on("moveend", handleViewportChange)

    // Clean up
    return () => {
      if (leafletMap.current) {
        leafletMap.current.off("moveend", handleViewportChange)
      }
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [L, onViewportChange, autoFilter])

  // Update markers when results change
  useEffect(() => {
    if (!L || !isMapInitialized || !leafletMap.current) return

    // Clear existing markers
    markersRef.current.forEach((marker) => {
      if (leafletMap.current) leafletMap.current.removeLayer(marker)
    })
    markersRef.current = []

    console.log("Updating markers with results:", results.length)
    let validMarkers = 0

    // Create a custom icon for better visibility
    const customIcon = L.divIcon({
      className: "custom-map-marker",
      html: `<div style="background-color: red; width: 16px; height: 16px; border-radius: 50%; border: 2px solid black;"></div>`,
      iconSize: [20, 20],
      iconAnchor: [10, 10],
    })

    // Add a test marker at 0,0 to verify the map is working
    const testMarker = L.marker([0, 0], {
      icon: customIcon,
    }).addTo(leafletMap.current)
    testMarker.bindPopup("Test Marker at [0, 0]")
    markersRef.current.push(testMarker)
    validMarkers++

    // Process each result
    results.forEach((result, index) => {
      try {
        // Extract coordinates from the nested structure
        if (result.fields?.coordinates?.[0]?.coord?.[0]?.coordinates) {
          const coordinates = result.fields.coordinates[0].coord[0].coordinates

          if (Array.isArray(coordinates) && coordinates.length === 2) {
            // Coordinates are [longitude, latitude]
            const [lng, lat] = coordinates

            // Log the coordinates for debugging
            console.log(`Creating marker for result ${index} at [${lat}, ${lng}] (lat, lng)`)

            // Create a marker with the custom icon
            const marker = L.marker([lat, lng], {
              icon: customIcon,
            }).addTo(leafletMap.current)

            // Add a popup with the title
            if (result.fields.title) {
              marker.bindPopup(result.fields.title[0] || "Location")
            }

            markersRef.current.push(marker)
            validMarkers++
          }
        }
      } catch (e) {
        console.error(`Error processing coordinates for result ${index}:`, e)
      }
    })

    console.log(`Added ${validMarkers} markers to the map (including test marker)`)
    setMarkersCount(validMarkers)

    // Only fit bounds to markers if NOT in auto-filtering mode
    if (markersRef.current.length > 1 && !isAutoFilteringRef.current) {
      // More than just the test marker and not auto-filtering
      const group = L.featureGroup(markersRef.current)
      leafletMap.current.fitBounds(group.getBounds(), { padding: [50, 50] })
    }

    // Reset the auto-filtering flag
    isAutoFilteringRef.current = false
  }, [L, results, isMapInitialized])

  // Handle map resize when expanded/collapsed
  useEffect(() => {
    if (leafletMap.current) {
      setTimeout(() => {
        leafletMap.current.invalidateSize()
      }, 100)
    }
  }, [isExpanded])

  const toggleSelectionMode = () => {
    // Store current view before toggling selection mode
    if (leafletMap.current && !selectionMode) {
      const center = leafletMap.current.getCenter()
      currentViewRef.current = {
        center: [center.lat, center.lng],
        zoom: leafletMap.current.getZoom(),
      }
    }

    // Clean up any existing selection
    if (selectionMode && rectRef.current && leafletMap.current) {
      leafletMap.current.removeLayer(rectRef.current)
      rectRef.current = null
      startPointRef.current = null
      isDraggingRef.current = false
      setSelectionRect(null)
    }

    // Toggle selection mode
    setSelectionMode(!selectionMode)
  }

  const toggleAutoFilter = () => {
    const newAutoFilter = !autoFilter
    setAutoFilter(newAutoFilter)

    // Notify parent component of the change
    if (onViewportChange && newAutoFilter) {
      // Immediately trigger a viewport search when turning on auto-filter
      const bounds = leafletMap.current.getBounds()
      const sw = bounds.getSouthWest()
      const ne = bounds.getNorthEast()

      // Set flag to indicate we're auto-filtering
      isAutoFilteringRef.current = true
      setIsFilteringActive(true)

      // Pass the current viewport bounds to the parent
      onViewportChange([sw.lng, sw.lat, ne.lng, ne.lat])

      // Reset filtering indicator after a short delay
      setTimeout(() => {
        setIsFilteringActive(false)
      }, 500)
    }
  }

  return (
    <div
      className={`relative rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 ${
        isExpanded ? "h-[60vh]" : "h-[300px]"
      } z-[1]`}
    >
      {/* Add Leaflet CSS */}
      <style jsx global>{`
        .leaflet-container {
          height: 100%;
          width: 100%;
          background-color: #f0f0f0;
        }
        .dark .leaflet-container {
          background-color: #333;
        }
        .custom-map-marker {
          z-index: 1000 !important;
        }
      `}</style>

      <div ref={mapRef} className="h-full w-full" />

      <div className="absolute top-2 left-2 z-[1000] flex gap-2">
        <Button variant="secondary" size="sm" onClick={onToggleExpand}>
          {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
        </Button>

        <Button
          variant={selectionMode ? "default" : "secondary"}
          size="sm"
          onClick={toggleSelectionMode}
          className={selectionMode ? "bg-primary text-primary-foreground" : ""}
        >
          {selectionMode ? "Cancel Selection" : "Select Area"}
        </Button>

        <Button
          variant={autoFilter ? "default" : "secondary"}
          size="sm"
          onClick={toggleAutoFilter}
          className={autoFilter ? "bg-primary text-primary-foreground" : ""}
        >
          {autoFilter ? "Auto-Filter On" : "Auto-Filter Off"}
        </Button>
      </div>

      {selectionMode && (
        <div className="absolute bottom-2 left-2 z-[1000] bg-white dark:bg-gray-800 p-2 rounded-md shadow-md">
          <p className="text-sm text-gray-900 dark:text-gray-100">Click and drag to select an area</p>
        </div>
      )}

      <div className="absolute bottom-2 right-2 z-[1000] bg-white dark:bg-gray-800 p-2 rounded-md shadow-md">
        <p className="text-sm text-gray-900 dark:text-gray-100">
          {markersCount > 0 ? `${markersCount} locations on map` : "No locations on map"}
        </p>
      </div>

      {isFilteringActive && autoFilter && (
        <div className="absolute top-2 right-2 z-[1000] bg-primary text-primary-foreground px-3 py-1 rounded-md shadow-md flex items-center">
          <Filter size={14} className="mr-1 animate-pulse" />
          <p className="text-sm">Filtering...</p>
        </div>
      )}
    </div>
  )
}
