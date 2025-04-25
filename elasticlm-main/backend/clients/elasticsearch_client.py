# backend/clients/elasticsearch_client.py

from elasticsearch import AsyncElasticsearch
from config import settings
from utils.logger import logger
from elasticsearch import AuthenticationException, ConnectionError

# Initialize Elasticsearch client with API Key only
try:
    es = AsyncElasticsearch(
        hosts=[settings.ES_URL],
        api_key=settings.ES_API_KEY,
        verify_certs=True,  # Ensure SSL certificates are verified in production
        ssl_show_warn=False,
    )
    logger.info("Elasticsearch client initialized successfully with API Key.")
except AuthenticationException as ae:
    logger.error(f"Authentication failed while initializing Elasticsearch client: {ae}")
    raise
except ConnectionError as ce:
    logger.error(f"Connection error while initializing Elasticsearch client: {ce}")
    raise
except Exception as e:
    logger.error(f"Unexpected error during Elasticsearch client initialization: {e}")
    raise

CHAT_INDEX = "elastic_lm_chats"
# USER_INDEX = "elastic_lm_users"

USER_DOCS_TEMPLATE = {
    "mappings": {
        "properties": {
            "user_id": {"type": "keyword"},
            "chat_id": {"type": "keyword"},
            "messages": {
                "type": "nested",
                "properties": {
                    "role": {"type": "keyword"},
                    "content": {"type": "text"},
                    "timestamp": {"type": "date"}
                }
            },
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
            "semantic_text": {
                "inference_id": ".elser-2-elasticsearch",
                "type": "semantic_text"
            },
            "file_name": {
                "type": "keyword"
            },
            "source": {"type": "keyword"},
            "text": {
                "copy_to": "semantic_text",
                "type": "text"
            },
            "timestamp": {"type": "date"}
        }

    }
}

async def create_user_docs_index():
    index_name = "elastic_lm_docs"
    try:
        exists = await es.indices.exists(index=index_name)
        if not exists:
            await es.indices.create(index=index_name, body=USER_DOCS_TEMPLATE)
            logger.info(f"Created Elasticsearch index: {index_name}")
        else:
            logger.debug(f"Elasticsearch index already exists: {index_name}")
    except AuthenticationException as ae:
        logger.error(f"Authentication failed while creating Elasticsearch docs index '{index_name}': {ae}")
        raise
    except ConnectionError as ce:
        logger.error(f"Connection error while creating Elasticsearch docs index '{index_name}': {ce}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while creating Elasticsearch docs index '{index_name}': {e}")
        raise

async def create_elastic_lm_chats_index():
    index_name = CHAT_INDEX
    mapping = {
        "mappings": {
            "properties": {
                "user_id": {"type": "keyword"},
                "chat_id": {"type": "keyword"},
                "messages": {
                    "type": "nested",
                    "properties": {
                        "role": {"type": "keyword"},
                        "content": {"type": "text"},
                        "timestamp": {"type": "date"}
                    }
                },
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"}
            }
        }
    }

    try:
        exists = await es.indices.exists(index=index_name)
        if not exists:
            await es.indices.create(index=index_name, body=mapping)
            logger.info(f"Created Elasticsearch chat index: {index_name}")
        else:
            logger.debug(f"Elasticsearch chat index already exists: {index_name}")
    except AuthenticationException as ae:
        logger.error(f"Authentication failed while creating Elasticsearch chat index '{index_name}': {ae}")
        raise
    except ConnectionError as ce:
        logger.error(f"Connection error while creating Elasticsearch chat index '{index_name}': {ce}")
        raise
    except ElasticsearchException as ee:
        logger.error(f"Elasticsearch exception while creating Elasticsearch chat index '{index_name}': {ee}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while creating Elasticsearch chat index '{index_name}': {e}")
        raise

async def initialize_indices():
    # await create_elastic_lm_users_index()
    await create_elastic_lm_chats_index()
    # If you have a default user or specific logic, adjust accordingly
    # For example, creating an index for "batman2" if needed
