import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const { query, url, apiKey, mapLocationOnly } = await request.json()

    if (!url || !apiKey || !query) {
      return NextResponse.json({ success: false, error: "Missing required parameters" }, { status: 400 })
    }

    const cleanUrl = url.endsWith("/") ? url.slice(0, -1) : url

    // Build the query body
    const queryBody: any = {
      size: 20,
      retriever: {
        rrf: {
          rank_window_size: 20,
          retrievers: [
            {
              standard: {
                query: {
                  semantic: {
                    field: "source_text_semantic",
                    query: query,
                  },
                },
              },
            },
            {
              standard: {
                query: {
                  multi_match: {
                    query: query,
                    fields: ["source_text"],
                  },
                },
              },
            },
          ],
        },
      },
      _source: false,
      fields: ["title", "opening_text", "source_text", "coordinates.coord"],
    }

    // Add filter for map location if requested
    if (mapLocationOnly) {
      queryBody.retriever.rrf.filter = {
        nested: {
          path: "coordinates",
          query: {
            exists: {
              field: "coordinates.coord",
            },
          },
        },
      }
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

    // Log the first result to see the structure
    if (data.hits.hits && data.hits.hits.length > 0) {
      console.log("Sample result structure:", JSON.stringify(data.hits.hits[0], null, 2))
    }

    return NextResponse.json({ success: true, data: data.hits.hits || [] })
  } catch (error) {
    console.error("Error in search API:", error)
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 },
    )
  }
}

