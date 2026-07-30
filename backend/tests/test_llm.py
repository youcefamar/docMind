from services.llm import (
    DEFAULT_REFUSAL,
    LLMService,
    citation_is_supported,
    normalize_citation_labels,
    sanitize_citation_labels,
    strip_thinking_content,
    validate_citations,
)


def _source(index: int = 1, score: float = 0.9) -> dict:
    return {
        "doc_id": f"doc-{index}",
        "chunk_id": f"chunk-{index}",
        "filename": "policy.md",
        "category": "HR",
        "page_number": index,
        "excerpt": "Remote work is allowed two days per week.",
        "similarity": score,
    }


def test_validate_citations_rejects_unknown_labels():
    citations = validate_citations("Supported [S1], forged [S99], and invalid [S0].", [_source()])

    assert [citation.source_id for citation in citations] == ["S1"]
    assert citations[0].filename == "policy.md"


def test_sanitize_citation_labels_removes_forged_labels():
    assert sanitize_citation_labels("Answer [S1] [S99] [S0].", 1) == "Answer [S1] ."


def test_grouped_citation_labels_are_normalized_and_validated():
    sources = [_source(1), _source(2), _source(3)]
    answer = "Evidence [S1, S3]."

    assert normalize_citation_labels(answer) == "Evidence [S1] [S3]."
    assert sanitize_citation_labels(answer, len(sources)) == "Evidence [S1] [S3]."
    assert [citation.source_id for citation in validate_citations(answer, sources)] == ["S1", "S3"]


def test_strip_thinking_content_removes_complete_and_unfinished_blocks():
    assert strip_thinking_content("<think>private reasoning</think>Answer [S1]") == "Answer [S1]"
    assert strip_thinking_content("Answer [S1]<think>unfinished reasoning") == "Answer [S1]"


def test_local_service_never_returns_thinking_content_from_the_model():
    class ThinkingModel:
        def create_chat_completion(self, **_kwargs):
            return {
                "choices": [
                    {
                        "message": {
                            "content": "<think>private reasoning</think>\nRegression is covered [S1]."
                        }
                    }
                ],
                "usage": {"completion_tokens": 10},
            }

    service = LLMService(auto_load=False)
    service.local_llm = ThinkingModel()

    answer, _score, _label = service.generate_answer("Question", [_source()])

    assert answer == "Regression is covered [S1]."
    assert "think" not in answer


def test_local_service_refuses_response_containing_only_hidden_reasoning():
    class ThinkingOnlyModel:
        def create_chat_completion(self, **_kwargs):
            return {
                "choices": [{"message": {"content": "<think>private reasoning</think>"}}],
                "usage": {"completion_tokens": 4},
            }

    service = LLMService(auto_load=False)
    service.local_llm = ThinkingOnlyModel()

    answer, score, label = service.generate_answer("Question", [_source()])

    assert answer == DEFAULT_REFUSAL
    assert score == 0.15
    assert label == "Low"


def test_citation_support_signal_uses_excerpt_overlap():
    citation = validate_citations("Remote work is allowed. [S1]", [_source()])[0]
    assert citation_is_supported("Remote work is allowed. [S1]", citation) is True
    assert citation_is_supported("The cafeteria serves lunch. [S1]", citation) is False


def test_local_service_refuses_without_sources():
    service = LLMService(auto_load=False)

    answer, score, label = service.generate_answer("What is the policy?", [])

    assert answer == DEFAULT_REFUSAL
    assert score == 0.0
    assert label == "Low"


def test_local_service_uses_grounded_extractive_fallback_without_weights():
    service = LLMService(auto_load=False)

    answer, score, label = service.generate_answer("Can I work remotely?", [_source()])

    assert "Remote work is allowed" in answer
    assert "[S1]" in answer
    assert score == 0.95
    assert label == "High"


def test_local_service_builds_source_labelled_prompt():
    service = LLMService(auto_load=False)
    messages = service._build_messages("Question", [_source(), _source(2)], [])

    assert "SOURCE [S1]" in messages[-1]["content"]
    assert "SOURCE [S2]" in messages[-1]["content"]
    assert "Never create a label" in messages[0]["content"]


def test_local_service_refuses_low_score_context(monkeypatch):
    monkeypatch.setenv("DOCMIND_MIN_SOURCE_SCORE", "0.5")
    service = LLMService(auto_load=False)

    answer, score, label = service.generate_answer("Unknown", [_source(score=0.2)])

    assert answer == DEFAULT_REFUSAL
    assert score == 0.2
    assert label == "Low"


def test_local_service_accepts_rrf_quality_scores_with_profile_gate(monkeypatch):
    monkeypatch.delenv("DOCMIND_QUALITY_MIN_SOURCE_SCORE", raising=False)
    service = LLMService(auto_load=False)

    answer, score, label = service.generate_answer(
        "What is the policy?",
        [_source(score=1 / 61)],
        retrieval_profile="quality",
    )

    assert "Remote work is allowed" in answer
    assert score == 0.02
    assert label == "Medium"
