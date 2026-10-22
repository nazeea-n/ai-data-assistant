"""Gemini integration. The AI is given a text summary of the data, never the raw file."""
import os

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

INSTRUCTIONS = (
    "You are a careful data analyst. You are given a summary of a dataset and a question. "
    "Answer ONLY from the summary. If the summary does not contain enough information, say so "
    "and explain what extra information would be needed. Never invent numbers. "
    "Keep answers short, in plain English, and use bullet points when listing."
)


class AIError(Exception):
    """A problem the user can understand (missing key, network, quota...)."""


def build_prompt(question, context, history=None):
    parts = [INSTRUCTIONS, "", "DATASET SUMMARY:", context, ""]
    if history:
        parts.append("EARLIER CONVERSATION:")
        for role, text in history[-6:]:
            parts.append(f"{'User' if role == 'user' else 'Assistant'}: {text}")
        parts.append("")
    parts += [f"QUESTION: {question}", "ANSWER:"]
    return "\n".join(parts)


def ask(question, context, api_key, history=None, model=None, client=None):
    """Send one question to Gemini. `client` can be passed in for testing."""
    if not question or not question.strip():
        raise AIError("Please type a question.")
    if client is None:
        if not api_key:
            raise AIError("Add your Gemini API key in the sidebar first.")
        try:
            from google import genai
        except ImportError as exc:
            raise AIError("The 'google-genai' package is not installed. Run: pip install -r requirements.txt") from exc
        client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model=model or DEFAULT_MODEL, contents=build_prompt(question, context, history))
    except Exception as exc:  # network, quota, bad key, bad model name
        raise AIError(f"Gemini request failed: {exc}") from exc
    text = getattr(response, "text", None)
    if not text:
        raise AIError("Gemini returned an empty answer. Try rephrasing the question.")
    return text.strip()


def summarize(context, api_key, **kwargs):
    return ask("Give a short executive summary of this dataset: what it is about, the 3 most "
               "important findings, data quality problems, and 3 suggested next steps.",
               context, api_key, **kwargs)
