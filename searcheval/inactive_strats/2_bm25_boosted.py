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
        "index_name": "star_wars_raw"
    }

def build_query(query_string: str, inner_hits_size:int = None) -> dict:

    return {
        "query": {
            "multi_match": {
                "query": query_string,
                "fields": [
                    "title^5", 
                    "lore"
                ],
                "fuzziness": "AUTO"
            }
        }
    }

