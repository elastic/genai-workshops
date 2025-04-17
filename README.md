# Elastic GenAI Professional Cert Module 6

This is the source code for the the Module 6. In this code we are going to work with Search and RAG evaluation.

## Starting the workshop in Instruqt

```----->```

Follow the instructions in the right hand side of the instruqt window.

```----->```



## Running outside of Instruqt

This code depends on the following inference endpoints existing in your Elasticsearch Instance:


```
PUT _inference/text_embedding/my-e5-endpoint
{
  "service": "elasticsearch",
  "service_settings": {
    "adaptive_allocations": {
      "enabled": true,
      "min_number_of_allocations": 1,
      "max_number_of_allocations": 10
    },
    "num_threads": 1,
    "model_id": ".multilingual-e5-small"
  }
}

PUT /_inference/rerank/my-elastic-rerank
{
  "service": "elasticsearch",
  "service_settings": {
        "num_threads": 1,
        "model_id": ".rerank-v1",
        "adaptive_allocations": {
          "enabled": true,
          "min_number_of_allocations": 1,
          "max_number_of_allocations": 4
        }
      }
}

PUT /_inference/sparse_embedding/my-elser-endpoint
{
      "service": "elser",
      "service_settings": {
        "num_threads": 1,
        "model_id": ".elser_model_2_linux-x86_64",
        "adaptive_allocations": {
          "enabled": true,
          "min_number_of_allocations": 1,
          "max_number_of_allocations": 10
        }
      }
}
```