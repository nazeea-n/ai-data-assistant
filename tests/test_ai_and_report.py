import pytest

import ai
import analysis
import report


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeClient:
    def __init__(self, text="Revenue is highest in the North."):
        self.text = text
        self.last_prompt = None
        self.models = self

    def generate_content(self, model, contents):
        self.last_prompt = contents
        return FakeResponse(self.text)


def test_prompt_contains_question_context_and_history():
    prompt = ai.build_prompt("Which region is best?", "Rows: 10", [("user", "hi"), ("assistant", "hello")])
    assert "Which region is best?" in prompt and "Rows: 10" in prompt and "User: hi" in prompt


def test_ask_returns_text_from_client():
    client = FakeClient()
    answer = ai.ask("Which region is best?", "ctx", api_key="k", client=client)
    assert answer == "Revenue is highest in the North."
    assert "Which region is best?" in client.last_prompt


def test_ask_without_key_gives_friendly_error():
    with pytest.raises(ai.AIError, match="API key"):
        ai.ask("question", "ctx", api_key="")


def test_ask_with_empty_question():
    with pytest.raises(ai.AIError):
        ai.ask("  ", "ctx", api_key="k", client=FakeClient())


def test_empty_answer_is_an_error():
    with pytest.raises(ai.AIError):
        ai.ask("q", "ctx", api_key="k", client=FakeClient(text=""))


def test_pdf_report_is_created():
    df = analysis.load_file("sample_data/sales_sample.csv", "sales_sample.csv")
    pdf = report.build_pdf(df, "sales_sample.csv", ai_summary="**Summary** line one\nline two")
    assert pdf.startswith(b"%PDF") and len(pdf) > 10_000
