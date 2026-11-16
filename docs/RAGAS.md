# BLUCARE+ — MAKE THE MEDICAL RAG SYSTEM EXCELLENT

## Main objective

I want to significantly improve the actual medical RAG pipeline in BluCare+.

The application should work naturally for ordinary people, not just perfectly written technical queries.

Users might:
- Ask simple medical questions.
- Describe symptoms in their own words.
- Make spelling or grammatical mistakes.
- Ask follow-up questions.
- Use different words for the same medical condition.
- Provide incomplete information.
- Ask questions that our medical knowledge base does not cover.

Our system must understand their meaning, retrieve relevant medical evidence and generate clear, useful and trustworthy responses.

**The goal is excellent RAG quality, not complicated architecture. Keep the existing system simple, powerful and maintainable.**

## 1. Understand our current results first

Inspect our existing:

- RAGAS evaluation results.
- Original baseline and improved reports.
- Golden medical dataset.
- Per-question results and failure analysis.
- Medical documents and Qdrant collection.
- BGE embedding configuration.
- Retrieval and filtering logic.
- CrossEncoder reranking.
- Context construction.
- Groq generation prompt.
- Citation validation.

Our latest reported scores are:

| Metric | Reported score |
|---|---:|
| Faithfulness | 0.1471 |
| Context Recall | 0.5833 |
| Context Precision | 0.5000 |
| Answer Relevancy | 0.3761 |

These are not good enough.

Investigate actual failed questions and identify why each failure happened. Do not start changing random parameters.

Also verify the discrepancy between the 62-case golden dataset and the 12-case comparison cohort. Preserve both datasets and clearly identify which results are comparable.

## 2. Improve how the system understands questions

Users should not need to know medical terminology to use BluCare+.

Improve query preparation so that:

- Different phrasings of the same question can retrieve relevant evidence.
- Simple everyday language is understood.
- Common spelling mistakes do not unnecessarily break retrieval.
- Follow-up questions use the existing conversation context.
- Important patient-provided details are preserved.
- Irrelevant conversation history is not added to retrieval queries.
- The original user meaning is never changed.

For example:

"Why my head is paining?"

"Why do I have a headache?"

"What causes headache?"

The system should recognize their related meaning and retrieve useful medical evidence.

Use our existing embedding model and a simple query-preparation approach. Do not introduce unnecessary AI agents or multiple expensive LLM calls.

## 3. Improve document retrieval

Our retrieval must find the correct medical information, not just documents containing similar words.

Inspect and improve:

- Existing embedding generation.
- Qdrant search.
- Chunk quality and size.
- Chunk overlap.
- Metadata filtering.
- Similarity thresholds.
- Number of retrieved chunks.
- Duplicate retrieval.
- Relevant document coverage.

Use evaluation results to tune the retrieval configuration.

If relevant evidence exists in Qdrant but is not retrieved, fix the search configuration.

If evidence is missing because the medical documents are incomplete, identify the missing coverage instead of changing thresholds to hide the problem.

Do not blindly increase top-k or remove useful filters.

## 4. Improve CrossEncoder reranking

Inspect whether relevant documents are being retrieved but ranked poorly.

Make sure:

- The correct query is passed to the reranker.
- Retrieved chunks are scored correctly.
- Results are sorted in the correct order.
- The most useful medical evidence reaches the final context.
- Irrelevant and duplicate chunks are removed.

Keep the existing CrossEncoder unless the evaluation proves it is unsuitable.

## 5. Improve medical context construction

The LLM must receive useful, readable and sufficient evidence.

Improve context construction so that:

- Relevant chunks are prioritized.
- Important clinical details are not truncated.
- Duplicate information is reduced.
- Source IDs and metadata are preserved.
- Different medical topics are not mixed incorrectly.
- The context stays within the model's token limit.

Do not pass every retrieved document blindly to Groq.

## 6. Improve the final answer generation

This is extremely important.

The generated answer should be:

- Directly relevant to the user's question.
- Easy to understand.
- Grounded in retrieved medical evidence.
- Clear about uncertainty.
- Free from invented medical claims.
- Concise but sufficiently informative.
- Properly cited.

Use a short, well-designed generation prompt.

The model must:

1. Answer the actual question first.
2. Use retrieved evidence to support medical claims.
3. Avoid adding unsupported information.
4. Clearly distinguish established evidence from uncertainty.
5. Never fabricate citations.
6. Abstain or explain limitations when evidence is insufficient.
7. Avoid repetitive generic disclaimers and unnecessary information.
8. Never present a possible condition as a confirmed diagnosis.

Use everyday language. Do not make users read complicated medical terminology unless it is explained.

## 7. Improve medical knowledge coverage

Inspect our actual medical corpus.

The reported knowledge base currently contains 11 verified guideline documents.

Identify:
- Which topics are adequately covered.
- Which common user questions have insufficient evidence.
- Which medical topics are missing.
- Which documents have incomplete metadata.
- Which sources need better chunking or ingestion.

Expand the corpus only where necessary.

Use trustworthy medical references such as WHO, NICE and CDC, with appropriate source verification.

For each added document, preserve:

- Document title.
- Publisher.
- Original source URL.
- Publication or update date when available.
- Relevant medical topic.
- Document ID.
- Provenance information.

Do not add random internet articles or duplicate documents just to increase corpus size.

Never invent guideline recommendations or medical references.

## 8. Make the system work for different kinds of users

Test the RAG system using:

**Simple questions**
- What is migraine?
- What causes fever?
- What is dehydration?

**Everyday language**
- My head hurts whenever I wake up.
- Why does my throat hurt when I swallow?
- I feel weak since yesterday.

**Different wording**
- What is a tension headache?
- Explain tension-type headache.
- What does tension headache mean?

**Follow-up questions**
- Why does this happen?
- What should I watch for?
- How is it different from migraine?

**Incomplete or out-of-scope questions**
- Questions without enough information.
- Questions outside our available medical corpus.
- Questions requiring professional medical assessment.

Evaluate each category separately to understand where the system performs well and where it struggles.

## 9. Preserve medical safety

Improving RAG quality must never weaken BluCare+ safety.

Always preserve:

- Existing deterministic emergency checks.
- Existing patient-case management.
- Patient-specific context.
- Allergy and medication considerations where relevant.
- Emergency escalation.
- Evidence-grounded medical recommendations.

Never allow a high retrieval similarity score to mean that a patient has a particular disease.

Never generate unsupported medication dosages or treatment instructions.

Never treat missing symptoms as confirmed negative symptoms.

When evidence is insufficient, clearly say so instead of producing a confident answer.

The safety engine must run independently of retrieval quality.

## 10. Use RAGAS to prove every improvement

We already have RAGAS, Langfuse and Redis.

Reuse them. Do not add any more infrastructure.

After each meaningful improvement:

- Run existing automated tests.
- Run the same RAGAS golden dataset.
- Compare results with the original baseline.
- Compare results with the previous improved version.
- Inspect failed questions.
- Record retrieval and generation latency.

Track all four metrics:

1. Faithfulness.
2. Answer Relevancy.
3. Context Precision.
4. Context Recall.

Also report performance separately for in-scope questions, out-of-scope questions and safety-related questions.

Do not remove difficult test cases or modify reference answers just to increase scores.

If the evaluation exposes an issue with the evaluator or reference data, document it instead of hiding it.

Keep all previous reports and experiment history permanently.

## 11. Keep the implementation simple

Do not introduce:

- New AI agents.
- Another vector database.
- Another embedding provider.
- Redis replacement.
- Another observability platform.
- Complex multi-stage retrieval architectures without evidence.
- Unnecessary paid APIs.
- Unnecessary dependencies.

Continue using our existing FastAPI, LangGraph, BGE, Qdrant, CrossEncoder, Groq, RAGAS, Langfuse and Redis architecture.

Make targeted improvements to the existing code.

Preserve existing API contracts and frontend functionality.

## 12. Final deliverables

Create:

`BLUCARE_RAG_QUALITY_REPORT.md`

Include:

- Original weaknesses.
- Root causes.
- Improvements implemented.
- Updated architecture diagram.
- Before-and-after RAGAS metrics.
- Results by query category.
- Example questions that improved.
- Questions that still fail.
- Remaining medical knowledge gaps.

Update:

`INTERVIEW_NOTES.md`

Include:
- What problems we found.
- How we improved retrieval.
- How we improved answer generation.
- Why we made each change.
- Actual evaluation scores.
- What we learned.
- Simple technical interview questions and answers.

Create a final experiment report that preserves all previous results.

## 13. Definition of success

The work is complete when:

- Ordinary users can ask questions naturally.
- Similar questions retrieve relevant medical evidence.
- The correct medical documents reach the final context.
- Answers are directly relevant and understandable.
- Unsupported medical claims are reduced.
- Valid citations are provided.
- Insufficient evidence is handled honestly.
- All medical safety checks remain intact.
- All previous RAGAS results are preserved.
- New results demonstrate measurable improvements.

**FINAL INSTRUCTION**

Do not chase artificial 100% evaluation scores.

I want a genuinely better BluCare+ system that ordinary people can use confidently.

Understand the existing failures, fix their actual causes, test the complete RAG pipeline and prove the improvement using RAGAS.

Keep the system simple, fast, accurate and easy to explain in an internship interview.

Do not move on to another optimization project until this RAG quality improvement is complete and its results have been reviewed.