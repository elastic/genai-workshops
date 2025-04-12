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
        "rag_context": "source_text",
        # "rerank_inner_hits": True    ### THIS IS THE BIG NEW THING
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
                            "title"
                        ],
                        # "fuzziness": "AUTO"
                    }
                },
                "must_not": disambiguation
            }
        }
    }




    semantic_query = {
      "query": {
        "bool": {
          "must": {
            "semantic": {
                "field": "source_text_semantic",
                "query": query_string
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
              "standard": semantic_query
            },

            ## Second method
            {
              "standard": lexical_query
            }

          ]
        }
      }


    # return {
    #   "retriever": rrf_retriever,
    #   "_source": ["source_text"],
    # }

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


    return {
      "retriever": {
        "text_similarity_reranker": {
          "retriever": rrf_retriever,
          "field": "source_text",
          "inference_id": "my-elastic-rerank",
          "inference_text": query_string,
          "rank_window_size": 10,
          "min_score": 0.05
        }
      },
      "_source": ["source_text"],
    } 