# MASTER PROMPT: BLUCARE+ — COMPLETE RAG CODEBASE ANALYSIS & TECHNICAL INTERVIEW PREPARATION

## YOUR ROLE

Act as my Senior AI Engineer, RAG Architect, Software Engineer, Code Reviewer, Security Reviewer and Technical Interview Mentor.

You are working inside my existing Antigravity workspace, where the BluCare+ project repository is open.

I authorize you to use the available workspace tools, terminal, filesystem and network access to perform the following project-local tasks:

- Install the required agent skills.
- Create directories and SKILL.md files.
- Read and analyze the relevant project source code.
- Run safe, relevant inspection commands.
- Generate interactive HTML architecture diagrams.
- Create detailed Markdown interview documentation.
- Perform code quality, architecture and security reviews.
- Use the installed skills to conduct the analysis.

Do not ask me for confirmation at every individual safe step. The scope is already authorized: install skills for the CURRENT PROJECT ONLY, not globally.

If Antigravity, the operating system or a tool requires a permission approval, request the necessary permission and continue after it is granted.

Do not claim to have administrator privileges you do not possess, bypass security controls, use sudo to force installation, or access another user's files.

---

# IMPORTANT PROJECT CONTEXT

BluCare+ is my AI-powered medical symptom triage and conversational RAG project.

The project aims to understand user symptoms, ask relevant follow-up questions, retrieve supporting medical knowledge and generate evidence-grounded responses using an LLM.

Some of the important concepts and technologies discussed during development include:

- Python backend and API development.
- Conversational AI and session management.
- Symptom extraction and normalization.
- LangChain and LLM orchestration.
- Document ingestion and preprocessing.
- Text chunking and embeddings.
- Vector database and similarity search.
- Retrieval-Augmented Generation.
- Medical evidence grounding.
- Context management and adaptive follow-up questions.
- RAGAS evaluation.
- Faithfulness, Answer Relevance, Context Precision and Context Recall.
- Langfuse / OpenTelemetry observability, if implemented.
- Database operations and API integrations.

This is background context, NOT proof that every listed technology or feature exists in the current codebase.

IMPORTANT:
Inspect the actual repository and determine what is implemented, partially implemented, planned or absent.

Never invent architecture, file paths, API endpoints, technologies, performance numbers or features.

# PRIMARY OBJECTIVE

I used AI-assisted development extensively while building this project.

Now I want to understand the complete implementation so I can confidently explain it during technical interviews.

I should be able to answer:

1. What does this project do?
2. Why did I choose this particular technology?
3. Where exactly is each technology used?
4. How does the complete application work internally?
5. How does data travel between modules?
6. How does the RAG pipeline actually work?
7. Why did I choose this retrieval approach?
8. What are the weaknesses in my implementation?
9. What happens when something fails?
10. How would I improve the system if an interviewer challenged my design?

The final result must be detailed but easy to understand.

Avoid unnecessary enterprise architecture, complicated terminology and theoretical discussions unrelated to my actual implementation.

---

# PHASE 1 — REPOSITORY DISCOVERY AND PREPARATION

Start by identifying the actual project root.

Run safe inspection commands such as:

```bash
pwd
ls -la
git status --short
git log -5 --oneline
```

Inspect the complete project structure, excluding generated or irrelevant folders such as:

- node_modules
- .venv
- venv
- __pycache__
- build
- dist
- .git

Identify:

- Frontend entry points.
- Backend entry points.
- API routes.
- Controllers.
- Services and utility modules.
- Database models.
- Session management.
- RAG pipeline.
- Embedding generation.
- Vector database.
- LLM integration.
- Evaluation code.
- Configuration and deployment files.

Inspect dependency manifests such as:

- requirements.txt
- pyproject.toml
- package.json
- package-lock.json
- Dockerfile
- docker-compose.yml
- Other relevant configuration files.

Do not expose secret values.

Never print, copy, include in reports or send externally:

- API keys.
- Access tokens.
- Passwords.
- Private credentials.
- Database connection secrets.
- Real patient information.
- Sensitive medical datasets.

Skip actual .env values and private data files. Use synthetic examples when an explanation requires sample data.

Before making changes, record the existing Git status. Do not overwrite existing user changes.

# PHASE 2 — INSTALL ALL REQUIRED SKILLS

Install the following four skills specifically for Antigravity and this project.

Use the latest compatible Skills CLI.

First, check Node.js and npm availability:

```bash
node --version
npm --version
```

Use project-level installation.

## Skill 1: Archify

Purpose: Generate interactive architecture, sequence and data-flow diagrams.

Archify repository:

https://github.com/tt-a1i/archify

Follow its installation procedure.

First discover the package:

```bash
npx -y skills@latest add https://archify.si --list --full-depth
```

Confirm that the listing contains exactly one skill named `archify`.

Inspect the target installation directory before installing. If an existing unmanaged installation or conflicting files are present, preserve them and report the conflict instead of overwriting them.

Install for Antigravity:

```bash
npx -y skills@latest add https://archify.si \
  --skill archify \
  --agent antigravity \
  --copy \
  --yes
```

Verify the installation using the actual installed location:

```bash
node <INSTALLED_ARCHIFY_PATH>/bin/archify.mjs doctor
```

Do not generate diagrams as part of the installation operation itself. Complete and verify installation first, then proceed to the architecture analysis phase.

## Skill 2: Addy Osmani — Code Review and Quality

Repository:

https://github.com/addyosmani/agent-skills

Install:

```bash
npx -y skills@latest add https://github.com/addyosmani/agent-skills \
  --skill code-review-and-quality \
  --agent antigravity \
  --copy \
  --yes
```

Purpose:

- Correctness.
- Code readability.
- Architecture.
- Maintainability.
- Performance.
- Engineering quality.

## Skill 3: Addy Osmani — Security and Hardening

Install:

```bash
npx -y skills@latest add https://github.com/addyosmani/agent-skills \
  --skill security-and-hardening \
  --agent antigravity \
  --copy \
  --yes
```

Purpose:

- Input validation.
- API security.
- Authentication and authorization.
- Secrets management.
- Dependency risks.
- Prompt injection.
- Data privacy.
- Secure handling of external content.

## Skill 4: Matt Pocock — Improve Codebase Architecture

Repository:

https://github.com/mattpocock/skills

Install:

```bash
npx -y skills@latest add https://github.com/mattpocock/skills \
  --skill improve-codebase-architecture \
  --agent antigravity \
  --copy \
  --yes
```

Purpose:

- Identify tightly coupled modules.
- Identify unnecessarily complicated abstractions.
- Find shallow modules.
- Understand module responsibilities.
- Recommend simpler architecture.
- Explain refactoring trade-offs.

If any installation fails, troubleshoot it safely. Do not delete existing files or force an overwrite.

If a skill is already correctly installed, reuse and verify it.

After installation, inspect:

```bash
find .agents/skills -maxdepth 3 -name SKILL.md -print
```

Read every installed skill's SKILL.md and understand its instructions.

If Antigravity has not automatically discovered the new skills, use the installed files directly for this execution and explain whether a reload or new conversation is needed for slash-command discovery.

---

# PHASE 3 — CREATE OUR CUSTOM INTERVIEW COACH SKILL

Create:

```text
.agents/
└── skills/
    └── rag-interview-coach/
        └── SKILL.md
```

Create the following SKILL.md:

---

name: rag-interview-coach

description: Analyzes the BluCare+ RAG project and prepares a complete technical interview guide covering architecture, technology selection, request lifecycle, embeddings, retrieval, LLM orchestration, evaluation, security, code quality and scalability.

---

# RAG INTERVIEW COACH

## Objective

Reverse-engineer the existing BluCare+ repository and explain it in a way that a final-year AI and Data Science engineering student can confidently present in technical interviews.

## Responsibilities

1. Understand the actual codebase.
2. Identify every major technology.
3. Map technology usage to exact source files.
4. Trace the most important request flows.
5. Explain the complete RAG pipeline.
6. Identify technical weaknesses.
7. Explain architectural trade-offs.
8. Prepare interview questions and answers.
9. Simulate an interviewer when requested.

## Rules

- Use actual code as evidence.
- Never invent implementation details.
- Explain complicated concepts using simple English.
- Provide real file paths and function names.
- Use line numbers whenever possible.
- Separate existing features from proposed improvements.
- Never expose secrets or private data.
- Never modify application source code.

## Interview Mode

Prepare beginner, intermediate and advanced questions.

For each question provide:

- What the interviewer expects.
- A technically correct answer.
- An example from BluCare+.
- A possible follow-up question.

When mock interview mode is activated, ask one question at a time, wait for the response, grade it out of 10 and correct technical and communication mistakes.

---

Save this file and verify that its YAML frontmatter and content are correct.

Use this skill throughout the remaining analysis. If slash-command discovery requires a reload, directly read and follow the file now rather than stopping the workflow.

---

# PHASE 4 — COMPLETE ARCHITECTURE UNDERSTANDING USING ARCHIFY

This is one of the most important phases.

Use the actual installed Archify skill and its documentation.

Generate clear, interactive, standalone HTML diagrams backed by source-code evidence.

Do not produce generic diagrams that merely describe what an ordinary RAG application looks like.

I want to understand MY implementation.

Create the following diagrams separately.

## Diagram 1: Complete System Architecture

Show:

- User.
- Frontend.
- Backend.
- API routes.
- Conversational logic.
- RAG orchestration.
- Embedding model.
- Vector database.
- LLM provider.
- Main database.
- Other real external integrations.

Only include components that actually exist.

Use clear arrows to explain their communication.

Separate optional integrations from the normal execution path.

## Diagram 2: Complete User Request Lifecycle

Trace what actually happens when a user enters a symptom and clicks Submit.

Show:

User Input
→ Frontend
→ API Request
→ Input Validation
→ Session Handling
→ Symptom Processing
→ Retrieval
→ Context Construction
→ LLM
→ Response Processing
→ Database Update, if applicable
→ Frontend Response

Follow the actual code and include branches for important conditions and errors.

## Diagram 3: Conversational Follow-up Flow

Explain how the application handles an ongoing conversation.

Show:

- Previous conversation history.
- Current user message.
- Symptom extraction.
- Missing information detection.
- Follow-up decision.
- Context preservation.
- Retrieval when required.
- Response generation.
- Session update.

Pay special attention to how the existing implementation handles:

- Repeated questions.
- Duration extraction.
- Incorrect symptom names.
- Session history.
- Context contamination.
- Follow-up decisions.

## Diagram 4: RAG Pipeline and Data Flow

Explain two separate flows.

DOCUMENT INGESTION:

Document
→ Loading
→ Cleaning
→ Chunking
→ Metadata
→ Embedding Generation
→ Vector Database

USER QUERY:

User Query
→ Query Processing
→ Query Embedding
→ Similarity Search
→ Retrieved Chunks
→ Context Construction
→ LLM
→ Generated Answer

Explain every step with real project references.

## Diagram Quality Requirements

This is for learning and interviews, not an architecture presentation for a large enterprise.

Therefore:

- Use clean layouts.
- Use simple labels.
- Avoid too many nodes.
- Use meaningful colors.
- Keep the primary path visually clear.
- Separate optional paths.
- Include a small legend.
- Use readable text.
- Include source file references and line numbers wherever supported.
- Add short explanations to important nodes.
- Make relationships and arrow directions unambiguous.
- Use clickable nodes where Archify supports them.

Do not put all the diagrams into one overcrowded image.

Create separate diagrams.

Use Archify's actual schemas, validation procedures and CLI commands. Do not invent unsupported properties or commands.

Save and preserve the generated HTML artifacts under:

```text
.archify/
```

Create an index in:

```text
docs/interview-prep/diagrams/README.md
```

Link every generated diagram and briefly explain what I should learn from it.

If a component or relationship cannot be verified, clearly mark it as unknown instead of guessing.

---

# PHASE 5 — COMPLETE TECHNOLOGY STACK ANALYSIS

Inspect all dependency manifests and the actual implementation.

Create:

```text
docs/interview-prep/02-tech-stack.md
```

For every important technology, explain:

1. What is it?
2. What problem does it solve?
3. Why does BluCare+ need it?
4. Where exactly is it used?
5. Which file, function or class uses it?
6. Why is it suitable compared with alternatives?
7. What is its main disadvantage?
8. What happens if we replace it?

Give comparisons only where they are relevant.

Examples:

- LangChain vs custom Python orchestration.
- Chroma vs FAISS vs Qdrant.
- Vector search vs traditional keyword search.
- Dense retrieval vs hybrid retrieval.
- Semantic chunking vs fixed-size chunking.
- FastAPI vs Flask, if applicable.
- PostgreSQL vs MongoDB, if relevant.
- RAGAS vs alternative evaluation frameworks.

Do not assume that a library is being used simply because it exists in requirements.txt.

Distinguish between:

- Installed dependency.
- Imported dependency.
- Actively used dependency.
- Unused or legacy dependency.

Create a clear technology table with columns:

Technology | Purpose | Actual Usage | Why Chosen | Alternative | Trade-off

At the end, write a simple explanation of the complete technology stack that I can speak during an interview.

---

# PHASE 6 — COMPLETE RAG DEEP DIVE

Create:

```text
docs/interview-prep/03-rag-pipeline.md
```

Explain the RAG implementation from beginning to end.

Cover:

## 1. Document Ingestion

- How documents enter the system.
- How they are loaded.
- How they are cleaned.
- How text is split.
- How chunk overlap works.
- How metadata is stored.
- How embeddings are generated.

## 2. Embeddings

Explain:

- What embeddings are.
- How text becomes numerical vectors.
- Why semantically similar content has useful vector relationships.
- Which embedding model is actually used.
- How embedding dimensions are determined.
- Why the selected model is appropriate.
- What happens when the embedding model changes.

## 3. Vector Database

Explain:

- What is stored in the database.
- How vector indexing works at a conceptual level.
- How similarity search works.
- What cosine similarity means, if used.
- What Top-K means.
- How metadata filtering works.
- How retrieval results are returned.

Use the actual implementation.

## 4. Retrieval

Explain:

- User query processing.
- Query embedding.
- Similarity search.
- Retrieval filtering.
- Context selection.
- What happens when no relevant documents are found.

## 5. Generation

Explain:

- How the prompt is built.
- How retrieved context reaches the LLM.
- How conversation history is included.
- How the response is generated.
- How evidence grounding is handled.
- What happens when retrieved evidence is insufficient.

## 6. Conversational Intelligence

Explain how the application maintains context between messages.

Investigate real implementations of:

- Symptom extraction.
- Symptom normalization.
- Session state.
- Duration handling.
- Adaptive questioning.
- Missing information detection.
- Question generation.
- Conversation memory.

Explain any problems you discover with concrete examples from the code.

## 7. RAG Failure Scenarios

Explain:

- Incorrect document retrieval.
- Irrelevant chunks.
- Poor chunk boundaries.
- Embedding mismatch.
- Empty search results.
- Hallucinations.
- Incorrect evidence attribution.
- Prompt injection.

For each, explain how it can happen and how the existing system handles it.

---

# PHASE 7 — CODE QUALITY AND SECURITY AUDIT

Use the installed skills:

- code-review-and-quality
- security-and-hardening

Create:

```text
docs/interview-prep/04-code-review.md
```

Perform an evidence-based audit.

Inspect these areas:

1. Backend architecture.
2. API routes.
3. Service organization.
4. Session management.
5. RAG pipeline.
6. Embedding and vector search.
7. Database operations.
8. LLM communication.
9. Error handling.
10. Security and privacy.

Identify the most important 5–10 findings.

Use severity:

- Critical
- High
- Medium
- Low

For each finding explain:

- Issue.
- Actual file and function.
- Exact code evidence.
- Why it is problematic.
- What could happen.
- Recommended improvement.
- How to verify the improvement.

Pay particular attention to:

- Missing input validation.
- Unnecessary repeated LLM calls.
- Missing timeout handling.
- Poor exception handling.
- N+1 queries, if present.
- Unnecessary database requests.
- Unbounded conversation history.
- Inefficient retrieval.
- Missing caching opportunities.
- API key exposure.
- Cross-user session isolation.
- Unsafe prompt construction.
- Prompt injection from retrieved documents.
- Sensitive data leakage through logs.

Do not claim a vulnerability merely because you cannot find a particular protection.

State whether a weakness is confirmed, suspected or not verified.

Do not automatically repair anything.

---

# PHASE 8 — ARCHITECTURAL REVIEW

Use the installed:

improve-codebase-architecture

skill.

Analyze the actual module structure.

Find:

- Files doing too many things.
- Duplicate business logic.
- Tightly coupled modules.
- Unnecessary abstraction layers.
- Unclear responsibilities.
- Unnecessarily complicated functions.
- Difficult-to-test modules.
- Unused modules.

Create:

```text
docs/interview-prep/05-architecture-review.md
```

For each important problem:

1. Show the existing structure.
2. Explain why it is problematic.
3. Suggest a simpler structure.
4. Show the proposed file organization where useful.
5. Explain the advantages.
6. Explain the disadvantages.
7. Explain whether the refactor is worth doing.

Keep the recommendations realistic.

Do not introduce microservices, Kubernetes, Kafka, complex design patterns or distributed architecture unless there is an actual, justified requirement.

This is an academic and interview-preparation project.

Do not create GitHub issues, pull requests, commits or change application source code.

The architecture review is for understanding and interview preparation, not a refactoring campaign.

---

# PHASE 9 — SCALABILITY AND ENGINEERING TRADE-OFFS

Create a section covering practical hypothetical interview scenarios.

Answer these questions using the actual implementation.

1. What happens if traffic increases 10x?
2. What happens if the LLM API is unavailable?
3. What happens if vector retrieval fails?
4. How could we reduce retrieval latency?
5. How could we reduce LLM API costs?
6. How could we avoid repeated embedding generation?
7. How should growing conversation history be managed?
8. How could database performance be improved?
9. How would we prevent users from accessing another user's session?
10. How would we improve overall reliability?

For every answer explain:

Current implementation
→ Bottleneck
→ Practical improvement
→ Trade-off

Do not invent performance benchmarks.

Do not turn every answer into an enterprise redesign.

Prioritize practical engineering improvements such as:

- Better database queries.
- Indexing where appropriate.
- Caching where safe.
- Request timeouts.
- Rate limiting.
- Concurrency control.
- Reusing embeddings.
- Limiting unnecessary context.
- Batching where appropriate.
- Background processing only when justified.

Explain what should be optimized first and why.

---

# PHASE 10 — RAGAS AND OBSERVABILITY ANALYSIS

Inspect the actual implementation.

Create a section explaining whether the following are present:

- RAGAS.
- Faithfulness.
- Answer Relevance.
- Context Precision.
- Context Recall.
- Golden evaluation datasets.
- Evaluation scripts.
- Langfuse.
- OpenTelemetry.
- Retrieval latency tracking.
- Generation latency tracking.
- Token usage tracking.
- Error tracking.

Categorize each:

IMPLEMENTED
PARTIALLY IMPLEMENTED
PLANNED
NOT FOUND

Explain how I should discuss RAG evaluation in an interview.

Do not claim evaluation results that have not actually been measured.

Explain why evaluating RAG retrieval and evaluating LLM response generation are two different things.

---

# PHASE 11 — CREATE MY COMPLETE TECHNICAL INTERVIEW STUDY GUIDE

Create:

```text
docs/interview-prep/06-interview-preparation.md
```

This is the most important final document.

Prepare it in simple English, with practical examples from BluCare+.

Organize it into these sections.

## A. Project Introduction

Prepare:

- 30-second introduction.
- 1-minute project introduction.
- 2-minute technical explanation.

Make the language natural and suitable for a final-year engineering student.

## B. Architecture Explanation

Prepare a simple explanation of the complete application.

Explain the request flow from the user's message to the final response.

Tell me how to explain each important module.

## C. Technology Justification

Prepare interview-ready answers for:

- Why Python?
- Why the selected backend framework?
- Why LangChain, if used?
- Why a vector database?
- Why the selected embedding model?
- Why the selected LLM?
- Why RAG instead of direct LLM prompting?
- Why the chosen database?
- Why the evaluation framework?

Base every answer on actual implementation and clearly identify any engineering reasoning that is inferred rather than documented historical reasoning.

## D. RAG Technical Questions

Prepare detailed answers for:

- What is RAG?
- What are embeddings?
- What is vector search?
- What is cosine similarity?
- What is chunking?
- What is chunk overlap?
- What is Top-K retrieval?
- What is context precision?
- What is context recall?
- What is faithfulness?
- What is hallucination?
- What is prompt injection?
- How can retrieval quality be improved?

## E. Backend and Database Questions

Prepare:

- How does an API request work?
- What happens between controller and service?
- How is session history maintained?
- How is data persisted?
- How do you handle exceptions?
- How do you avoid duplicate database operations?
- What are the bottlenecks?

## F. Architecture and System Design Questions

Prepare:

- Explain the complete architecture.
- What would break under 10x traffic?
- How would you reduce latency?
- How would you improve reliability?
- What would you change in version 2?
- What technical debt exists?

## G. Code-Level Questions

Select important functions and explain:

- Input.
- Output.
- Purpose.
- Internal logic.
- Dependencies.
- Why the function is needed.
- Possible edge cases.

Include exact source references.

## H. Project Weaknesses

Prepare an honest answer for:

"What are the limitations of your project?"

Include realistic engineering weaknesses and how I would improve them.

Do not present unimplemented features as completed achievements.

## I. Top Interview Questions

Prepare at least 25 high-quality technical interview questions with:

- Question.
- Expected answer.
- Actual project example.
- Possible follow-up.

Prioritize the most likely questions first.

## J. Quick Revision

Create a final two-page-style revision section:

- Architecture in one glance.
- Technology stack in one glance.
- RAG pipeline in one glance.
- Important terminology.
- Top 15 questions.
- Important weaknesses.
- My best project explanation.

---

# PHASE 12 — SIMPLE PROJECT GLOSSARY

Create:

```text
docs/interview-prep/07-glossary.md
```

Explain important technical terms using this structure:

TERM

Meaning:
Simple English explanation.

Where we use it:
Actual BluCare+ file or function.

Example:
A simple real-world example.

Interview answer:
One or two sentences I can speak.

Include relevant terms from RAG, Python, APIs, databases, embeddings, vector search, LLMs, evaluation and architecture.

Do not create a huge unrelated dictionary.

---

# PHASE 13 — QUALITY CHECK AND FINAL DOCUMENTATION INDEX

Create the following final documentation structure:

```text
docs/
└── interview-prep/
    ├── README.md
    ├── diagrams/
    │   └── README.md
    ├── 02-tech-stack.md
    ├── 03-rag-pipeline.md
    ├── 04-code-review.md
    ├── 05-architecture-review.md
    ├── 06-interview-preparation.md
    └── 07-glossary.md
```

The README.md must be the entry point.

Explain the recommended reading order:

1. Understand the architecture.
2. Understand the technology stack.
3. Learn the RAG pipeline.
4. Understand code weaknesses.
5. Study interview questions.
6. Revise the glossary.

Include relative links to all documents and the generated Archify HTML diagrams.

Ensure all output documents are readable and properly structured.

Verify that:

- All referenced files actually exist.
- Source paths are correct.
- Line references are reasonable and current.
- The diagrams open correctly.
- No credentials are included.
- No features are falsely presented as implemented.
- No application source files were modified.
- No existing user changes were overwritten.

Record the final Git status and compare it with the initial Git status.

---

# IMPORTANT EXECUTION RULES

1. Work through all phases sequentially in this same task.
2. Actually run the installation commands; do not merely print them.
3. Actually create the custom SKILL.md file.
4. Read and use the installed skill instructions.
5. Generate real Archify HTML diagrams, not just Mermaid text or generic illustrations.
6. Read actual code before preparing technical explanations.
7. Cite actual file paths and functions wherever possible.
8. Keep explanations beginner-friendly without sacrificing technical accuracy.
9. Separate implemented functionality from planned features.
10. Do not modify business logic, application code, database schemas, prompts or dependencies.
11. Do not run destructive database operations, migrations, deployment commands or real external medical requests.
12. Do not create GitHub issues, PRs or commits.
13. Do not perform expensive or unnecessary production benchmarking.
14. If a skill fails to install, record the failure and continue with the remaining available tools.
15. If a diagram fails validation, repair and validate it using Archify's own process.
16. Do not stop after creating the installation files. Complete the analysis and documentation.
17. Do not ask me to select among multiple options. Make reasonable decisions based on the repository and this interview-preparation goal.

# FINAL SUCCESS CRITERIA

I consider this task complete only when:

- The required skills have been installed or their failures have been clearly reported.
- My custom rag-interview-coach/SKILL.md exists.
- The actual BluCare+ architecture has been traced.
- Multiple interactive architecture diagrams have been generated and validated.
- The real technology stack has been explained.
- The actual RAG pipeline has been reverse-engineered.
- Code quality and security reviews have been completed.
- Architectural weaknesses have been documented.
- Practical scalability trade-offs have been explained.
- A complete interview study guide has been created.
- At least 25 interview questions and answers are included.
- All documentation has been linked from one README.

# FINAL RESPONSE

Once everything is complete, provide:

1. Installation status of all four skills.
2. Location of my custom SKILL.md.
3. Number and names of diagrams generated.
4. Location of the interview preparation documentation.
5. Five most important technical weaknesses discovered.
6. The five most important technologies used in my actual project.
7. Any incomplete tasks or installation errors.

Finally, tell me which document I should open first to start preparing for my technical interview.

Remember:

MY GOAL IS NOT TO BUILD A MORE COMPLICATED PRODUCT.

MY GOAL IS TO UNDERSTAND EVERY IMPORTANT PART OF THE EXISTING BLUCARE+ PROJECT SO WELL THAT I CAN EXPLAIN IT, JUSTIFY IT, DEBUG IT AND DEFEND IT IN A REAL TECHNICAL INTERVIEW.