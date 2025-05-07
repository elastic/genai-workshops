interface ElasticConfig {
  url: string
  apiKey: string
}

export async function searchElasticsearch(query: string, config: ElasticConfig, mapLocationOnly = false) {
  try {
    if (!config.url || !config.apiKey) {
      console.error("Missing Elasticsearch configuration")
      return []
    }

    const response = await fetch("/api/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        url: config.url,
        apiKey: config.apiKey,
        mapLocationOnly,
      }),
    })

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ error: `Error: ${response.status} ${response.statusText}` }))
      throw new Error(errorData.error || `Error: ${response.status} ${response.statusText}`)
    }

    const result = await response.json()
    return result.data || []
  } catch (error) {
    console.error("Error searching Elasticsearch:", error)
    throw error // Re-throw to allow the calling code to handle it
  }
}

export async function searchWithGeoBoundingBox(bbox: [number, number, number, number], config: ElasticConfig) {
  try {
    if (!config.url || !config.apiKey) {
      console.error("Missing Elasticsearch configuration")
      return []
    }

    const response = await fetch("/api/geo-search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        bbox,
        url: config.url,
        apiKey: config.apiKey,
      }),
    })

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ error: `Error: ${response.status} ${response.statusText}` }))
      throw new Error(errorData.error || `Error: ${response.status} ${response.statusText}`)
    }

    const result = await response.json()
    return result.data || []
  } catch (error) {
    console.error("Error searching Elasticsearch with geo bounding box:", error)
    throw error // Re-throw to allow the calling code to handle it
  }
}
