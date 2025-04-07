"use client"

import { useState, useEffect } from "react"

export function useLeaflet() {
  const [L, setL] = useState<any>(null)
  const [isLoaded, setIsLoaded] = useState(false)

  useEffect(() => {
    if (typeof window !== "undefined") {
      import("leaflet").then((leaflet) => {
        setL(leaflet.default)
        setIsLoaded(true)
      })
    }
  }, [])

  return { L, isLoaded }
}

