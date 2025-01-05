from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

from utility.PGEval import PGEval
from deepeval.test_case import LLMTestCaseParams

from deepeval.dataset import EvaluationDataset

from deepeval import evaluate

## Evaluates whether the answer follows the context
answer_relevancy_metric = AnswerRelevancyMetric(
    threshold=0.5,
    model="gpt-4o",
    include_reason=True
)


## Evaluates whether the answer is factual and complete based on the golden answer
correctness_metric = PGEval(
    name="Correctness",
    criteria="Determine whether the actual output is factually correct based on the expected output.",
    # NOTE: you can only provide either criteria or evaluation_steps, and not both
    evaluation_steps=[
        "Check whether the facts in 'actual output' contradicts any facts in 'expected output'",
        "You should also moderately penalize omission of detail",
        "Vague language, or contradicting OPINIONS, are not OK",
        "the actual output should have citations in the format [1] and will penalize for lack of citations",
        "do not check, comment, or penalize whether the expected output has citations"
    ],
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
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
        metrics=[ correctness_metric],  #answer_relevancy_metric,
        print_results=False,
        use_cache=True
    )

