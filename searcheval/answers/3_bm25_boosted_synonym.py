



def is_disabled() -> bool:
    return False

def get_parameters() -> dict:
    return {
        "index_name": "star_wars_custom"
    }

def build_query(query_string: str) -> dict:

    return {
        "query": {
            "multi_match": {
                "query": query_string,
                "fields": [
                    "title.with_synonyms^5", 
                    "lore.with_synonyms"
                ],
                "fuzziness": "AUTO"
            }
        }
    }


