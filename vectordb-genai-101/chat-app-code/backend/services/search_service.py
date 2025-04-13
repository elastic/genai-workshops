from elasticsearch import Elasticsearch
import logging
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Initialize the Elasticsearch client
es_client = Elasticsearch(
    hosts=os.getenv('ES_URL', 'http://kubernetes-vm:9200'),
    # api_key=os.getenv('ES_API_KEY')
    basic_auth=(
        os.getenv('ES_USER', 'elastic'),
        os.getenv('ES_PASSWORD', 'changeme')
    )
)


def perform_es_search(query, index):
    """Performs the Elasticsearch query based on the context type."""
    logging.info(f"Starting Elasticsearch search for query: {query}")

## TODO USERS ENTER QUERY CODE HERE
    es_query = {

    }


    try:
        result = es_client.search(index="nyc_regulations", body=es_query)

    except Exception as e:
        # If generated query fails fallback to backup query
        logging.error(f"Error in Elasticsearch search: {str(e)}")
        raise

    # logging.info(f"elasticsearch results: {result}")
    hits = result["hits"]["hits"]
    logging.info(f"number of hits: {len(hits)}")
    return hits


