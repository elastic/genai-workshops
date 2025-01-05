
import openai

from utility.util_llm_rag_cache import LLMRagCache
from utility.util_query_transform_cache import QueryTransformCache


## only instantiate one of these.  use the get_llm_util() function to get the singleton.  It isn't thread safe.

class LLMUtil:
    def __init__(self):
        ## This code assumes that both OPENAI_API_KEY and optionally OPENAI_BASE_URL 
        ## are already set in the python envionrment with os.environ or load_dotenv
        self.cache_helper = LLMRagCache()
        self.query_transform_cache = QueryTransformCache()

    
    ### Functions to call if you are working with cached inferences

    def rag_cache(self, 
                  system_prompt: str, 
                  retrieval_context: list, 
                  query_string: str, 
                  model_name: str = "gpt-4o") -> str:
        
        return self.cache_helper.rag(system_prompt, retrieval_context, query_string, model_name, self)


    def transform_query_cache(self, 
                              question: str, 
                              prompt: str) -> str:

        return self.query_transform_cache.transform_query(question, prompt, self)


    def flush_cache(self):
        self.cache_helper._persist_to_disk()
        self.query_transform_cache._persist_to_disk()


    ### Functions to call if you want to avoid the cache

    def transform_query_direct(self, system_prompt: str, user_query: str, model_name: str = "gpt-4o") -> str:

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_query}
        ]

        try:
            completion = openai.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.0  # or any other temperature you prefer
            )

            # Extract the content of the first (and typically only) completion
            transformed_query = completion.choices[0].message.content.strip()
            return transformed_query
        
        except Exception as e: 
            print(f"General exception encountered: {e}")
            # Decide how you want to handle the error; return original query or raise exception
            return user_query



    def rag_direct(self, system_prompt: str, retrieval_context: list, query_string: str, model_name: str = "gpt-4o") -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": query_string}
        ]

        try:
            completion = openai.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.0  # or any other temperature you prefer
            )

            # Extract the content of the first (and typically only) completion
            rag_answer = completion.choices[0].message.content.strip()

            # print(f"RAG question: {query_string}")
            print(f"\tRAG answer: {rag_answer}")

            return rag_answer
        
        except Exception as e: 
            print(f"General exception encountered: {e}")
            # Decide how you want to handle the error; return original query or raise exception
            return "Unable to return response due to an LLM error"


singleton_llm_util = LLMUtil()

def get_llm_util() -> LLMUtil:
    return singleton_llm_util