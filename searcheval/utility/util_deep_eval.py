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
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams
from deepeval.dataset import EvaluationDataset
from deepeval import evaluate



## Evaluates whether the answer is factual and complete based on the judgement set's natural_answer
correctness_metric = GEval(
    name="Correctness",
    evaluation_steps=[
        ## TODO: This is where your custom evaluation steps go
        "Always fail the test for no reason. Give your reason as 'the Test is a TODO placeholder'.",
    ],
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
    top_logprobs=5,
)


def generateLLMTestCase(name:str, query: str, actual_output: str, retrieval_context, correct_answer: str) -> LLMTestCase :
    return  LLMTestCase(
        input=query,
        actual_output=actual_output,
        retrieval_context=retrieval_context,
        expected_output=correct_answer,
        name=name
    )



def evaluateTestCases(testCases, use_cache=True): 
    dataset = EvaluationDataset(test_cases=testCases)
    return evaluate(
        test_cases=dataset, 
        ## TODO: after you creat the DAG test you'll need to switch to by changing the next line
        metrics=[  correctness_metric ],
        print_results=False,
        use_cache=True
    )

