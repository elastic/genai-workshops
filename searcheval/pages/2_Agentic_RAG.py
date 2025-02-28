import streamlit as st

from dotenv import load_dotenv

from datetime import datetime, timezone
import asyncio
import json
import os

import random
from typing import List, Union

from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ModelRequest,SystemPromptPart, UserPromptPart

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel

import nest_asyncio
nest_asyncio.apply()

import requests
from io import StringIO
load_dotenv(stream=StringIO(requests.get('http://kubernetes-vm:9000/env').text))

## For Lab Environment
openai_api_key =  os.environ.get("LLM_APIKEY") 
url = os.environ.get("LLM_PROXY_URL") 
openai_api_base = f"https://{url}"

os.environ["OPENAI_API_KEY"] = openai_api_key
os.environ["OPENAI_BASE_URL"] = openai_api_base


# ## For local
# load_dotenv()


st.set_page_config(
    page_title="Agentic RAG App",
    page_icon="🧠",
)


################
## Retrieval Code for RAG
################

from utility.util_es import get_es
from utility.util_llm import LLMUtil, get_llm_util
from utility.util_es import search_to_context
import final_strat as strategy_module

@st.cache_resource
def get_es_client():
    print("Getting ES client ...")
    return get_es()
es = get_es_client()

@st.cache_resource
def get_cached_llm_util():
    print("Getting LLM Util ...")
    return get_llm_util()
llm_util = get_cached_llm_util()

def search_for_knowledge(es, original_query: str) -> str:

    print(f"\033[91mRAG question: {original_query}\033[0m")

    doc_limit = 6
    inner_hits_size = 3
    citation_limit = 9

    rag_system_prompt = """
Instructions:

- You are an assistant for question-answering tasks.
- Answer questions truthfully and factually using only the context presented.
- Do not jump to conclusions or make assumptions.
- If the answer is not present in the provided context, just say that you don't know rather than making up an answer or using your own knowledge from outside the prompt.
- You must always cite the document where the answer was extracted using inline academic citation style [], using the position or multiple positions. Example:  [1][3].
- Use markdown format for code examples or bulleted lists.
- You are correct, factual, precise, and reliable.


Context:
{context}
"""
    
    tokens_used = 0

    ## pre-process the query string
    query_transform_prompt = strategy_module.get_parameters().get("query_transform_prompt", None)
    if query_transform_prompt:
        response = llm_util.transform_query_direct(
            system_prompt=query_transform_prompt, 
            user_query=original_query)
        query_string = response["answer"]
        total_tokens = response["total_tokens"]
        tokens_used += total_tokens
    else:
        query_string = original_query

    ## Do the RAG

    index_name = strategy_module.get_parameters()['index_name']
    body = strategy_module.build_query(query_string, inner_hits_size)
    rag_context = strategy_module.get_parameters().get("rag_context", "lore")
    ## determine if this strategy wants inner hits re-ranked
    rerank_inner_hits = strategy_module.get_parameters().get("rerank_inner_hits", False)

    ## RAG: R retrieval
    retrieval_context  = search_to_context(es, index_name, query_string, body, rag_context, rerank_inner_hits, doc_limit, citation_limit)
    top_context_citations = retrieval_context[:citation_limit]

    context = "\n".join([f"[{i+1}] {text}" for i, text in enumerate(top_context_citations)])

    system_prompt = rag_system_prompt.format(context=context)

    rag_reponse = llm_util.rag_direct(system_prompt, top_context_citations, original_query, should_print=False)
    actual_output = rag_reponse["answer"]
    rag_tokens = rag_reponse["total_tokens"]
    tokens_used += rag_tokens

    print(f"\t\033[91mRAG answer: {actual_output}\033[0m")
    print(f"\t\033[91mTotal tokens used: {tokens_used}\033[0m")

    return actual_output




################
## AGENTs and MODELS
################

tool_tip_inject = None

@st.cache_resource
def get_model():
    print("Getting model ...")
    return OpenAIModel('gpt-4o')
model = get_model()

research_questions = 2


agent_system_prompt = f"""
You are an expert researcher focused on Star Wars lore and trivia. 
Your primary task is to look up factual information using external research tools rather than relying on your own internal knowledge. 
You can make up to {research_questions} research calls on different sub-topics if you wish
Then you will present your findings to the user in concise bullet points using Markdown.

Instructions:
1. **Always rely on external research.** Before answering any Star Wars–related question, consult the available tools for relevant information. 
2. **Use Markdown bullet points** to present facts you’ve discovered through your research.
3. **Only provide facts from your research** — avoid speculation or drawing conclusions beyond what you’ve found.
4. **Do not elaborate or add additional commentary**— just repeat the researched facts in bullet points, and then provide a short concluding statement.
5. **If no information is found,** clearly state that no data was located and prompt the user for clarification.

**Example 1:**
- **User’s question:** “What is the name of the Wookiee home world?”
- **Knowledge from tool:** “The home world of Chewbacca the Wookiee is Kashyyyk.”
- **Example answer:**  
  > I researched the topic and found the following information:  
  > - The Wookiee home world is called Kashyyyk  
  > Therefore, Kashyyyk is the Wookiee homeworld.

**Example 2:**
- **User’s question:** “Who is the ajncnbjusc?”
- **Knowledge from tool:** “No information found about ajncnbjusc.”
- **Example answer:**  
  > I researched the topic but found no information. Please clarify your question or ask another question.

"""


@st.cache_resource
def get_agent():
    agent =  Agent()

    ################
    ## TOOLs
    ################
    print("Configuring tools ...")

    # @agent.tool_plain  
    # def roll_die() -> str:
    #     """Roll a six-sided die and return the result."""
    #     if tool_tip_inject:
    #         tool_tip_inject.info("Rolling a die")
    #     return ic( str(random.randint(1, 6)) )


    @agent.tool_plain
    def search_star_wars(query: str) -> str:
        """Search for knowledge about Star Wars lore and trivia"""
        if tool_tip_inject:
            tool_tip_inject.info("Referring to trivia")
        return search_for_knowledge(es, query)

    return agent

agent = get_agent()



################
## Chat
################
## The part that streams a response from the Agent

def _debug_chat_history(messages: List[ModelMessage], when: Union[str, None]  ):
    if when:
        print(f"######### {when} : Chat History #########")
    
    for message in messages:
        role = message.kind
        content = ""
        for part in message.parts:
            type_name = type(part).__name__
            if part.part_kind == 'tool-call':
                content += f"{type_name}- call made to tool: \033[91m{part.tool_name}\033[0m"
            elif type_name == 'UserPromptPart':
                content += f"{type_name}: \033[92m{part.content}\033[0m"
            else:
                content += f"{type_name}: \033[94m{part.content}\033[0m"
        print(f"{role}: {content}")
        print("")
    print("")


async def prompt_ai(message):

    # ## Streaming version
    # ## Saving this code for a later day. We can use a streaming response from OpenAI, but thrugh a proxy we are getting an error related to 
    # ## https://github.com/pydantic/pydantic-ai/issues/149
    # async with agent.run_stream(message, model=model, message_history=st.session_state.messages) as result: 
    #     async for message in result.stream_text(delta=True):
    #         yield message
    # ## Add user message to chat history
    # st.session_state.messages.extend(result.new_messages())
    # _debug_chat_history(result.new_messages(), None)

    ## non streaming version
    result = agent.run_sync(message, model=model, message_history=st.session_state.messages) 
    _debug_chat_history(result.new_messages(), None)
    yield result.data



        

###############
## Some Utilities
###############

def _gen_system_prompt(prompt: str) -> ModelRequest:
    return ModelRequest(
        parts=[
            SystemPromptPart(
                content=prompt, 
                part_kind='system_prompt')
            ], 
        kind='request'
    )


def _gen_ai_response_obj(response_content: str) -> ModelResponse:
    return ModelResponse(
        parts=[
            TextPart(
                content=response_content, 
                part_kind='text')
            ], 
        timestamp=datetime.now(timezone.utc),  # Current UTC time
        kind='response'
    )

def _gen_user_prompt_obj(prompt: str) -> ModelRequest:
    return ModelRequest(
        parts=[
            UserPromptPart(
                content=prompt, 
                part_kind='user_prompt')
            ], 
        kind='request'
    )


def _is_system_prompt(message: ModelMessage) -> bool:
    return any(part.part_kind == 'system_prompt' for part in message.parts)





###############
## The UI
###############

async def main():

    # col1, col2 = st.columns([0.8, 0.2])
    # with col1:
    st.title("Star Wars Trivia")
    # with col2:
    if st.button("Reset Chat"):
        st.session_state.messages = [
            _gen_system_prompt(agent_system_prompt),
            _gen_ai_response_obj("Welcome to the Star Wars trivia chat! Ask me a question.")
        ]
        st.rerun()


    # Initialize chat history -- https://ai.pydantic.dev/api/messages/
    if "messages" not in st.session_state:
        my_system_prompt = agent_system_prompt

        ## will be an array of the base class ModelMessage
        st.session_state.messages = [_gen_system_prompt(my_system_prompt)]

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:

        ## don't print the system prompts
        if _is_system_prompt(message):
            continue

        role = message.kind
        content = "".join(part.content for part in message.parts if 'tool' not in part.part_kind)

        if role in ["request", "response"] and len(content) > 0:
            with st.chat_message("human" if role == "request" else "ai"):
                st.markdown(content)

    # React to user input
    if prompt := st.chat_input("Ask a Star Wars trivia question:"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)

        # Display assistant response in chat message container ... streaming !
        response_content = ""
        with st.chat_message("ai"):

            message_placeholder = st.empty()  # Placeholder for updating the message
            # Run the async generator to fetch responses
            async for chunk in prompt_ai(prompt):

                response_content += chunk
                # Update the placeholder with the current response content
                message_placeholder.markdown(response_content)

        # Add question and response to chat history
        user_prompt = _gen_user_prompt_obj(prompt)
        st.session_state.messages.append(user_prompt)

        ai_response = _gen_ai_response_obj(response_content)
        st.session_state.messages.append(ai_response)



if __name__ == "__main__":
    asyncio.run(main())