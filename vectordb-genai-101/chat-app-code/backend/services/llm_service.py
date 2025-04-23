import os
import logging
from .inference_service import es_chat_completion

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# TODO - this should not be hardcoded
index_source_fields = {
    "nyc_regulations": [
        "semantic_content"
    ]
}


def init_conversation_history():
    # convo = [
    #     {
    #         "role": "user",
    #         "content": "Hi, I have questions about Notary regulations"
    #     },
    #     {
    #         "role": "assistant",
    #         "content": "Sure, I can help with that. What specific questions do you have?"
    #     },
    # ]
    convo = []

    return convo


def create_llm_prompt(question, results, conversation_history):
    """
    Create a prompt for the LLM based on the question, search results, and conversation history provided
    :param question:
    :param results:
    :param conversation_history:
    :return:
    """
    logging.info("Starting to create LLM prompt")
    context = ""
    logging.info(f"Results: {results}")
    for hit in results:
        inner_hit_path = f"{hit['_index']}.{index_source_fields.get(hit['_index'])[0]}"
        ## For semantic_text matches, we need to extract the text from the inner_hits
        if 'inner_hits' in hit and inner_hit_path in hit['inner_hits']:
            context += '\n --- \n'.join(inner_hit['_source']['text'] for inner_hit in hit['inner_hits'][inner_hit_path]['hits']['hits'])
        else:
            source_field = index_source_fields.get(hit["_index"])[0]
            hit_context = hit["_source"][source_field]
            context += f"{hit_context}\n"

    prompt = f"""
    Instructions:

    You are an AI assistant trained to help residents, city employees, and local organizations understand and navigate regulations, policies, and services in New York City.

    Guidelines:

    Audience:
    - Assume the user could be a resident, agency worker, small business owner, or community organizer.
    - Use clear, respectful, and accessible language for all levels of technical understanding.

    Response Structure:
    - **Clarity**: Provide direct, well-structured responses. Use bullet points if listing items.
    - **Factuality**: Only use information from the context provided.
    - **Citations**: Use inline citation format (e.g., [1], [2]) based on the order of the context chunks if applicable.
    - **Markdown**: Format responses using Markdown for lists, bolding, etc.

    Context Usage:
    - Base your answer only on the context and prior conversation history.
    - If the answer isn’t in the context, respond with: _"I'm unable to answer that based on the information provided."_
    - Do not make up information or speculate.
    - Reference relevant details from earlier user questions when appropriate.

    Tone:
    - Friendly, helpful, and professional.
    - Show empathy if the user expresses frustration or confusion.

    Conversation History:
    {conversation_history}

    Context:
    {context}

    User Question:
    {question}

    Respond using only the provided context and conversation history.
    """

    logging.info("Done creating LLM prompt")
    logging.info(f"Full Prompt: {prompt}")
    return prompt


def build_conversation_history(history, user_message, ai_response):
    """
    Function to build converstation history for the LLM
    Keep 2 messages from the user and 2 messages from the AI
    When the count of messages from the user and AI each is greater than 2,
     keep the last 2 messages as is
     make a call to the LLM to summarize the conversation and keep the summary

    Summary is kept in the "system" role

    structure
    [
      {"role": "system", "content": "Conversation summary:  [summary here]"},
      {"role": "user", "content": "2 messages ago"},
      {"role": "assistant", "content": "2 responses ago"},
      {"role": "user", "content": "1 message ago"},
      {"role": "assistant", "content": "1 response ago"}
    ]
    """
    logging.info("Starting to build conversation history function")
    if len(history) < 2:
        logging.info("History is less than 2 messages. Adding new messages to history")
        history.extend([
            {
                "role": "user",
                "content": user_message
            },
            {
                "role": "assistant",
                "content": ai_response
            }
        ])
        return history

    logging.info("History is greater than 4 messages. Summarizing conversation")
    summary_prompt = f"""
You are a conversation summarizer for a public service AI assistant.
Your task is to produce a concise but rich summary of the conversation so far.

Rules:
1. Focus on regulations, city services, or policies the user asked about.
2. Retain specific references to programs, documents, or topics (e.g., congestion pricing, parking permits).
3. Note unresolved or follow-up questions for context continuity.
4. Be precise, structured, and helpful — this summary will guide future answers.

Conversation History:
{history}

New User Message:
{user_message}

New Assistant Response:
{ai_response}

Provide your summary in the following format:
SUMMARY: [A concise but informative summary of the conversation so far.]
KEY TOPICS: [List of specific regulations, policies, services, or departments mentioned.]
USER CONCERNS: [List any user pain points, frustrations, or recurring themes.]
UNRESOLVED QUESTIONS: [List of open items or questions that have not been fully answered.]
"""

    summary = es_chat_completion(summary_prompt, os.getenv("INFERENCE_ID"))
    logging.info(f"LLM Summary of history: {summary}")

    return [
        {
            "role": "system",
            "content": summary
        },
        history[-2],
        history[-1],
        {
            "role": "user",
            "content": user_message
        },
        {
            "role": "assistant",
            "content": ai_response
        }
    ]
