import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const { url, apiKey } = await request.json()

    if (!url || !apiKey) {
      return NextResponse.json({ success: false, error: "URL and API key are required" }, { status: 400 })
    }

    // Try multiple endpoints for validation
    const endpoints = [
      "/", // Root endpoint
      "/_cat/indices?format=json", // List indices (simpler permission)
      "/_cluster/health", // Cluster health (might require more permissions)
    ]

    let lastError = null
    let success = false
    let responseData = null

    // Try each endpoint until one succeeds
    for (const endpoint of endpoints) {
      try {
        const fullUrl = `${url}${endpoint}`
        console.log(`Trying to validate with endpoint: ${fullUrl}`)

        const response = await fetch(fullUrl, {
          method: "GET",
          headers: {
            Authorization: `ApiKey ${apiKey}`,
            "Content-Type": "application/json",
          },
          // Add a reasonable timeout
          signal: AbortSignal.timeout(5000),
        })

        // If we get a 401 or 403, it means the API key is invalid
        if (response.status === 401 || response.status === 403) {
          return NextResponse.json(
            { success: false, error: "Invalid API key or insufficient permissions" },
            { status: 401 },
          )
        }

        // If we get a 410 Gone, try the next endpoint
        if (response.status === 410) {
          lastError = "This endpoint is not available (410 Gone)"
          continue
        }

        if (!response.ok) {
          lastError = `Elasticsearch returned: ${response.status} ${response.statusText}`
          continue
        }

        // Try to parse the response as JSON
        try {
          responseData = await response.json()
          success = true
          break // We found a working endpoint
        } catch (e) {
          // If the response is not JSON, but status is OK, consider it a success
          if (response.ok) {
            success = true
            responseData = { message: "Connection successful" }
            break
          }
          lastError = "Invalid JSON response from Elasticsearch"
          continue
        }
      } catch (endpointError) {
        lastError = endpointError instanceof Error ? endpointError.message : "Unknown error"
        continue
      }
    }

    if (success) {
      return NextResponse.json({
        success: true,
        message: "Connection successful",
        data: responseData,
      })
    } else {
      return NextResponse.json(
        { success: false, error: lastError || "Failed to connect to Elasticsearch" },
        { status: 400 },
      )
    }
  } catch (error) {
    console.error("Error validating Elasticsearch connection:", error)

    // Provide more helpful error messages
    let errorMessage = "Failed to connect to Elasticsearch"
    if (error instanceof Error) {
      if (error.name === "AbortError") {
        errorMessage = "Connection timed out. Please check the URL and try again."
      } else {
        errorMessage = error.message || errorMessage
      }
    }

    return NextResponse.json({ success: false, error: errorMessage }, { status: 500 })
  }
}
