"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ChevronDown, ChevronUp, Globe } from "lucide-react"

interface ResultsListProps {
  results: any[]
}

export function ResultsList({ results }: ResultsListProps) {
  const [expandedResults, setExpandedResults] = useState<Set<number>>(new Set())

  const toggleExpand = (index: number) => {
    const newExpanded = new Set(expandedResults)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedResults(newExpanded)
  }

  if (results.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">
          No results to display. Try searching for something or selecting an area on the map.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {results.map((result, index) => {
        const isExpanded = expandedResults.has(index)

        // Extract fields from the response format
        const title = result.fields?.title?.[0] || "Untitled"
        const openingText = result.fields?.opening_text?.[0] || "No summary available"
        const sourceText = result.fields?.source_text?.[0] || "No content available"

        // Check if the result has coordinates using the correct path
        let hasCoordinates = false

        if (result.fields?.coordinates?.[0]?.coord?.[0]?.coordinates) {
          const coords = result.fields.coordinates[0].coord[0].coordinates
          hasCoordinates = Array.isArray(coords) && coords.length === 2
        }

        return (
          <Card key={index} className="overflow-hidden bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
            <CardHeader className="py-4 bg-white dark:bg-gray-800">
              <div className="flex justify-between items-center">
                <CardTitle className="text-xl text-gray-900 dark:text-white flex items-center gap-2">
                  {title}
                  {!hasCoordinates && <Globe className="h-4 w-4 text-red-500" title="Missing coordinates" />}
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pb-4 bg-white dark:bg-gray-800">
              <div className="prose dark:prose-invert max-w-none">
                {isExpanded ? (
                  <div className="space-y-4">
                    <div className="wiki-content text-gray-700 dark:text-gray-300">
                      {sourceText.split("\n\n").map((paragraph, i) => {
                        // Handle headings (== Heading ==)
                        if (paragraph.match(/^==\s+.+\s+==$/)) {
                          return (
                            <h2 key={i} className="text-xl font-bold mt-4 mb-2">
                              {paragraph.replace(/^==\s+|\s+==$/g, "")}
                            </h2>
                          )
                        }
                        // Handle subheadings (=== Subheading ===)
                        else if (paragraph.match(/^===\s+.+\s+===$/)) {
                          return (
                            <h3 key={i} className="text-lg font-bold mt-3 mb-1">
                              {paragraph.replace(/^===\s+|\s+===$/g, "")}
                            </h3>
                          )
                        }
                        // Handle lists (starting with * or #)
                        else if (paragraph.startsWith("*") || paragraph.startsWith("#")) {
                          return (
                            <ul key={i} className="list-disc pl-5 space-y-1">
                              {paragraph.split("\n").map((item, j) => (
                                <li key={j}>{item.replace(/^[*#]\s+/, "")}</li>
                              ))}
                            </ul>
                          )
                        }
                        // Regular paragraphs
                        else {
                          // Process wiki formatting within paragraphs
                          let formattedText = paragraph

                          // Check if the paragraph contains a header followed by a list
                          const headerListMatch = paragraph.match(/^(={2,3}\s*(.+?)\s*={2,3})\n([*#].+)$/s)
                          if (headerListMatch) {
                            // Extract the header and list content
                            const [, headerFull, headerText, listContent] = headerListMatch
                            const headerLevel = headerFull.startsWith("===") ? 3 : 2

                            // Format the header
                            const headerTag = headerLevel === 3 ? "h3" : "h2"
                            const headerClass = headerLevel === 3 ? "text-lg" : "text-xl"

                            // Process the list items
                            const listItems = listContent
                              .split("\n")
                              .map((item, j) => {
                                // Remove the list marker (* or #) and trim
                                const cleanItem = item.replace(/^[*#]\s*/, "")
                                return `<li key="${j}">${cleanItem}</li>`
                              })
                              .join("")

                            // Combine header and list
                            formattedText = `<${headerTag} class="${headerClass} font-bold my-2">${headerText}</${headerTag}><ul class="list-disc pl-5 space-y-1">${listItems}</ul>`

                            return <div key={i} dangerouslySetInnerHTML={{ __html: formattedText }} />
                          }

                          // Process headers within text (=== Header ===)
                          formattedText = formattedText.replace(/===\s*(.+?)\s*===/g, (match, header) => {
                            return `<h3 class="text-lg font-bold my-2">${header}</h3>`
                          })

                          // Process subheaders within text (== Subheader ==)
                          formattedText = formattedText.replace(/==\s*(.+?)\s*==/g, (match, header) => {
                            return `<h2 class="text-xl font-bold my-3">${header}</h2>`
                          })

                          // Check if the text contains list items (lines starting with * or #)
                          if (formattedText.includes("\n* ") || formattedText.includes("\n# ")) {
                            const lines = formattedText.split("\n")
                            let processedHtml = ""
                            let inList = false

                            lines.forEach((line) => {
                              if (line.startsWith("* ") || line.startsWith("# ")) {
                                // Start a list if not already in one
                                if (!inList) {
                                  processedHtml += '<ul class="list-disc pl-5 space-y-1">'
                                  inList = true
                                }
                                // Add list item
                                processedHtml += `<li>${line.substring(2)}</li>`
                              } else {
                                // Close list if we were in one
                                if (inList) {
                                  processedHtml += "</ul>"
                                  inList = false
                                }
                                // Add regular line
                                processedHtml += line + "<br/>"
                              }
                            })

                            // Close list if still open
                            if (inList) {
                              processedHtml += "</ul>"
                            }

                            return <div key={i} dangerouslySetInnerHTML={{ __html: processedHtml }} />
                          }

                          // Process bold text ('''bold''')
                          formattedText = formattedText.replace(/'''(.+?)'''/g, "<strong>$1</strong>")

                          // Process italic text (''italic'')
                          formattedText = formattedText.replace(/''(.+?)''/g, "<em>$1</em>")

                          // Process wiki links ([[link|text]] or [[link]])
                          formattedText = formattedText.replace(/\[\[(.+?)(?:\|(.+?))?\]\]/g, (match, link, text) => {
                            const displayText = text || link
                            const url = link.replace(/\s+/g, "_")
                            return `<a href="https://en.wikivoyage.org/wiki/${url}" class="text-primary hover:underline" target="_blank">${displayText}</a>`
                          })

                          return <div key={i} dangerouslySetInnerHTML={{ __html: formattedText }} />
                        }
                      })}
                    </div>
                    <a
                      href={`https://en.wikivoyage.org/wiki/${title.replace(/\s+/g, "_")}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center mt-4 text-primary hover:underline"
                    >
                      <Globe size={16} className="mr-1" />
                      View on WikiVoyage
                    </a>
                  </div>
                ) : (
                  <div className="whitespace-pre-line text-gray-700 dark:text-gray-300">{openingText}</div>
                )}

                <Button variant="outline" size="sm" onClick={() => toggleExpand(index)} className="mt-4">
                  {isExpanded ? (
                    <>
                      <ChevronUp size={16} className="mr-1" />
                      Hide full text
                    </>
                  ) : (
                    <>
                      <ChevronDown size={16} className="mr-1" />
                      Show full text
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
