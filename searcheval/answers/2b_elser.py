

def is_disabled() -> bool:
    return False

def get_parameters() -> dict:
    return {
        "index_name": "star_wars_sem_elser",
        "rag_context": "lore_semantic"
    }

def build_query(query_string: str) -> dict:
    return {
      "retriever": {
        
            
              "standard": {
                "query": {
                  "nested": {
                    "path": "lore_semantic.inference.chunks",
                    "query": {
                      "sparse_vector": {
                        "inference_id": ".elser-2-elasticsearch",
                        "field": "lore_semantic.inference.chunks.embeddings",
                        "query": query_string
                      }
                    },
                    "inner_hits": {
                      "size": 2,
                      "name": "star_wars_sem_elser.lore_semantic",
                      "_source": [
                        "lore_semantic.inference.chunks.text"
                      ]
                    }
                  }
                }
              }
          
      }
    }
    