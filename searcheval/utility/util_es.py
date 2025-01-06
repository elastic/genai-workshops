from elasticsearch import Elasticsearch, helpers, OrjsonSerializer
from elasticsearch import BadRequestError
import os
import json

## attempt to load environment variables
## if they aren't there we'll assume we are in Instruqt and accessing kubernetes-vm
es_host = os.getenv("ES_SERVER", None)
es_api_key = os.getenv("ES_API_KEY", None)

## The singleton Elasticsearch client instance

if es_host and es_api_key:
    print("Using ES with configured Host and API key ...")
    es = Elasticsearch(
        hosts=[f"{es_host}"],
        # basic_auth=(es_username, es_password),
        api_key=es_api_key,
        serializer=OrjsonSerializer(),
        http_compress=True,
        max_retries=10,
        connections_per_node=100,
        request_timeout=120,
        retry_on_timeout=True,
    )
else:
    print("Connecting to ES inside local Kubernetes ...")
    es_host="http://kubernetes-vm:9200"
    es_username="elastic"
    es_password="changeme"
    es = Elasticsearch(
        hosts=[f"{es_host}"],
        basic_auth=(es_username, es_password),
        # api_key=es_api_key,
        serializer=OrjsonSerializer(),
        http_compress=True,
        max_retries=10,
        connections_per_node=100,
        request_timeout=120,
        retry_on_timeout=True,
    )


def get_es() -> Elasticsearch:
    """
    Get the Elasticsearch singleton client instance.

    Returns:
        Elasticsearch: The Elasticsearch client instance.
    """
    return es


def check_and_create_index(es:Elasticsearch, index_name:str, settings:dict, mappings:dict):
    """
    Check if an Elasticsearch index exists, and create it if it does not.

    Parameters:
    es (Elasticsearch): An instance of the Elasticsearch client.
    index_name (str): The name of the index to check or create.
    settings (dict): The settings for the index to be created.
    mappings (dict): The mappings for the index to be created.

    Returns:
    None
    """
    # Check if the index exists
    if not es.indices.exists(index=index_name):
        # Create the index with the settings
        es.indices.create(index=index_name, settings=settings, mappings=mappings)
    else:
        print(f"Index '{index_name}' already exists.")

def check_and_create_synonyms(es:Elasticsearch, synonym_set_name:str, synonym_set:list): 
    """
    Check and create a synonym set in Elasticsearch.

    This function checks if a synonym set exists in Elasticsearch and creates it if it does not.

    Args:
        es (Elasticsearch): An instance of the Elasticsearch client.
        synonym_set_name (str): The name of the synonym set to be created or checked.
        synonym_set (list): A list of synonyms to be included in the synonym set.

    Returns:
        None
    """
    resp = es.synonyms.put_synonym(
        id=synonym_set_name,
        synonyms_set=synonym_set
    )
    print(resp)



def _batchify(docs, batch_size):
    for i in range(0, len(docs), batch_size):
        yield docs[i:i + batch_size]


def bulkLoadIndex( es, json_docs, index_name, id_param, batch_size=10):
    def bulkLoadIndex(es, json_docs, index_name, id_param, batch_size=10):
        """
        Bulk loads JSON documents into an Elasticsearch index.

        Parameters:
        es (Elasticsearch): An instance of the Elasticsearch client.
        json_docs (list): A list of JSON documents to be indexed.
        index_name (str): The name of the Elasticsearch index.
        id_param (str): The key in the JSON documents to be used as the document ID.
        batch_size (int, optional): The number of documents to be processed in each batch. Default is 10.

        Raises:
        BadRequestError: If the specified index does not exist.

        Returns:
        None
        """

    # Create the index with the mapping if it doesn't exist
    if not es.indices.exists(index=index_name):
        raise BadRequestError(f"Index [{index_name}] needs to exist before bulk loading")

    batches = list(_batchify(json_docs, batch_size))

    for batch in batches:
        # Convert the JSON documents to the format required for bulk insertion
        bulk_docs = [
            {
                "_op_type": "index",
                "_index": index_name,
                "_source": doc,
                "_id": doc[id_param]
            }
            for doc in batch
        ]

        # Perform bulk insertion
        success, errors =  helpers.bulk(es, bulk_docs, raise_on_error=False)
        if errors:
            for error in errors:
                print(error)



def search_to_context(es: Elasticsearch, index_name: str, query_string: str, body: dict, rag_context: str, rerank_inner_hits: bool, doc_limit: int, citation_limit: int) -> list:
    """
    Executes a search query on the specified Elasticsearch index and extracts a specific context field from the results.

    Args:
        es (Elasticsearch): An instance of the Elasticsearch client.
        index_name (str): The name of the Elasticsearch index to search.
        body (dict): The search query body.
        rag_context (str): The field name to extract from the search results.
        doc_limit (int): The maximum number of search results to process.
        citation_limit (int): The maximum number of search citations to return.

    Returns:
        list: A list of context values extracted from the search results.
    """
    results = es.search(index=index_name, body=body)

    context = []
    # results['hits']['hits'] is the list of hits returned by Elasticsearch
    
    if rerank_inner_hits:
        results_to_examine = results['hits']['hits'][:doc_limit]
        for hit in results_to_examine:
            inner_hits = hit.get('inner_hits', [])
            if len(inner_hits) > 0:
                for inner_hit  in inner_hits.get(f"{index_name}.{rag_context}", {})["hits"]["hits"]:
                    context_value = inner_hit["_source"].get("text", "")
                    context.append(str(context_value))

        reranked_resp = es.inference.inference(
            task_type="rerank",
            inference_id= "my-elastic-rerank",  #"cohere_rerank"
            input=context,
            query=query_string
        )

        top_results = [item['text'] for item in reranked_resp['rerank'][:citation_limit]]
        return top_results
    else:

        for hit in results['hits']['hits'][:doc_limit]:
        
            inner_hits = hit.get('inner_hits', [])

            if len(inner_hits) > 0:
                # print("inner hits")
                for inner_hit  in inner_hits.get(f"{index_name}.{rag_context}", {})["hits"]["hits"]:
                    # print(json.dumps(inner_hit, indent=2))    
                    context_value = inner_hit["_source"].get("text", "")
                    context.append(str(context_value))
            
            else:
                # print("normal hits")
                
                # Safely get the value in case `rag_context` is missing
                context_value = hit["_source"].get(rag_context, "")
                context.append(str(context_value))


        return context[:citation_limit]
