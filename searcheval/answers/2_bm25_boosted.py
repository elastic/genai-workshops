def get_parameters() -> dict:
    return {
        "is_disabled": False,
        "index_name": "star_wars_custom"
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

