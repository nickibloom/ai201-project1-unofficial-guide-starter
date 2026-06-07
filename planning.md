# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

Unfiltered student-generated knowledge from the Rutgers University community (r/rutgers), spanning housing pitfalls, academic integrity, regional campus realities, transit changes, and post-graduation job markets.

Official university channels provide sanitized, idealized information (e.g., glossy housing brochures, high employment statistics, and rigid course catalogs). This "unofficial" community knowledge is valuable because it contains the unvarnished truth students need to survive, such as warnings about predatory off-campus apartments, the mental toll of course failure, and the actual reputation of regional campuses. It is impossible to find through official channels because universities do not document their own administrative shortcomings ("The RU Screw"), infrastructure flaws, or peer cheating cultures.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

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

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

800 to 1,200 characters (approximately 150 to 250 words).

**Overlap:**

200 characters (approximately 40 to 50 words).

**Reasoning:**

Our corpus consists entirely of Reddit threads, which feature a unique structure: a single parent post followed by an unpredictable tree of nested student comments and replies. Traditional fixed-character chunking (e.g., cutting exactly every 500 characters) would devastatingly slice through these conversations, separating a student's question from another student's reply, rendering the vector completely useless.

An 800–1,200 character target is roughly the length of a thorough Reddit post or a 2-3 paragraph comment chain. This ensures that a student's rant (like the off-campus housing warning in Doc 1) or a detailed piece of campus advice remains entirely intact within a single chunk.

A 200-character overlap acts as a semantic bridge. Since Reddit responses rely entirely on the context of the comment above them, this overlap ensures that the tail-end of a preceding comment is carried into the next chunk, preserving the conversational thread's continuity.

Because we are dealing with diverse, drifting topics (e.g., a general thread where someone suddenly mentions a specific campus landmark like Newark's RBS or a New Brunswick bus route), this size is small enough to ensure high semantic density, yet large enough to contain the unique "trigger words" required for our chunk-level campus classification logic.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

all-MiniLM-L6-v2 via the sentence-transformers library

**Top-k:**

3 chunks per query

**Production tradeoff reflection:**

If deploying this system at scale for real users with an unlimited budget, all-MiniLM-L6-v2 would be replaced. While excellent for local development because it requires no API keys and has zero hosting costs, it introduces strict production bottlenecks.

In upgrading to a commercial or larger open-source model (such as OpenAI's text-embedding-3-large or a flagship BGE/E5 model), the following trade-offs would be weighed:

-> Accuracy on Domain-Specific Text (Highest Priority): Reddit data is heavily saturated with internet slang, abbreviations, and hyper-local terminology (e.g., "RU Screw," "Livi," "Cac," "LX bus"). A standard, lightweight embedding model struggles to understand that "Livi" and "Livingston" map to the same physical location. A larger, state-of-the-art model has a much richer semantic understanding of colloquial text, drastically improving retrieval accuracy for messy student data.

-> Context Length vs. Latency: all-MiniLM-L6-v2 has a hard limit of 256 input tokens. If a student leaves a long, highly detailed comment detailing a housing horror story, the tail end of that comment is cut off before it can even be embedded. Upgrading to a model with an 8k+ token context window allows the system to ingest entire discussion threads in a single embedding. However, larger context lengths and bigger models increase vector dimensions (e.g., from 384 dimensions to 1536 or 3072 dimensions), which increases search latency.

-> Latency vs. Accuracy: Real users expect sub-second response times. High-dimension models yield incredibly precise semantic matches, but they take longer to generate vectors and scan the database. The system would need to balance whether a 5% increase in retrieval accuracy is worth a 200ms delay in user response time.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What specific maintenance issues did students face at The Standard off-campus apartments? | According to student warnings, the building suffered from severe mold, consistent water leaks, elevator failures, and hidden fees from predatory leasing practices.|
| 2 | What are students complaining about regarding EV charging stations on campus? | Students are violating charging etiquette by unplugging other people's electric vehicles while they are still in the middle of charging.|
| 3 | Why are students upset about upcoming administrative budget cuts and how does it affect faculty? | The university administration is implementing budget cuts that target adjunct professors, sparking student backlash over tuition hikes and reduced faculty support ("The RU Screw").|
| 4 | What advice or perspective do graduates give about finding a job with a Rutgers supply chain degree?| Graduates note a brutal entry-level job market and feelings of imposter syndrome regarding salary, while comparing the corporate networking pipelines between regional campuses (Newark vs. New Brunswick). |
| 5 | How do students counter the negative stereotypes about the Rutgers-Camden campus? | Students defend the campus by highlighting its tight-knit community culture, smaller class sizes, and closer, more accessible interactions with faculty compared to larger campuses.|

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. The chunking strategy relies on a character count window (800–1,200 characters). Because Reddit comments are written informally without standardized paragraph lengths, a hard character cutoff will inevitably slice through the middle of a student's core piece of advice or completely separate a question comment from its nested reply.

If a student posts a detailed warning about an apartment landlord in Doc 1, and the crucial name of the leasing company or the specific resolution falls right on the boundary line, the information gets split. The embedding model will vectorize two partial contexts, which weakens their semantic scores. At query time, the retrieval engine might only pull down the first half of the comment, leaving the LLM with an incomplete or ambiguous context, leading to an incomplete or inaccurate answer.

2. Reddit discussions are notorious for "comment drift," where a thread starts on a specific topic (e.g., Doc 4 regarding EV charging etiquette) but devolves into an unrelated argument about campus parking tickets, general commuting gripes, or jokes in the lower comment trees.

Because the dataset contains general threads rather than perfectly clean, single-topic documents, the vector store will contain chunks that are structurally part of the target document but contextually irrelevant to the core domain. If a user asks a specific question about vehicle charging, a chunk containing a tangent about Rutgers parking police might be retrieved simply because it shares keywords like "parking lot" and "car." This pushes noisy, non-essential data into the LLM prompt window, risking an answer that is distracted or fails to directly address the user's core prompt.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->


=================================================================================================
1. DOCUMENT INGESTION    -->  [ Raw Reddit JSON ] ➔ Parse & Flatten ➔ Strip Noise
                              (Tool: Python Native / requests)
=================================================================================================
                                     ▼
=================================================================================================
2. CHUNKING              -->  [ Character Splitting ] ➔ 800-1200 chars / 200 overlap
                              [ Metadata Enrichment ] ➔ Campus keyword-tagging logic
                              (Tool: Custom Python Functions)
=================================================================================================
                                     ▼
=================================================================================================
3. EMBEDDING & STORE     -->  Generate Text Embeddings (384-dimensional vectors)
                              ➔ Save to Local Database
                              (Tools: sentence-transformers [all-MiniLM-L6-v2] | ChromaDB)
=================================================================================================
                                     ▼
=================================================================================================
4. RETRIEVAL             -->  User Query ➔ Embed Query ➔ Semantic Search ➔ Top-K (3 Chunks)
                              (Tools: Streamlit UI ➔ ChromaDB Vector Query)
=================================================================================================
                                     ▼
=================================================================================================
5. GENERATION            -->  [ Grounded Prompt Injection ] ➔ Strict context enforcement
                              ➔ Generate Response with Source Citations
                              (Tools: Groq API [llama-3.3-70b-versatile] ➔ Streamlit Display)
=================================================================================================

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

AI Tool: Claude 

Input: I will give it the specific list of my 10 target Reddit thread URLs, the Project Overview & Scope, and my complete Chunking Strategy section (including the 800–1,200 character window, 200-character overlap, and the keyword-based campus tagging logic).

Expected Output: Two functional components: a standalone ingestion script that fetches raw data via the .json workaround, filters out system noise (AutoModerator, [deleted], [removed]), and flattens comment trees; and a chunk_and_tag_document() Python function that breaks that text down into my exact character windows while injecting the dynamic campus metadata tags into the chunk payload.

Verification: I will execute the scripts locally, print the character count of a sample chunk (len(chunk_text)) to ensure it fits the 800–1,200 range, check that consecutive chunks share a ~200-character overlap text string, and inspect the metadata dictionary to confirm specific campus strings (like "Newark" or "New Brunswick") were assigned correctly based on text triggers.

**Milestone 4 — Embedding and retrieval:**

Input: I will feed Claude my System Architecture blueprint, my Vector Store & Semantic Search specification (detailing the use of local ChromaDB and the all-MiniLM-L6-v2 model from sentence-transformers), and a sample JSON payload of a chunk generated in Milestone 3.

Expected Output: An orchestration script that initializes a persistent local ChromaDB instance, loads the embedding model, loops through my chunk files to generate 384-dimensional dense vectors, upserts them alongside their respective metadata, and provides a raw retrieval function to execute a query.

Verification: I will check the database initialization by running a basic script to assert that collection.count() precisely equals the total number of chunks generated in Milestone 3. I will then test the retrieval function using a sample question from my evaluation suite to verify that it successfully prints out exactly three ($K=3$) distinct, contextually relevant chunks.

**Milestone 5 — Generation and interface:**

Input: I will provide the Evaluation Plan matrix, my Architecture Diagram, the specific Groq API requirements (llama-3.3-70b-versatile), and the native gr.ChatInterface documentation paradigm mapping a backend function predict(message, history) to a conversational layout.

Expected Output: A unified user interface script (app.py) built entirely with Gradio. This script will contain a prediction function that ingests the user's incoming message, manages conversational history context, triggers the ChromaDB query string, structures the context-grounded prompt window for Groq, and maps it directly to a clean gr.ChatInterface block.

Verification: I will spin up the interface locally via python app.py in my terminal, navigate to the generated local URL, test my 5 evaluation matrix queries, and verify that the chat dashboard prints clean markdown text outputs along with explicit source citations. I will also test the "Clear" button to confirm chat state resets without dropping errors.