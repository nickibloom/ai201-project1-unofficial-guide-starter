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

Unfiltered student-generated knowledge from the Rutgers University community (r/rutgers), spanning housing pitfalls, academic integrity, regional campus realities, transit changes, and post-graduation job markets.

Official university channels provide sanitized, idealized information (e.g., glossy housing brochures, high employment statistics, and rigid course catalogs). This "unofficial" community knowledge is valuable because it contains the unvarnished truth students need to survive, such as warnings about predatory off-campus apartments, the mental toll of course failure, and the actual reputation of regional campuses. It is impossible to find through official channels because universities do not document their own administrative shortcomings ("The RU Screw"), infrastructure flaws, or peer cheating cultures.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 |r/rutgers, "WARNING for Rutgers Students: Think Twice Before Renting at The Standard. Trapped in elevator, mold, water leaks from ceilings, HIDDEN ISSUES that they may CHARGE YOU FOR + off campus housing tips." | Reddit discussion |https://www.reddit.com/r/rutgers/comments/14butcp/warning_for_rutgers_students_think_twice_before/|
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

152 chunks across the 10 threads, none exceeding 1,200 characters and averaging ~1,020 characters. (Preprocessing before chunking: `ingest.py` parses the raw thread JSON, flattens the post and recursive comment tree into a single text stream, and strips noise — `AutoModerator`, `[deleted]`, and `[removed]` comments — before `chunks.py` splits it.)

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

While synthesizing the answer, the LLM will append inline anchors directly behind key sentences, for example: "...maintenance issues like black mold were rampant [1]."

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
| 1 | What specific maintenance issues did students face at The Standard off-campus apartments? | Severe mold, water leaks, elevator failures, and hidden fees from predatory leasing. | Listed mold, water leaks from ceilings, and being trapped in the elevator; flagged the "HIDDEN ISSUES that they may CHARGE YOU FOR" fee warning and noted the fire department is a frequent visitor. | Relevant — all 3 chunks from the correct thread (dist 0.35–0.40). | Accurate — captured every expected issue with grounded citations. |
| 2 | What are students complaining about regarding EV charging stations on campus? | Students unplug others' EVs mid-charge, violating charging etiquette. | Explained that people unplug EVs mid-charge (cited a Tesla unplugged after 14 min / +1%), declining commuter courtesy, too few chargers, and that it may count as criminal mischief reportable to RUPD. | Partially relevant — only the rank-2 chunk was the correct EV thread (0.54); ranks 1 and 3 were off-target housing-thread chunks. | Accurate — the model correctly grounded on the single relevant chunk and ignored the off-target ones. |
| 3 | Why are students upset about upcoming administrative budget cuts and how does it affect faculty? | Cuts target adjunct professors, sparking backlash ("The RU Screw"); hurts faculty support. | Explained adjuncts teach ~1/3 of undergrad classes for <1% of budget, dozens face layoffs (~100 classes), threatening time-to-degree; cited Math/CS unfilled positions and the Athletic Dept's $500M debt as an unfair contrast. | Relevant — all 3 chunks from the correct "RU Screw" thread (dist 0.36–0.46). | Accurate — strongly matches; richer detail than expected, minus an explicit "tuition hikes" mention. |
| 4 | What advice or perspective do graduates give about finding a job with a Rutgers supply chain degree? | Brutal entry market, salary imposter syndrome; compares Newark vs. New Brunswick networking pipelines. | Advised taking "shit roles" for experience, upskilling (data/AI certs), persistence ("first job, not your last"), and noted you can list "Rutgers University" without specifying the campus. | Relevant — all 3 chunks from the correct thread (best retrieval, dist 0.31–0.37). | Partially accurate — solid grounded advice, but lighter on the salary-gaslighting and Newark-vs-NB networking-pipeline angle the expected answer emphasized. |
| 5 | How do students counter the negative stereotypes about the Rutgers-Camden campus? | Tight-knit community, smaller class sizes, closer faculty access. | Highlighted smaller class sizes / personalized learning, flexible willing professors, campus diversity and community, and feeling safe commuting/walking around. | Partially relevant — top 2 chunks came from the general "Rutgers is a great school" thread; the dedicated "Is Camden really that bad?" thread only ranked 3rd. | Accurate — themes (small classes, community, faculty access) align with the expected answer. |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

**Summary:** 3 of 5 questions retrieved cleanly from the correct thread (Q1, Q3, Q4); Q2 and Q5 showed the "comment drift / shared-vocabulary" retrieval weakness predicted in planning.md — the correct source ranked 2nd or 3rd behind topically-overlapping chunks. Despite that, all 5 answers stayed accurate and grounded, because the LLM drew from the relevant retrieved chunk and ignored the off-target ones. Q4 is the only partial on accuracy: the advice is correct but underweights the regional-campus networking comparison the expected answer stressed. This pattern (weak top-1 retrieval on slang-heavy / overlapping topics, yet accurate generation) directly supports the embedding-model upgrade argued for in the Retrieval Approach reflection.

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** Q2 — "What are students complaining about regarding EV charging stations on campus?" (retrieval failure, not generation).

**What the system returned:** The final answer was actually correct, but *retrieval ranked the wrong document first*. For top-k=3, the ranking was:
- **[1] (dist 0.473)** — a chunk from the *housing* thread ("WARNING… The Standard") about apartment paperwork and "violations and health hazards." Completely unrelated to EV charging.
- **[2] (dist 0.539)** — the actual EV thread ("PSA: Don't unplug other people's cars"), the correct source.
- **[3] (dist 0.550)** — another off-topic housing chunk.

So 2 of the 3 retrieved chunks were off-target, and the correct thread was beaten to the top spot by an unrelated document.

**Root cause (tied to a specific pipeline stage):** This is an embedding / retrieval failure (Stages 3–4), specifically a vocabulary mismatch in the `all-MiniLM-L6-v2` model — not a chunking or generation problem. The correct EV chunk never contains the formal query terms: it says "Tesla," "charger," "charging," "charging spaces" — never "EV," "electric vehicle," or "charging station." The query "EV charging stations… complaining… on campus" has two strong signals, and the lightweight model latched onto the wrong one: the generic "student complaining on campus" sentiment. The housing chunk is saturated with exactly that grievance vocabulary ("this post scared me," "don't let them treat you poorly," "violations and health hazards"), so it scored as semantically closer to a complaint-shaped query than the narrative EV post, which tells a calm story about a 14-minute charge. The model has shallow understanding of hyper-local/colloquial phrasing and can't reliably map "EV charging station" → "someone yanked my Tesla charger."

**What you would change to fix it:** I would add a sparse keyword/BM25 score alongside the dense vector and fuse them. Lexical matching on "charging"/"unplug"/"charger" would immediately surface the EV thread regardless of the dense model's confusion over a "complaint"-shaped query.
Or I would upgrade the embedding model to a larger one (e.g. BGE-large, E5, or `text-embedding-3-large`) with richer colloquial/domain understanding and a longer context window.

It is worth noting the generation stage masked this failure: because the correct chunk still landed in the top-3 and the grounding prompt told the model to use only relevant context, the LLM ignored the two housing chunks and answered correctly. Had the correct chunk fallen to rank 4+, it would have been dropped from the context entirely and the answer would have failed outright. So, the retrieval weakness is real even though this particular response was accurate.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

The planning doc's specificity turned each milestone into a near-executable contract rather than a vague goal. Because the Chunking Strategy already fixed the exact numbers (800–1,200 characters, 200-character overlap) and the per-milestone AI Tool Plan spelled out concrete details. The five-stage architecture diagram also mapped almost one-to-one onto the four scripts (`ingest.py` → `chunks.py` → `embed.py` → `app.py`), which kept the pipeline modular. The Anticipated Challenges section was especially valuable in hindsight: it predicted "comment drift" and topically-overlapping retrieval, so when Q2 and Q5 retrieved off-target chunks during evaluation, I already had the vocabulary to diagnose and explain the failure instead of being surprised by it.

**One way your implementation diverged from the spec, and why:**

The largest divergence was the entire data-acquisition method in Stage 1 (Ingestion). The spec called for a standalone script that fetches each thread programmatically by appending `.json` to the URL, sending a custom `User-Agent`, and sleeping between requests. I built that initially, but every request returned HTTP 403, and testing showed Reddit was blocking the network's egress IP at the edge (even reddit.com's homepage 403'd while other sites returned 200). Programmatic scraping was not possible, so I pivoted: the 10 threads were saved manually as raw JSON from a logged-in browser into `documents/json_dumps/`, and `ingest.py` was rewritten to read and parse those local files instead of making any HTTP calls, the `requests`/`User-Agent`/`time.sleep` logic was removed entirely while the parsing, flattening, and noise-filtering logic stayed identical to the spec.

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

I gave Claude my planning.md file along with the following prompt:

I am working on Milestone 3 (Ingestion and Chunking) for my Unoffical Guide RAG application. 

Please write a robust Python ingestion script based on the following specifications:

1. TARGET URLS:
Here is the list of 10 target r/rutgers Reddit threads I need to fetch data from:
- https://www.reddit.com/r/rutgers/comments/14butcp/warning_for_rutgers_students_think_twice_before/
- https://www.reddit.com/r/rutgers/comments/1rs591k/the_ru_screw_is_coming_for_adjunct_professors/
- https://www.reddit.com/r/rutgers/comments/1i2q3fe/new_bus_route_just_dropped/
- https://www.reddit.com/r/rutgers/comments/1sbr92n/psa_dont_unplug_other_peoples_cars_while_its/
- https://www.reddit.com/r/rutgers/comments/1s3ovg9/graduated_from_rutgers_with_a_supply_chain_degree/
- https://www.reddit.com/r/rutgers/comments/1srwn8j/genuinely_about_to_fail_35_of_my_classes/
- https://www.reddit.com/r/rutgers/comments/1somr5w/cheating_in_class/
- https://www.reddit.com/r/rutgers/comments/1jekoj8/is_camden_really_that_bad/
- https://www.reddit.com/r/rutgers/comments/1n7oapr/stop_packing_up_before_the_lectures_over/
- https://www.reddit.com/r/rutgers/comments/1q1l81y/rutgers_is_a_great_school/

2. WORKAROUND & REQUEST CONSTRAINTS:
- Loop through these URLs and append `.json` to the end of them to request raw data.
- Include a custom `User-Agent` header (e.g., 'RutgersRAGApp/1.0 by Student') so Reddit does not return a 429 error.
- Add a tiny time delay (e.g., `time.sleep(2)`) between requests to be respectful of the endpoint.

3. DATA PARSING & FLATTENING LOGIC:
- Reddit's thread JSON structure returns a list containing two main elements: index [0] is the parent post data, and index [1] is the recursive comment tree.
- Extract the main post details: `title`, `selftext` (post body), and the `url` (permalink).
- Create a recursive function to walk down the nested comment tree array (`replies -> data -> children`). 
- Flatten all comments into a plain conversational text stream.
- Noise Filtering: Strip out any comments where the author is "AutoModerator", or where the body is literally "[deleted]" or "[removed]".

4. OUTPUT FORMAT:
- For each thread, save a clean JSON file in a directory named `raw_data/`.
- The saved JSON file should have a structured layout like this:
  {
    "post_title": "...",
    "source_url": "...",
    "flattened_content": "Post Title: ... \nPost Body: ... \nComment by user1: ... \nComment by user2: ..."
  }

- *What it produced:*

Claude created the ingest.py script and responded with the following message:

The script ran end-to-end and handled everything gracefully — but 0/10 threads saved, all 403 Blocked. I dug into the root cause, and it's not your code:

Test	Result
example.com (control)	✅ 200
reddit.com homepage	❌ 403
r/rutgers/about.json	❌ 403
oauth.reddit.com	❌ 403 (network-security block page)
r.jina.ai proxy → Reddit	❌ Reddit returns "blocked by network security"
Reddit OAuth token endpoint	⚠️ 401 (reachable, needs credentials)
Since even Reddit's homepage returns 403 from here while example.com works, this environment's egress IP (74.105.190.146) is blocked by Reddit at the network edge. Browser User-Agent, full sec-* headers, old.reddit.com, and a fetch-proxy all hit the same wall. This is Reddit's broad anti-scraping enforcement — unauthenticated .json access is largely dead now, and this IP is flagged.

The one promising signal: the OAuth token endpoint is reachable (returned 401, not a block page). Authenticated requests are treated differently from anonymous ones, so the official API is the robust path forward — but it needs a developer token.

How would you like to proceed?

- *What I changed or overrode:*

I pivoted to manually retrieving the json versions of the webpages for the threads since there was no way to get the data via requests. I then instructed Claude to use the json dumps I had placed in the documents folder and create an ingestion and cleaning script for those instead.

**Instance 2**

- *What I gave the AI:* 

I gave Claude my Chunking Strategy section and asked it to write a separate `chunks.py` that splits the flattened threads into 800–1,200 character chunks with ~200 character overlap. I specifically directed it to snap chunk boundaries to comment/line breaks so it would never cut through the middle of a comment.

- *What it produced:* 

It built `chunks.py`, which reads `raw_data/`, greedily packs whole comments into chunks (hard-splitting only a single comment that alone exceeds the max), and carries a ~200-char overlap forward. It output 152 chunks across the 10 threads, none over 1,200 characters, averaging ~1,020 — plus a verification report showing the size distribution and a sample overlap.

- *What I changed or overrode:* 

I scoped this step to chunking only and told Claude to defer the campus keyword-tagging from my spec for now. I also chose the boundary-snapping approach over a naive fixed-character split after Claude flagged that ~10 chunks fell under my 800 minimum. I accepted those smaller chunks as the deliberate tradeoff for keeping every comment intact.
