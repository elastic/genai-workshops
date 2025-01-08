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
        "index_name": "star_wars_sem_e5",
        "query_transform_prompt": """Instructions:

    - you are an assistant that interprets questions for use in an information retrieval system
    - most questions should be left unmodified
    - however if the question has major sections that are unimportant to the question or if the question needs simplifying rephrase the question to a single sentence
    - Do not use quotes.
        """,
        "rag_context": "lore_semantic",
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
                    "path": "lore_semantic.inference.chunks",
                    "query": {
                      "knn": {
                        "field": "lore_semantic.inference.chunks.embeddings",
                        "query_vector_builder": {
                          "text_embedding": {
                            "model_id": ".multilingual-e5-small-elasticsearch",
                            "model_text": query_string
                          }
                        }
                      }
                    },
                    "inner_hits": {
                      "size": inner_hits_size,
                      "name": "star_wars_sem_e5.lore_semantic",
                      "_source": [
                        "lore_semantic.inference.chunks.text"
                      ]
                    }
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
                      "title",
                      "lore"
                    ],
                    
                  }
                }
              }
            }
          ]
        }
      },
      "_source": False
    }