import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const { bbox, url, apiKey } = await request.json()

    if (!url || !apiKey || !bbox || !Array.isArray(bbox) || bbox.length !== 4) {
      return NextResponse.json({ success: false, error: "Missing or invalid parameters" }, { status: 400 })
    }

    const [minLng, minLat, maxLng, maxLat] = bbox
    const cleanUrl = url.endsWith("/") ? url.slice(0, -1) : url

    console.log("Geo search with bbox:", bbox)

    // Use a simpler query that just returns documents with coordinates
    const queryBody = {
      size: 100,
      query: {
        nested: {
          path: "coordinates",
          query: {
            exists: {
              field: "coordinates.coord",
            },
          },
        },
      },
      _source: false,
      fields: ["title", "opening_text", "source_text", "coordinates.coord"],
    }

    const response = await fetch(`${cleanUrl}/wiki-voyage_2025-03-07_elser-embeddings/_search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `ApiKey ${apiKey}`,
      },
      body: JSON.stringify(queryBody),
      signal: AbortSignal.timeout(10000),
    })

    if (!response.ok) {
      return NextResponse.json(
        { success: false, error: `Elasticsearch error: ${response.status} ${response.statusText}` },
        { status: response.status },
      )
    }

    const data = await response.json()

    // Filter results client-side based on the bounding box
    const filteredResults = data.hits.hits.filter((hit: any) => {
      try {
        if (hit.fields?.coordinates?.[0]?.coord?.[0]?.coordinates) {
          const [lng, lat] = hit.fields.coordinates[0].coord[0].coordinates

          // Log the coordinates and bounding box for debugging
          console.log(`Checking if [${lng}, ${lat}] is in bbox [${minLng}, ${minLat}, ${maxLng}, ${maxLat}]`)

          return lng >= minLng && lng <= maxLng && lat >= minLat && lat <= maxLat
        }
        return false
      } catch (e) {
        console.error("Error filtering hit:", e)
        return false
      }
    })

    console.log(
      `Geo search returned ${data.hits.hits?.length || 0} total results, filtered to ${filteredResults.length}`,
    )

    return NextResponse.json({ success: true, data: filteredResults || [] })
  } catch (error) {
    console.error("Error in geo-search API:", error)
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 },
    )
  }
}

