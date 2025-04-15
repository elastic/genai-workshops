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

    // Use Elasticsearch's geo_bounding_box query directly
    const queryBody = {
      size: 100,
      query: {
        nested: {
          path: "coordinates",
          query: {
            bool: {
              filter: {
                geo_bounding_box: {
                  "coordinates.coord": {
                    top_left: {
                      lat: maxLat,
                      lon: minLng,
                    },
                    bottom_right: {
                      lat: minLat,
                      lon: maxLng,
                    },
                  },
                },
              },
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

    console.log(`Geo search returned ${data.hits.hits?.length || 0} results using geo_bounding_box filter`)

    return NextResponse.json({ success: true, data: data.hits.hits || [] })
  } catch (error) {
    console.error("Error in geo-search API:", error)
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 },
    )
  }
}
