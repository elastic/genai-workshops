from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase



from deepeval.metrics.dag import (
    DeepAcyclicGraph,
    TaskNode,
    BinaryJudgementNode,
    NonBinaryJudgementNode,
    VerdictNode,
)
from deepeval.metrics import DAGMetric

# from utility.PGEval import PGEval
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams

from deepeval.dataset import EvaluationDataset

from deepeval import evaluate

# ## Evaluates whether the answer follows the context
# answer_relevancy_metric = AnswerRelevancyMetric(
#     threshold=0.5,
#     model="gpt-4o",
#     include_reason=True
# )


## Evaluates whether the answer is factual and complete based on the golden answer

# correctness_metric = GEval(
#     name="Correctness",
#     criteria="Determine whether the actual output is factually correct based on the expected output.",
#     # NOTE: you can only provide either criteria or evaluation_steps, and not both
#     evaluation_steps=[
#         "Check whether the facts in 'actual output' contradicts any facts in 'expected output'",
#         "You should also moderately penalize omission of detail",
#         "Vague language, or contradicting OPINIONS, are not OK",
#         "the actual output should have citations in the format [1] and will penalize for lack of citations",
#         "do not check, comment, or penalize whether the expected output has citations"
#     ],
#     evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
#     top_logprobs=5,
# )

correctness_metric = GEval(
    name="Correctness",
    # criteria="Determine whether the actual output is factually correct based on the expected output.",
    # NOTE: you can only provide either criteria or evaluation_steps, and not both
    evaluation_steps=[
        "Check whether the facts in 'actual output' contradicts any facts in 'expected output'",
        "You should heavily penalize when 'actual output' is missin a citation of the format [#]",
        "You should also moderately penalize omission of detail",
        "Vague language, or contradicting OPINIONS, are not OK",
        # "the actual output should have citations in the format [1] and will penalize for lack of citations",
        "do not check, comment, or penalize whether 'expected output' has citations"
    ],
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
    top_logprobs=5,
)



mention_of_no_context_node = BinaryJudgementNode(
    criteria="test whether `citation annotation` is present in the format [#] or [#. #] and not null",
    children=[
        VerdictNode(verdict=False, score=0),
        VerdictNode(verdict=True, child=correctness_metric),
    ],
)

extract_citation_used_node = TaskNode(
    instructions="Extract the citation annotation of format [#] or [#, #] used in the answer `actual_output`, if not ciation is present return null",
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
    output_label="citation annotation",
    children=[mention_of_no_context_node],
)

from deepeval.models import GPTModel
my_dag = DeepAcyclicGraph(root_nodes=[extract_citation_used_node])

citation_correctness = DAGMetric(
    name="Citation Correctness", 
    dag=my_dag, 
    verbose_mode=False,
    # model= GPTModel(model="gpt-4o", temperature= 0.0)
)



def generateLLMTestCase(name:str, query: str, actual_output: str, retrieval_context, correct_answer: str) -> LLMTestCase :
    return  LLMTestCase(
        input=query,
        actual_output=actual_output,
        retrieval_context=retrieval_context,
        expected_output=correct_answer,
        name=name
    )



def evaluateTestCases(testCases): 
    dataset = EvaluationDataset(test_cases=testCases)
    return evaluate(
        test_cases=dataset, 
        metrics=[ citation_correctness],
        print_results=False,
        use_cache=True
    )

