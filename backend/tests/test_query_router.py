from models.contracts import QueryRoutingResult
from services.query_router import QueryRouterService


def test_query_router_passthrough_when_disabled(monkeypatch):
    monkeypatch.setenv("DOCMIND_QUERY_ROUTING_ENABLED", "false")
    router = QueryRouterService()

    result = router.route_query("Where is the office?")
    assert result.router_applied is False
    assert result.refined_query == "Where is the office?"
    assert result.model == "passthrough"


def test_query_router_empty_question():
    router = QueryRouterService()

    result = router.route_query("   ")
    assert result.router_applied is False
    assert result.refined_query == "   "


def test_query_router_passthrough_when_no_client():
    class FakeLLM:
        nebius_client = None

    router = QueryRouterService(FakeLLM())
    result = router.route_query("What is the refund policy?", current_category="Finance")

    assert result.router_applied is False
    assert result.refined_query == "What is the refund policy?"
    assert result.category == "Finance"
    assert result.model == "extractive-passthrough"


def test_query_router_successful_reformulation():
    class FakeUsage:
        prompt_tokens = 32
        completion_tokens = 18

    class FakeMessage:
        content = '{"search_terms": "remote telework WFH policy guidelines", "category": "HR"}'

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]
        usage = FakeUsage()

    class FakeCompletions:
        def create(self, **kwargs):
            return FakeResponse()

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAI:
        chat = FakeChat()

    class FakeLLM:
        nebius_client = FakeOpenAI()

    router = QueryRouterService(FakeLLM())
    result = router.route_query(
        "Can I work from home?",
        current_category="All",
        valid_categories=("General", "HR", "Tech", "Finance"),
    )

    assert isinstance(result, QueryRoutingResult)
    assert result.router_applied is True
    assert result.refined_query == "remote telework WFH policy guidelines"
    assert result.category == "HR"
    assert result.prompt_tokens == 32
    assert result.completion_tokens == 18
    assert result.model == router.fast_model


def test_query_router_preserves_explicit_user_category():
    class FakeUsage:
        prompt_tokens = 20
        completion_tokens = 10

    class FakeMessage:
        content = '{"search_terms": "employment contracts", "category": "HR"}'

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]
        usage = FakeUsage()

    class FakeOpenAI:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return FakeResponse()

    class FakeLLM:
        nebius_client = FakeOpenAI()

    router = QueryRouterService(FakeLLM())
    # User explicitly requested "Legal", model suggested "HR" -> User's explicit filter must win
    result = router.route_query(
        "Contract rules",
        current_category="Legal",
        valid_categories=("General", "HR", "Legal"),
    )

    assert result.category == "Legal"
    assert result.refined_query == "employment contracts"


def test_query_router_extracts_json_from_markdown():
    markdown_content = """```json
    {
        "search_terms": "network architecture VPN setup",
        "category": "Tech"
    }
    ```"""

    class FakeMessage:
        content = markdown_content

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]
        usage = None

    class FakeOpenAI:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return FakeResponse()

    class FakeLLM:
        nebius_client = FakeOpenAI()

    router = QueryRouterService(FakeLLM())
    result = router.route_query(
        "How to connect to VPN?",
        current_category="All",
        valid_categories=("General", "Tech"),
    )

    assert result.router_applied is True
    assert result.refined_query == "network architecture VPN setup"
    assert result.category == "Tech"


def test_query_router_handles_malformed_response_safely():
    class FakeMessage:
        content = "I cannot generate valid JSON for this query."

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]
        usage = None

    class FakeOpenAI:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return FakeResponse()

    class FakeLLM:
        nebius_client = FakeOpenAI()

    router = QueryRouterService(FakeLLM())
    result = router.route_query(
        "Original question",
        current_category="All",
        valid_categories=("General", "HR"),
    )

    assert result.router_applied is True
    assert result.refined_query == "Original question"
    assert result.category == "All"


def test_filter_and_rerank_chunks():
    router = QueryRouterService()
    chunks = [
        {"doc_id": "1", "similarity": 0.45},
        {"doc_id": "2", "similarity": 0.88},
        {"doc_id": "3", "similarity": 0.12},
        {"doc_id": "4", "similarity": 0.72},
        {"doc_id": "5", "similarity": 0.65},
        {"doc_id": "6", "similarity": 0.95},
    ]

    filtered = router.filter_and_rerank_chunks("test query", chunks, target_k=3)
    assert len(filtered) == 3
    assert [c["doc_id"] for c in filtered] == ["6", "2", "4"]
