import csv
import json
import glob
import os
import importlib.util
import traceback

# from dotenv import load_dotenv
# load_dotenv('.env')

# from utility.util_es import get_es
from utility.util_llm import LLMUtil


openai_api_key = os.getenv("OPENAI_API_KEY")
llm_util = LLMUtil(openai_api_key)


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


def run_evaluation(es, golden_data, strategy_modules):
    results = {}

    ## Search rank Evaluation
    print("\b### SEARCH RANK EVAL")
    for strategy_name, module in strategy_modules.items():

        if hasattr(module, "is_disabled") and module.is_disabled(): ## or strategy_name != "1a_bm25" :
            print(f"Skipping strategy: {strategy_name}")
            continue

        print(f"Starting strategy: {strategy_name}")
        rank_eval_body = _build_rank_eval_request(golden_data, module)
        # print(json.dumps(rank_eval_body, indent=4))

        index_name = module.get_parameters()['index_name']
        
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
    return results




def output_eval_results(output_csv_path, output_json_path, results, golden_data, strategy_modules):
    strategy_names = list(strategy_modules.keys())
    strategy_names.sort()  # Sort the list in ascending order

    # Save results to JSON file
    with open(output_json_path, "w", encoding="utf-8") as json_file:
        json.dump(results, json_file, indent=4)


    # Save results to CSV file
    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        # Header: query plus one column per strategy
        header_row = ["query"] + strategy_names
        writer.writerow(header_row)
        
        # Write each query row
        per_strategy_sums = {s: 0.0 for s in strategy_names}
        per_strategy_counts = {s: 0 for s in strategy_names}
        
        for query_text, row_scores in results.items():
            row_to_write = [query_text]
            for s in strategy_names:
                strat_section = row_scores['scores'].get(s, None)
                score = strat_section.get('ndgc', None) if strat_section is not None else None
                row_to_write.append(score if score is not None else "")
                if score is not None:
                    per_strategy_sums[s] += score
                    per_strategy_counts[s] += 1
            writer.writerow(row_to_write)

        # Write total (avg) row
        total_row = ["Average NDCG Score"] 
        for s in strategy_names:
            if per_strategy_counts[s] > 0:
                avg_score = per_strategy_sums[s] / per_strategy_counts[s]
                total_row.append(avg_score)
            else:
                total_row.append("")
        writer.writerow(total_row)

    print(f"Evaluation complete. Results written to {output_csv_path} and {output_json_path}")

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

        query_string = strategy_module.query_transform(item["query"], llm_util,  strategy_module.get_parameters()["query_transform_prompt"]) if hasattr(strategy_module, "query_transform") else item["query"]

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
            #     "relevant_rating_threshold": 1
            # }
        }
    }
    
    return rank_eval_body



# def main():

#     OUTPUT_CSV = "search_evaluation_results.csv"
#     STRATEGIES_FOLDER = "strategies"       # Folder containing *.py strategy files
#     GOLDEN_DATA_CSV = "golden_data.csv"    # CSV with columns: query, best_ids, natural_answer (or similar)

#     # 1. Connect to Elasticsearch
#     es = get_es()
#     print(f"Connected to Elasticsearch version: {es.info()['version']['number']}")
    
#     # 2. Load the golden data set
#     golden_data = load_golden_data(GOLDEN_DATA_CSV)
#     print(f"Identified {len(golden_data)} golden data entry(ies) to use for search evaluation")
    
#     # 3. Load strategies from the strategies folder
#     strategy_modules = load_strategies(STRATEGIES_FOLDER)  # {name: module}
#     print(f"Identified {len(strategy_modules)} strategy(ies) to evaluate")

#     # 4. Evaluate each strategy
#     results = run_evaluation(es, golden_data, strategy_modules)

#     # 5. Output the evaluation results
#     output_eval_results(OUTPUT_CSV, results, strategy_modules)


    # ## We will store results in a structure like:
    # ## {
    # ##   query_text1: { "bm25": 0.88, "semantic": 0.79, ... },
    # ##   query_text2: { "bm25": 0.92, ... },
    # ##   ...
    # ## }
    # results = {}

    # ## Search rank Evaluation
    # print("\b### SEARCH RANK EVAL")
    # for strategy_name, module in strategy_modules.items():

    #     if hasattr(module, "is_disabled") and module.is_disabled(): ## or strategy_name != "1a_bm25" :
    #         print(f"Skipping strategy: {strategy_name}")
    #         continue

    #     print(f"Starting strategy: {strategy_name}")
    #     rank_eval_body = build_rank_eval_request(golden_data, module)
    #     # print(json.dumps(rank_eval_body, indent=4))

    #     index_name = module.get_parameters()['index_name']
        
    #     # 4. Call the _rank_eval API
    #     try:
    #         response = es.rank_eval(body=rank_eval_body, index=index_name)
    #         # print(response)
    #         ## response structure reference:
    #         ## {
    #         ##   "metric_score": 0.85,   # overall metric
    #         ##   "details": {
    #         ##       "query_1": { "metric_score": 1.0, "unrated_docs": [], ... },
    #         ##       "query_2": { "metric_score": 0.5, ... },
    #         ##       ...
    #         ##   }
    #         ## }

    #         ## Update results
    #         for i, item in enumerate(golden_data):
    #             qid = f"query_{i+1}"
    #             query_text = item["query"]
                
    #             ndcg_for_this_query = response["details"][qid]["metric_score"]
                
    #             if query_text not in results:
    #                 results[query_text] = {}
    #             results[query_text][strategy_name] = ndcg_for_this_query

    #         # print(json.dumps(response, indent=4))
    #     except Exception as e:
    #         print(f"Error running rank_eval for strategy {strategy_name}: {e}")
    #         traceback.print_exc()  
    #         print(json.dumps(rank_eval_body, indent=4))

    #         # Optionally fill with None or 0
    #         for item in golden_data:
    #             query_text = item["query"]
    #             if query_text not in results:
    #                 results[query_text] = {}
    #             results[query_text][strategy_name] = None


    # strategy_names = list(strategy_modules.keys())
    # strategy_names.sort()  # Sort the list in ascending order

    # with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as f:
    #     writer = csv.writer(f)
        
    #     # Header: query plus one column per strategy
    #     header_row = ["query"] + strategy_names
    #     writer.writerow(header_row)
        
    #     # Write each query row
    #     per_strategy_sums = {s: 0.0 for s in strategy_names}
    #     per_strategy_counts = {s: 0 for s in strategy_names}
        
    #     for query_text, row_scores in results.items():
    #         row_to_write = [query_text]
    #         for s in strategy_names:
    #             score = row_scores.get(s, None)
    #             row_to_write.append(score if score is not None else "")
    #             if score is not None:
    #                 per_strategy_sums[s] += score
    #                 per_strategy_counts[s] += 1
    #         writer.writerow(row_to_write)

    #     # Write total (avg) row
    #     total_row = ["TOTAL"]
    #     for s in strategy_names:
    #         if per_strategy_counts[s] > 0:
    #             avg_score = per_strategy_sums[s] / per_strategy_counts[s]
    #             total_row.append(avg_score)
    #         else:
    #             total_row.append("")
    #     writer.writerow(total_row)

    # print(f"Evaluation complete. Results written to {OUTPUT_CSV}")





# if __name__ == "__main__":
#     main()

