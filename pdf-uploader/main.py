import os
import base64
import logging
from elasticsearch import Elasticsearch, helpers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Initialize the Elasticsearch client
es_url = os.getenv('ELASTICSEARCH_URL')
es_user = os.getenv('ELASTICSEARCH_USER')
es_pass = os.getenv('ELASTICSEARCH_PASSWORD')

logging.debug(f'es_url: {es_url}')
logging.debug(f'es_user: {es_user}')

es = Elasticsearch(
    hosts=[es_url],
    basic_auth=(
        es_user,
        es_pass
    ),
    request_timeout=120,
    retry_on_timeout=True,
    max_retries=3
)

index_name = 'nyc_regulations'
pipeline_id = 'attachment'
pdf_dir = 'inputs'

# 1. Delete the old index (if it exists)
if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)

# 2. Create the index with the correct mapping
mapping = {
    "mappings": {
        "properties": {
            "attachment": {
                "properties": {
                    "content": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    }
                }
            },
            "semantic_content": {
                "type": "semantic_text",
                "inference_id": ".elser-2-elasticsearch",
                "model_settings": {
                    "task_type": "sparse_embedding"
                }
            }
        }
    }
}

es.indices.create(index=index_name, body=mapping)

# 3. Create the ingest pipeline (attachment)
pipeline_def = {
    "description": "Extract attachment information",
    "processors": [
        {
            "attachment": {
                "field": "data",
                "remove_binary": True
            }
        },
        {
            "set": {
                "field": "semantic_content",
                "value": "{{attachment.content}}"
            }
        }
    ]
}

es.ingest.put_pipeline(id=pipeline_id, body=pipeline_def)

# 4. Read and encode PDFs
def convert_pdf_to_base64(file_path):
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')

def generate_actions(pdf_dir):
    for filename in os.listdir(pdf_dir):
        if filename.lower().endswith(".pdf"):
            file_path = os.path.join(pdf_dir, filename)
            logging.info(f"Processing file: {file_path}")
            base64_encoded = convert_pdf_to_base64(file_path)
            yield {
                "_op_type": "index",
                "_index": index_name,
                "_source": {
                    "data": base64_encoded
                },
                "pipeline": pipeline_id
            }

# 5. Upload the documents using the ingest pipeline
helpers.bulk(es, generate_actions(pdf_dir))

logging.info("Finished indexing PDF documents.")
