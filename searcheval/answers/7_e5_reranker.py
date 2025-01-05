from utility.util_llm import LLMUtil
from utility.util_query_transform_cache import transform_query as cached_transform_query


def is_disabled() -> bool:
    return False

# "Given the following question, rephrase the question to be a simple standalone question in English. Keep the answer to a single sentence. Do not use quotes.",

def get_parameters() -> dict:
    return {
        "index_name": "star_wars_sem_e5",
        "query_transform_prompt": """Instructions:

- you are an assistant that interprets questions for use in an information retrieval system
- most questions should be left unmodified
- however if the question has major sections that are unimportant to the question or if the question needs simplifying rephrase the question to a single sentence
- Do not use quotes.
        """,
        "rag_context": "lore_semantic",
        "rerank_inner_hits": True
    }


def query_transform(query_string: str, llm_util, prompt:str) -> str:
    
    transformed_query = cached_transform_query(query_string, prompt, llm_util)

    # print(f'Original Question: {query_string}\n\tRewritten Question: {transformed_query}')
    return transformed_query


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
                  "title",
                  "lore"
                ],
                #"fuzziness": 1
              }
            }
          }
        }
      ]
    }
  },
  "_source": False,
  "size": 10
}
