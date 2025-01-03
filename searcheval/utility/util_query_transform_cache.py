import json
import os
import atexit
import hashlib
from collections import OrderedDict

CACHE_FILE_PATH = "query_transform_cache.json"
MAX_CACHE_SIZE = 1000  # Adjust to your desired capacity


class QueryTransformCache:
    """
    A simple LRU cache for storing (prompt + question) -> LLM transform results.
    Persists and loads its state from disk as JSON.
    """
    def __init__(self, cache_file_path: str = CACHE_FILE_PATH, max_size: int = MAX_CACHE_SIZE):
        self.cache_file_path = cache_file_path
        self.max_size = max_size
        self.cache = OrderedDict()  # key=hash, value={ 'prompt', 'question', 'answer' }
        
        # Load cache from disk on startup
        self._load_from_disk()

        # Register exit handler to persist cache on program exit
        atexit.register(self._persist_to_disk)

    def transform_query(self, question: str, prompt: str, llm_util) -> str:
        """
        Return a cached transform if available; otherwise call the LLM,
        cache the result, and return it.
        """
        cache_key = self._make_key(prompt, question)

        # LRU Cache Check
        if cache_key in self.cache:
            # print("\t\tCache Hit")
            # Move to end (most recently used)
            self.cache.move_to_end(cache_key, last=True)
            return self.cache[cache_key]["answer"]
        else:
            # print("\t\tCache Miss")
            # Generate a new answer via LLM
            answer = llm_util.transform_query(system_prompt=prompt, user_query=question)

            # Insert into cache
            self.cache[cache_key] = {
                "prompt": prompt,
                "question": question,
                "answer": answer
            }
            self.cache.move_to_end(cache_key, last=True)

            # Enforce max size (LRU eviction)
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)  # pop the least recently used item

            return answer

    def _make_key(self, prompt: str, question: str) -> str:
        """
        Create a repeatable hash from the prompt + question.
        """
        raw_text = f"{prompt}||{question}"
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
                print(f"[QueryTransformCache] Warning: Could not load cache from disk: {e}")
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
            print(f"[QueryTransformCache] Error: Could not persist cache to disk: {e}")


# Singleton-like pattern, if you prefer a single instance:
transform_cache = QueryTransformCache()


def transform_query(question: str, prompt: str, llm_util):
    """
    Convenience function that uses the module-level 'transform_cache' instance.
    """
    return transform_cache.transform_query(question, prompt, llm_util)


def close_cache():
    """
    If you want to manually persist the cache instead of only at exit,
    you can call this function to persist right away.
    """
    transform_cache._persist_to_disk()
