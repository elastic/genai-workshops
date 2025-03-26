def get_parameters() -> dict:
    """
    Returns a dictionary of parameters for configuring the search strategy

    Returns:
    dict: A dictionary containing the following keys:
        - is_disabled (bool): Indicates whether this search strategy is disabled.
        - index_name (str): The name of the index to be used.
        - query_transform_prompt (str): [OPTIONAL] Instructions for transforming queries.
        - rag_context (str): [OPTIONAL] The field to be used during RAG. defaults to 'lore' if not provided.
        - rerank_inner_hits (bool): Indicates whether to rerank inner hits.
    """
    return {
        "is_disabled": False,
        "index_name": "wiki-voyage_2025-03-07_e5-embeddings",
        "rag_context": "source_text_semantic",
        "rerank_inner_hits": True    ### THIS IS THE BIG NEW THING
    }

    
def build_query(query_string: str, inner_hits_size:int = 3) -> dict:
    return {
      "retriever": {
        "rrf": {
          "retrievers": [
            {
              "standard": {
                "query": {
                  "nested": {
                    "path": "source_text_semantic.inference.chunks",
                    "query": {
                      "knn": {
                        "field": "source_text_semantic.inference.chunks.embeddings",
                        "query_vector_builder": {
                          "text_embedding": {
                            "model_id": "my-e5-endpoint",
                            "model_text": query_string
                          }
                        }
                      }
                    },
                    "inner_hits": {
                      "size": inner_hits_size,
                      "name": "wiki-voyage_2025-03-07_e5-embeddings.source_text_semantic",
                      "_source": [
                        "source_text_semantic.inference.chunks.text"
                      ]
                    }
                  }
                }
              }
            },
            {
              "standard": {
                "query": {
                  "semantic": {
                    "field": "title_semantic",
                    "query": query_string
                  }
                }
              }
            },
            {
              "standard": {
                "query": {
                  "multi_match": {
                    "query": query_string,
                    "fields": [
                      "text",
                      "title"
                    ]
                  }
                }
              }
            }
          ]
        }
      },
      "_source": False
    }