from scripts.benchmark_nebius import (
    NebiusBenchmarkRunner,
    _build_parser,
    format_markdown_table,
)


def test_benchmark_nebius_parser():
    parser = _build_parser()
    args = parser.parse_args(["--repetitions", "5", "--mock", "--question", "Test question?"])

    assert args.repetitions == 5
    assert args.mock is True
    assert args.question == "Test question?"


def test_benchmark_runner_mock_metrics():
    runner = NebiusBenchmarkRunner(mock=True)
    summary = runner.run_benchmark("How does PTO work?", repetitions=2)

    assert "metrics" in summary
    metrics = summary["metrics"]

    assert "local_cpu" in metrics
    assert "tier1_nano" in metrics
    assert "tier2_ultra" in metrics
    assert "dual_nemotron_pipeline" in metrics

    assert metrics["tier1_nano"]["avg_latency_ms"] < 100.0  # Sub-100ms guarantee
    assert metrics["tier2_ultra"]["avg_tps"] > 50.0  # High token throughput on GPU
    assert "x" in metrics["dual_nemotron_pipeline"]["speedup_vs_cpu"]


def test_benchmark_markdown_formatting():
    runner = NebiusBenchmarkRunner(mock=True)
    summary = runner.run_benchmark("Test query", repetitions=1)
    markdown = format_markdown_table(summary)

    assert "# ⚡ DocMind Performance Benchmark" in markdown
    assert "Dual-Nemotron Pipeline" in markdown
    assert "credit savings" in markdown
