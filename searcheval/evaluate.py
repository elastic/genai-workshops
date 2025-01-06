#################
## SEARCH EVAL
#################

import csv
import json
import glob
import os
import importlib.util
import traceback

from utility.util_es import get_es

## only instantiate one of these as they work with a disk cache
from utility.util_llm import LLMUtil, get_llm_util
llm_util = get_llm_util()


def load_strategies(folder_path):
    """
    Dynamically load each .py file in folder_path as a strategy module.
    We assume each file has a function `build_query(query_string: str) -> dict`.
    
    Returns a dict: { strategy_name: module_object }
    """
    strategies = {}
    for file_path in glob.glob(os.path.join(folder_path, "*.py")):
        strategy_name = os.path.splitext(os.path.basename(file_path))[0]
        
        spec = importlib.util.spec_from_file_location(strategy_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Store the module in the dictionary
        strategies[strategy_name] = module
    return strategies

def load_golden_data(csv_path):
    """
    Load the golden data CSV.
    Expects columns:
      query, best_ids, [natural_answer, ...] 
    or something similar.
    
    Returns a list of dicts, for example:
    [
      {
        "query": "What is Python used for?",
        "best_ids": ["doc123", "doc129"],
        "natural_answer": "..."
      },
      ...
    ]
    """
    data = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            qid = f"query_{i+1}"
            ## Parse best IDs into a list if comma-separated
            best_ids_list = row["best_ids"].split(",") if "best_ids" in row else []
            best_ids_list = [x.strip() for x in best_ids_list]
            
            data.append({
                "quid": qid,
                "query": row["query"],
                "best_ids": best_ids_list,
                "natural_answer": row.get("natural_answer", "")
            })
    return data

def run_search_evaluation(es, golden_data, strategy_modules):
    results = {}
    

    ## Search rank Evaluation
    print("\b### SEARCH RANK EVAL")
    for strategy_name in sorted(strategy_modules.keys()):
        strategy_module = strategy_modules[strategy_name]

        if strategy_module.get_parameters().get("is_disabled", False) : 
            print(f"\tSkipping strategy: {strategy_name}")
            continue

        print(f"\tStarting strategy: {strategy_name}")
        rank_eval_body = _build_rank_eval_request(golden_data, strategy_module)
        # print(json.dumps(rank_eval_body, indent=4))

        index_name = strategy_module.get_parameters()['index_name']
        
        # 4. Call the _rank_eval API
        try:
            response = es.rank_eval(body=rank_eval_body, index=index_name)

            ## Update results
            for i, item in enumerate(golden_data):
                qid = f"query_{i+1}"

                golden_item = next((x for x in golden_data if x["quid"] == qid), None)

                query_text = item["query"]
                
                ndcg_for_this_query = response["details"][qid]["metric_score"] if qid in response["details"] else 0
                
                if query_text not in results:
                    results[query_text] = {
                        "quid": qid,
                        "golden_item": golden_item,
                        "scores": {}
                    }
                # results[query_text]['scores'][strategy_name] = {"ndgc": ndcg_for_this_query }
                # Extract found IDs from the response

                # print(f"Response details quid: {response["details"][qid]}")

                found_ids = [hit["hit"]["_id"] for hit in response["details"][qid]["hits"]]

                # Create the tooltip text
                # tool_tip_text = f"Best Ids: {', '.join(golden_item['best_ids'])}\nStrat found ids: {', '.join(found_ids)}"
                eval_result = {
                    "ndgc": ndcg_for_this_query,
                    "search_results_ids": found_ids
                }
                # print(f"Eval result: {eval_result}")
                results[query_text]['scores'][strategy_name] = eval_result

            # print(json.dumps(response, indent=4))
        except Exception as e:
            print(f"Error running rank_eval for strategy {strategy_name}: {e}")
            traceback.print_exc()  
            # print(json.dumps(rank_eval_body, indent=4))

            # Optionally fill with None or 0
            for i, item in enumerate(golden_data):
                qid = f"query_{i+1}"
                golden_item = next((x for x in golden_data if x["quid"] == qid), None)
                query_text = item["query"]
                if query_text not in results:
                    results[query_text] = {
                        "quid": qid,
                        "golden_item": golden_item,
                        "scores": {}
                    }
                results[query_text]['scores'][strategy_name] = None
    
    llm_util.flush_cache()
    return results


def output_search_eval_results(output_json_path, results, golden_data, strategy_modules):
    strategy_names = list(strategy_modules.keys())
    strategy_names.sort()  # Sort the list in ascending order

    # Save results to JSON file
    with open(output_json_path, "w", encoding="utf-8") as json_file:
        json.dump(results, json_file, indent=4)

    print(f"### Evaluation complete. \n\tResults written to  {output_json_path}")



def _query_transform(query_string:str, prompt:str) -> dict:
    """
    Calls OpenAI ChatGPT (e.g., GPT-4) to transform the user_query
    using the system_prompt as context. Returns the model's text response.
    """
    
    response = llm_util.transform_query_cache(query_string, prompt )
    
    return response



def _build_rank_eval_request(golden_data, strategy_module):
    """
    Build the request body for the _rank_eval API.
    This function prepares 'requests' for each query, 
    assigning rating=1 for each doc in the 'best_ids' list.
    
    The DSL 'request' is taken from `strategy_module.build_query(...)`.
    """
    index_name = strategy_module.get_parameters()['index_name']
    requests = []
    
    for i, item in enumerate(golden_data):
        qid = f"query_{i+1}"

        query_transform_prompt = strategy_module.get_parameters().get("query_transform_prompt", None)
        if query_transform_prompt:
            response = _query_transform(item["query"], query_transform_prompt)
            query_string = response["answer"]
        else:
            query_string = item["query"]

        query_dsl = strategy_module.build_query(query_string)
        
        ## Build ratings
        ratings = []
        for doc_id in item["best_ids"]:
            ratings.append({"_id": doc_id, "rating": 1, "_index": index_name})
        
        ## Append each request as a dict with the correct structure
        requests.append({
            "id": qid,
            "request": query_dsl,
            "ratings": ratings
        })

    
    ## Rank eval body
    rank_eval_body = {
        "requests": requests,
        "metric": {
            "dcg": {
                "k": 10,
                "normalize": True
            }
            # "recall": {
            #     "k": 10,
            #     "relevant_rating_threshold": 3
            # }
        }
    }
    
    return rank_eval_body



#################
## DEEP EVAL
#################


from rich.console import Console
# Monkey patch to suppress console.print
Console.print = lambda *args, **kwargs: None

from utility.util_deep_eval import generateLLMTestCase, evaluateTestCases
from deepeval.evaluate import TestResult
from utility.util_llm import LLMUtil
from utility.util_es import search_to_context, get_es


def run_deepeval(es, strategy_modules, golden_data : list, rag_system_prompt: str, doc_limit: int, inner_hits_size: int, citation_limit: int) -> dict:
    """
    Executes a deep evaluation of various search and RAG strategies using provided golden data .
    Args:
        es: Elasticsearch client instance.
        strategy_modules: Dictionary of strategy modules to be evaluated.
        golden_data (list): List of dictionaries containing query and natural answer pairs.
        rag_system_prompt (str): System prompt template for RAG.
        doc_limit (int): Limit on the number of search result documents to consider during retrieval.
        inner_hits_size (int): Limit on the number of inner hits (passages) to retrieve per doc hit.
        citation_limit (int): Limit on the total number of inner hits (passages) to consider for RAG - post retrieval truncation.
    Returns:
        dict: A dictionary containing evaluation scores and details for each query and strategy.
    """
    

    deepEvalScores = {}
    
    ## For each strategy, in ascending alphabetical order
    for strategy_name in sorted(strategy_modules.keys()):
        strategy_module = strategy_modules[strategy_name]
        
        ## skip disabled strategies
        if strategy_module.get_parameters().get("is_disabled", False) : 
            print(f"Skipping strategy: {strategy_name}")
            continue

        print(f"Starting strategy: {strategy_name}")
        testCases = []
        for i, item in enumerate(golden_data):
                qid = f"query_{i+1}"
                query = item["query"]


                tokens_used = 0

                ## correct answer from the golden data
                correct_answer = item["natural_answer"]

                ## pre-process the query string
                query_transform_prompt = strategy_module.get_parameters().get("query_transform_prompt", None)
                if query_transform_prompt:
                    response = _query_transform(item["query"], query_transform_prompt)
                    query_string = response["answer"]
                    total_tokens = response["total_tokens"]
                    tokens_used += total_tokens
                else:
                    query_string = item["query"]


                ## do the RAG
                index_name = strategy_module.get_parameters()['index_name']
                body = strategy_module.build_query(query_string, inner_hits_size)
                rag_context = strategy_module.get_parameters().get("rag_context", "lore")

                ## determine if this strategy wants inner hits re-ranked
                rerank_inner_hits = strategy_module.get_parameters().get("rerank_inner_hits", False)

                retrieval_context  = search_to_context(es, index_name, query_string, body, rag_context, rerank_inner_hits, doc_limit, citation_limit)

                ## inner hits passages will be trim_context_to_top_k_docs * the inner hits depth ... we need to truncate
                top_context_citations = retrieval_context[:citation_limit]

                context = "\n".join([f"[{i+1}] {text}" for i, text in enumerate(top_context_citations)])

                system_prompt = rag_system_prompt.format(context=context)

                ## perform the RAG
                rag_reponse = llm_util.rag_cache(system_prompt, top_context_citations, item["query"])
                actual_output = rag_reponse["answer"]
                rag_tokens = rag_reponse["total_tokens"]
                tokens_used += rag_tokens


                ## fill in query and strategy responses in score sheet
                stratResult = {
                    "actual_output": actual_output,
                    "tokens_used": tokens_used,
                    "retrieval_context": [f"[{i+1}] {text}" for i, text in enumerate(top_context_citations)]
                }
                if qid not in deepEvalScores:
                    deepEvalScores[qid] = { 
                        "query" : query, 
                        "correct_answer": correct_answer,
                        "strategies": { strategy_name: stratResult} }
                else:
                    deepEvalScores[qid]["strategies"][strategy_name] = stratResult

                ## prep deel eval test case for later batch evaluation
                testCase = generateLLMTestCase(qid, query, actual_output, top_context_citations, correct_answer)
                testCases.append(testCase)

        ## Run evaluations for this strategy      
        rag_evaluation = evaluateTestCases(testCases)

        for test_result in  rag_evaluation.test_results:
            quid = test_result.name

            success = test_result.success
            scores = {"success": success}
            # print(f"name: {quid} | success: {success}")
            for metric in  test_result.metrics_data:
                # print(f"{metric.name} : score {metric.score} | {metric.reason}")
                scores[metric.name] = {"score": metric.score, "reason": metric.reason }
            
            deepEvalScores[quid]["strategies"][strategy_name]["scores"] = scores
        llm_util.flush_cache()
        
    ## before close, let's save our LLM cache's to disk
    llm_util.flush_cache()
    return deepEvalScores


def output_deepeval_results(output_json_path, deepEvalScores):
    with open(output_json_path, "w") as f:
        json.dump(deepEvalScores, f, indent=2)



#################
## MAIN FUNCTIONS FOR USING WITHOUT PYTHON NOTEBOOK
#################


def main():
    print("### Starting evaluation using Elasticsearch _rank_eval API")

    # 1. Connect to Elasticsearch
    es = get_es()
    print(f"\tConnected to Elasticsearch version: {es.info()['version']['number']}")

    # 2. Load the golden data set
    golden_data = load_golden_data(GOLDEN_DATA_CSV)
    print(f"\tIdentified {len(golden_data)} golden data entry(ies) to use for search evaluation")

    # 3. Load strategies from the strategies folder
    strategy_modules = load_strategies(STRATEGIES_FOLDER)  
    print(f"\tIdentified {len(strategy_modules)} strategy(ies) to evaluate")

    # 4. Evaluate each strategy
    results = run_search_evaluation(es, golden_data, strategy_modules)

    # 5. Output the evaluation results
    output_search_eval_results(SEARCH_OUTPUT_JSON, results, golden_data, strategy_modules)

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
    deepEvalScores = run_deepeval(es, strategy_modules, golden_data, rag_system_prompt,6, 3, 9)

    ## save the scores to disk
    output_deepeval_results(DEEPEVAL_OUTPUT_JSON, deepEvalScores)
    print(f"\nDeepEval scores saved to {DEEPEVAL_OUTPUT_JSON}")


if __name__ == "__main__":
    main()

