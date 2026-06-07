"""
app.py — Milestone 5: Generation and Interface

The unified Gradio chat app for "The Unofficial Guide". Ties together:
    - Retrieval: ChromaDB top-k search via embed.retrieve() (Milestone 4).
    - Generation: Groq (llama-3.3-70b-versatile), grounded strictly in the
      retrieved r/rutgers discussion chunks, with inline [n] citations.
    - Interface: Gradio's native gr.ChatInterface(fn=predict, ...).

Run:
    python app.py
then open the local URL it prints.

Requires GROQ_API_KEY in a .env file (see .env.example).
"""

import os

import gradio as gr
from dotenv import load_dotenv
from groq import Groq

# Reuse the retrieval stack built in Milestone 4 (no duplicated Chroma/embedding code).
from embed import retrieve

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
TOP_K = 3
TEMPERATURE = 0.2  # low — we want grounded, not creative, answers

# The system prompt wrapper. {context} is filled per-query with retrieved chunks.
SYSTEM_PROMPT = """You are "The Unofficial Guide", a candid assistant that answers \
questions about life at Rutgers University using ONLY real student discussions \
from the r/rutgers subreddit.

Follow these rules strictly:
- Answer using ONLY the numbered context below. Do not use any outside knowledge.
- If the context does not contain enough information to answer, say so plainly \
("The student discussions I have don't cover that") instead of guessing.
- Cite your sources inline using bracketed numbers like [1] or [2] that match the \
numbered context items you drew from.
- Write in a clear, conversational tone and format your answer with Markdown.

Context (student discussions):
{context}"""

# Groq client is created lazily so the app can still load (and show a friendly
# error in chat) when the key is missing.
_client = None


def get_client():
    """Return a cached Groq client, or None if no API key is configured."""
    global _client
    if _client is None and GROQ_API_KEY:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


# --------------------------------------------------------------------------- #
# Context assembly
# --------------------------------------------------------------------------- #

def build_context(hits):
    """Turn retrieved chunks into (context_block, references_block).

    context_block is the numbered text fed to the model. references_block is a
    deterministic, human-readable source list appended after the answer so the
    citations always map to real URLs (rather than trusting the model to print
    them).
    """
    if not hits:
        return "(no relevant student discussions were found)", ""

    # Assign one citation number per unique source thread, so chunks from the
    # same thread share a number and the source list has no duplicate URLs.
    url_to_num = {}
    reference_items = []
    context_items = []
    for hit in hits:
        url = hit.get("source_url", "")
        title = hit.get("post_title", "Untitled thread")
        if url not in url_to_num:
            num = len(url_to_num) + 1
            url_to_num[url] = num
            reference_items.append(f"{num}. [{title}]({url})")
        num = url_to_num[url]
        context_items.append(f'[{num}] From the thread "{title}":\n{hit["text"]}')

    context_block = "\n\n".join(context_items)
    references_block = "\n\n---\n**Sources**\n\n" + "\n".join(reference_items)
    return context_block, references_block


# --------------------------------------------------------------------------- #
# Core prediction logic
# --------------------------------------------------------------------------- #

def predict(message, history):
    """Backend for gr.ChatInterface.

    `message` is the latest user turn; `history` is the prior conversation as a
    list of {"role", "content"} dicts (Gradio type="messages"). Retrieves
    context, builds a grounded prompt, calls Groq, and returns Markdown.
    """
    client = get_client()
    if client is None:
        return (
            "⚠️ **No Groq API key found.** Add `GROQ_API_KEY` to a `.env` file "
            "(see `.env.example`) and restart the app."
        )

    # 1 & 2 — retrieve top-k chunks and assemble grounded context.
    hits = retrieve(message, top_k=TOP_K)
    context_block, references_block = build_context(hits)

    # 3 — structure the prompt: system + prior turns + current question.
    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(context=context_block)}]
    for turn in history:
        # Gradio's "messages" format is a {"role", "content"} dict; older
        # "tuples" format is a (user, assistant) pair. Handle both.
        if isinstance(turn, dict):
            messages.append({"role": turn["role"], "content": turn["content"]})
        elif isinstance(turn, (list, tuple)) and len(turn) == 2:
            user_msg, assistant_msg = turn
            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            if assistant_msg:
                messages.append({"role": "assistant", "content": assistant_msg})
    messages.append({"role": "user", "content": message})

    # 4 — call Groq, with graceful error handling so the UI never crashes.
    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=TEMPERATURE,
        )
        answer = completion.choices[0].message.content
    except Exception as exc:  # network / API errors shouldn't kill the chat
        return f"⚠️ **Error contacting Groq:** {exc}"

    # Append the deterministic source list (only when we actually had context).
    if references_block:
        answer = f"{answer}{references_block}"
    return answer


# --------------------------------------------------------------------------- #
# Interface
# --------------------------------------------------------------------------- #

EXAMPLE_QUESTIONS = [
    "What maintenance issues did students face at The Standard apartments?",
    "What are students saying about EV charging etiquette on campus?",
    "How does the RU Screw affect adjunct professors and students?",
    "What advice do graduates give about supply chain degree jobs?",
    "How do students defend the Rutgers-Camden campus?",
]


def build_demo():
    """Construct the gr.ChatInterface app."""
    return gr.ChatInterface(
        fn=predict,
        title="The Unofficial Guide to Rutgers 🎓",
        description=(
            "Ask about housing, classes, campuses, transit, and jobs — answered "
            "from real r/rutgers student discussions, with sources."
        ),
        examples=EXAMPLE_QUESTIONS,
    )


if __name__ == "__main__":
    build_demo().launch()
