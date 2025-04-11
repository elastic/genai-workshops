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



    disambiguation = {
        "terms": {
          # "category": ["Disambiguation","Outline articles"]
          "category": ["Disambiguation"]
        }
    }


    lexical_query = {
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "query": query_string,
                        "fields": [
                            "source_text", 
                            # "title"
                        ],
                        "fuzziness": "AUTO",
                    }
                },
                "must_not": disambiguation
            }
        }
    }


    nested_semantic_query ={
      "query": {
        "bool": {
          "must": {
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
          },
          "must_not": disambiguation
        }
      }
    }

    rrf_retriever = {
        "rrf": { ## This stands for Reciprocal Rank Fusion 🔥🔥🔥
          "retrievers": [
            
            ## First method
            {
              "standard": nested_semantic_query
            },

            ## Second method
            {
              "standard": lexical_query
            }

          ]
        }
      }


    return {
      "retriever": rrf_retriever,
      "_source": False
    }

    # return {
    #   "retriever": {
    #     "text_similarity_reranker": {
    #       "retriever": rrf_retriever,
    #       "field": "source_text",
    #       "inference_id": "my-elastic-rerank",
    #       "inference_text": query_string,
    #       "rank_window_size": 10,
    #       "min_score": 0.05
    #     }
    #   },
    #   "_source": False
    # } 


    # return {
    #   "retriever": {
    #     "text_similarity_reranker": {
    #       "retriever": { "standard": nested_semantic_query },
    #       "field": "source_text",
    #       "inference_id": "my-elastic-rerank",
    #       "inference_text": query_string,
    #       "rank_window_size": 10,
    #       "min_score": 0.05
    #     }
    #   },
    #   "_source": False
    # } 