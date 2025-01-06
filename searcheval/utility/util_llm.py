
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
                  model_name: str = "gpt-4o") -> dict:
        
        return self.cache_helper.rag(system_prompt, retrieval_context, query_string, model_name, self)
        


    def transform_query_cache(self, 
                              question: str, 
                              prompt: str) -> dict:

        return  self.query_transform_cache.transform_query(question, prompt, self)


    def flush_cache(self):
        self.cache_helper._persist_to_disk()
        self.query_transform_cache._persist_to_disk()


    ### Functions to call if you want to avoid the cache

    def transform_query_direct(self, system_prompt: str, user_query: str, model_name: str = "gpt-4o") -> dict:

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

            # Print the total number of tokens used by the model
            total_tokens = completion.usage.total_tokens
            # print(f"Total tokens used: {total_tokens}")

            return {"answer": transformed_query, "total_tokens": total_tokens}
        
        except Exception as e: 
            print(f"General exception encountered: {e}")
            # Decide how you want to handle the error; return original query or raise exception
            return {"answer": user_query, "total_tokens": 0}



    def rag_direct(self, system_prompt: str, retrieval_context: list, query_string: str, model_name: str = "gpt-4o", should_print=True) -> dict:
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

            total_tokens = completion.usage.total_tokens
            # print(f"Total tokens used: {total_tokens}")

            # print(f"RAG question: {query_string}")
            if should_print:
                print(f"\tRAG answer: {rag_answer}")

            return {"answer": rag_answer, "total_tokens": total_tokens}
        
        except Exception as e: 
            print(f"General exception encountered: {e}")
            # Decide how you want to handle the error; return original query or raise exception
            return {"answer": "Unable to return response due to an LLM error", "total_tokens": 0}


singleton_llm_util = LLMUtil()

def get_llm_util() -> LLMUtil:
    return singleton_llm_util