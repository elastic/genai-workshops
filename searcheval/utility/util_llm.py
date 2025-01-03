
import openai

from utility.util_llm_rag_cache import LLMRagCache


class LLMUtil:
    def __init__(self, openai_api_key: str):
        # Set your OpenAI API key
        openai.api_key = openai_api_key
        self.cache_helper = LLMRagCache()

    def transform_query(self, system_prompt: str, user_query: str, model_name: str = "gpt-4o") -> str:
        """
        Calls OpenAI ChatGPT (e.g., GPT-4) to transform the user_query
        using the system_prompt as context. Returns the model's text response.
        """
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

    def rag_cache(self, 
                  system_prompt: str, 
                  retrieval_context: list, 
                  query_string: str, 
                  model_name: str = "gpt-4o") -> str:
        
        return self.cache_helper.rag(system_prompt, retrieval_context, query_string, model_name, self)


    def rag(self, system_prompt: str, retrieval_context: list, query_string: str, model_name: str = "gpt-4o") -> str:
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

            print(f"question: {query_string}")
            print(f"\t{rag_answer}")

            return rag_answer
        
        except Exception as e: 
            print(f"General exception encountered: {e}")
            # Decide how you want to handle the error; return original query or raise exception
            return "Unable to return response due to an LLM error"