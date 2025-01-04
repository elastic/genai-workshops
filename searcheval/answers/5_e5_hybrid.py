


def is_disabled() -> bool:
    return False

def get_parameters() -> dict:
    return {
        "index_name": "star_wars_sem_e5",
        "rag_context": "lore_semantic"
    }

def build_query(query_string: str) -> dict:

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
                  "size": 3,
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
                  "title^5",
                  "lore"
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
