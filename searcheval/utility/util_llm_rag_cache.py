import json
import os
import atexit
import hashlib
from collections import OrderedDict

CACHE_FILE_PATH = "./.caches/.rag_cache.json"
MAX_CACHE_SIZE = 1000  # Adjust to your desired capacity


class LLMRagCache:
    """
    A simple LRU cache for storing responses from rag(...) calls.
    Cache key is derived from:
       system_prompt || retrieval_context || query_string || model_name

    Persists and loads its state from disk as JSON.
    """
    def __init__(self, cache_file_path: str = CACHE_FILE_PATH, max_size: int = MAX_CACHE_SIZE):
        self.cache_file_path = cache_file_path
        self.max_size = max_size
        # key -> { 'system_prompt', 'retrieval_context', 'query_string', 'model_name', 'answer' }
        self.cache = OrderedDict()
        
        # Load cache from disk on startup
        self._load_from_disk()

        # Register exit handler to persist cache on program exit
        atexit.register(self._persist_to_disk)

    def rag(self, system_prompt: str, retrieval_context: list, query_string: str, 
            model_name: str, llm_util) -> dict:
        """
        Return a cached response if available; otherwise call llm_util.rag(...),
        cache the result, and return it.
        """
        cache_key = self._make_key(system_prompt, retrieval_context, query_string, model_name)

        # LRU Cache Check
        if cache_key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(cache_key, last=True)
            cache_hit = self.cache[cache_key]
            return {
                "answer": cache_hit["answer"], 
                "total_tokens": cache_hit["total_tokens"] 
            }
        else:
            # Generate a new answer via the LLM utility
            direct_response = llm_util.rag_direct(
                system_prompt=system_prompt, 
                retrieval_context=retrieval_context, 
                query_string=query_string, 
                model_name=model_name
            )

            # Insert into cache
            self.cache[cache_key] = {
                # "system_prompt": system_prompt,
                # "retrieval_context": retrieval_context,
                # "query_string": query_string,
                # "model_name": model_name,
                "answer": direct_response["answer"],
                "total_tokens": direct_response["total_tokens"]
            }
            self.cache.move_to_end(cache_key, last=True)

            # Enforce max size (LRU eviction)
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)  # pop the least recently used item

            return direct_response

    def _make_key(self, system_prompt: str, retrieval_context: list, 
                  query_string: str, model_name: str) -> str:
        """
        Create a repeatable hash from the provided parameters.
        """
        # Convert retrieval_context to a JSON string (deterministic ordering)
        rc_json = json.dumps(retrieval_context, sort_keys=True)
        raw_text = f"{system_prompt}||{rc_json}||{query_string}||{model_name}"
        return hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    def _load_from_disk(self):
        """
        Load the cache state from disk (JSON) if it exists.
        """
        if os.path.isfile(self.cache_file_path):
            try:
                with open(self.cache_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Convert the loaded dictionary into an OrderedDict
                self.cache = OrderedDict(data)
            except Exception as e:
                print(f"[LLMRagCache] Warning: Could not load cache from disk: {e}")
                self.cache = OrderedDict()
        else:
            # No cache file yet
            self.cache = OrderedDict()

    def _persist_to_disk(self):
        """
        Write the current cache state to disk in JSON format.
        Called automatically on interpreter exit (via `atexit`).
        """
        try:
            # Convert our OrderedDict to a regular dict for JSON dumping
            data_to_save = dict(self.cache)
            with open(self.cache_file_path, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[LLMRagCache] Error: Could not persist cache to disk: {e}")


