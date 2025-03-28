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
        "rag_context": "source_text",
        "index_name": "wiki-voyage_2025-03-07_e5-embeddings"
    }

def build_query(query_string: str, inner_hits_size:int = None) -> dict:
    """
    Constructs a query DSL for use in Elasticsearch

    Args:
        query_string (str): The search query string. You are not required to use this
        inner_hits_size (int, optional): The size of inner hits. You are not required to use this

    Returns:
        dict: A dictionary representing the search query.
    """

    lexical_query = {
        "query": {
            "multi_match": {
                "query": query_string,
                "fields": [
                    "source_text", 
                    # "title"
                ]
            }
        }
    }



    return lexical_query