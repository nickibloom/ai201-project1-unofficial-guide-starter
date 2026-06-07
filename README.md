# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 |r/rutgers, "WARNING for Rutgers Students: Think Twice Before Renting at The Standard | Trapped in elevator, mold, water leaks from ceilings, HIDDEN ISSUES that they may CHARGE YOU FOR + off campus housing tips." | Reddit discussion |https://www.reddit.com/r/rutgers/comments/14butcp/warning_for_rutgers_students_think_twice_before/|
| 2 |r/rutgers, "The RU Screw Is Coming for Adjunct Professors Again and Messing Things Up for Students" | Reddit discussion | https://www.reddit.com/r/rutgers/comments/1rs591k/the_ru_screw_is_coming_for_adjunct_professors/|
| 3 |r/rutgers, "new bus route just dropped!!!" | Reddit discussion |https://www.reddit.com/r/rutgers/comments/1i2q3fe/new_bus_route_just_dropped/|
| 4 |r/rutgers, "PSA: Don’t unplug other people’s cars while it’s charging" | Reddit discussion |https://www.reddit.com/r/rutgers/comments/1sbr92n/psa_dont_unplug_other_peoples_cars_while_its/|
| 5 |r/rutgers, "Graduated from Rutgers with a Supply Chain degree. Seeing old threads about $70k entry level offers feels like gaslighting. Is the “top school” pipeline the only way left?" | Reddit discussion |https://www.reddit.com/r/rutgers/comments/1s3ovg9/graduated_from_rutgers_with_a_supply_chain_degree/|
| 6 |r/rutgers, "genuinely about to fail 3/5 of my classes" | Reddit discussion |https://www.reddit.com/r/rutgers/comments/1srwn8j/genuinely_about_to_fail_35_of_my_classes/|
| 7 |r/rutgers, "cheating in class" | Reddit discussion |https://www.reddit.com/r/rutgers/comments/1somr5w/cheating_in_class/|
| 8 |r/rutgers, "Is Camden really that bad?" | Reddit discussion |https://www.reddit.com/r/rutgers/comments/1jekoj8/is_camden_really_that_bad/ |
| 9 |r/rutgers, "Stop Packing Up Before The Lectures Over" | Reddit discussion |https://www.reddit.com/r/rutgers/comments/1n7oapr/stop_packing_up_before_the_lectures_over/|
| 10 |r/rutgers, "Rutgers is a great school" | Reddit discussion |https://www.reddit.com/r/rutgers/comments/1q1l81y/rutgers_is_a_great_school/|

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:**

800 to 1,200 characters (approximately 150 to 250 words).

**Overlap:**

200 characters (approximately 40 to 50 words).


**Why these choices fit your documents:**

Our corpus consists entirely of Reddit threads, which feature a unique structure: a single parent post followed by an unpredictable tree of nested student comments and replies. Traditional fixed-character chunking (e.g., cutting exactly every 500 characters) would devastatingly slice through these conversations, separating a student's question from another student's reply, rendering the vector completely useless.

An 800–1,200 character target is roughly the length of a thorough Reddit post or a 2-3 paragraph comment chain. This ensures that a student's rant (like the off-campus housing warning in Doc 1) or a detailed piece of campus advice remains entirely intact within a single chunk.

A 200-character overlap acts as a semantic bridge. Since Reddit responses rely entirely on the context of the comment above them, this overlap ensures that the tail-end of a preceding comment is carried into the next chunk, preserving the conversational thread's continuity.

Because we are dealing with diverse, drifting topics (e.g., a general thread where someone suddenly mentions a specific campus landmark like Newark's RBS or a New Brunswick bus route), this size is small enough to ensure high semantic density, yet large enough to contain the unique "trigger words" required for our chunk-level campus classification logic.

**Final chunk count:**

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**

This project uses the all-MiniLM-L6-v2 model via the sentence-transformers library to map text chunks into 384-dimensional vectors. This lightweight model (under 100MB) runs entirely locally on CPU hardware, eliminating the need for paid API keys, network overhead, or rate limits during development. It excels at capturing semantic intent in conversational text, making it ideal for matching user questions to informal Reddit comments. It provides the optimal balance of sub-second retrieval latency and reliable search accuracy for a local RAG prototype.


**Production tradeoff reflection:**

If deploying this system at scale for real users with an unlimited budget, all-MiniLM-L6-v2 would be replaced. While excellent for local development because it requires no API keys and has zero hosting costs, it introduces strict production bottlenecks.

In upgrading to a commercial or larger open-source model (such as OpenAI's text-embedding-3-large or a flagship BGE/E5 model), the following trade-offs would be weighed:

-> Accuracy on Domain-Specific Text (Highest Priority): Reddit data is heavily saturated with internet slang, abbreviations, and hyper-local terminology (e.g., "RU Screw," "Livi," "Cac," "LX bus"). A standard, lightweight embedding model struggles to understand that "Livi" and "Livingston" map to the same physical location. A larger, state-of-the-art model has a much richer semantic understanding of colloquial text, drastically improving retrieval accuracy for messy student data.

-> Context Length vs. Latency: all-MiniLM-L6-v2 has a hard limit of 256 input tokens. If a student leaves a long, highly detailed comment detailing a housing horror story, the tail end of that comment is cut off before it can even be embedded. Upgrading to a model with an 8k+ token context window allows the system to ingest entire discussion threads in a single embedding. However, larger context lengths and bigger models increase vector dimensions (e.g., from 384 dimensions to 1536 or 3072 dimensions), which increases search latency.

-> Latency vs. Accuracy: Real users expect sub-second response times. High-dimension models yield incredibly precise semantic matches, but they take longer to generate vectors and scan the database. The system would need to balance whether a 5% increase in retrieval accuracy is worth a 200ms delay in user response time.


---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

You are an unvarnished, authentic academic advisor answering student questions using ONLY the provided Reddit context blocks. Your primary goal is absolute accuracy based on the provided text. 

Adhere to the following strict rules:
1. If the answer cannot be confidently found within the provided context, you must explicitly state: "I'm sorry, but that information isn't available in the informal student data logs." Do not attempt to guess, extrapolate, or use outside knowledge.
2. Rely entirely on the factual statements or student experiences provided. Never say "Based on my knowledge" or "As an AI."
3. For every major claim, advice point, or student sentiment you reference, you must attach the exact source URL and post title in an inline markdown citation format.

**How source attribution is surfaced in the response:**

Source attribution is handled directly via structural markdown injection within the gr.ChatInterface response string.

Because we are utilizing Gradio's native Markdown rendering engine inside the chat bubbles, the backend prediction loop will format every output into two distinct, structured zones.

While synthesizing the answer, the LLM will append inline anchors directly behind key sentences—for example: "...maintenance issues like black mold were rampant [1]."

At the very bottom of the generated text block, a clear horizontal rule boundary will be drawn, followed by a mapped references list utilizing the parsed metadata (source_url and post_title) tied directly to the indexed ChromaDB chunk:

     **Sources Cited:**
     * [1] [WARNING for Rutgers Students: Think Twice Before Renting...](https://www.reddit.com/r/rutgers/comments/14butcp/...)

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
