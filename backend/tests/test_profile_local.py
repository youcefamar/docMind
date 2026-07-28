from scripts.profile_local import _build_parser


def test_p6_2_profile_flags_are_explicit():
    args = _build_parser().parse_args(
        [
            "--full-corpus",
            "--isolated-indexes",
            "--rebuild-indexes",
            "--reranker-path",
            "C:/models/reranker",
            "--profile-run-dir",
            "data/profiling/runs/example",
            "--skip-generation",
            "--skip-llm-load",
        ]
    )

    assert args.full_corpus is True
    assert args.isolated_indexes is True
    assert args.rebuild_indexes is True
    assert args.reranker_path == "C:/models/reranker"
    assert args.profile_run_dir == "data/profiling/runs/example"
    assert args.skip_llm_load is True
