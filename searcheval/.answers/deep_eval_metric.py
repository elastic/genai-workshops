correctness_metric = GEval(
    name="Correctness",
    threshold=0.5,
    evaluation_steps=[
        "Check whether the facts in 'actual output' contradicts any facts in 'expected output'",
        "You should also moderately penalize omission of detail",
        "Vague language, or contradicting OPINIONS, are not OK",
        "do not check, comment, or penalize whether 'expected output' has citations"
    ],
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
    top_logprobs=5,
)

mention_of_no_context_node = BinaryJudgementNode(
    criteria="test whether `citation annotation` is present in the format [#] and not null",
    children=[
        VerdictNode(verdict=False, score=0),
        VerdictNode(verdict=True, child=correctness_metric),
    ],
)

extract_citation_used_node = TaskNode(
    instructions="Extract the citation annotation of format [#] used in the answer `actual_output`, if no ciation is present return null",
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
    output_label="citation annotation",
    children=[mention_of_no_context_node],
)

my_dag = DeepAcyclicGraph(root_nodes=[extract_citation_used_node])


citation_correctness_dag = DAGMetric(
    name="Citation Correctness", 
    dag=my_dag, 
    verbose_mode=False,
)