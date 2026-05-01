from typer.testing import CliRunner

from shellforgeai.cli import app
from shellforgeai.llm.codex_events import parse_codex_jsonl
from shellforgeai.llm.schemas import ModelResponse

runner = CliRunner()


def test_version_output_contains_name() -> None:
    r = runner.invoke(app, ["--version"])
    assert r.exit_code == 0
    assert "ShellForgeAI" in r.stdout


def test_codex_jsonl_parser_final_message_and_usage() -> None:
    raw = "\n".join(
        [
            '{"type":"thread.started","thread_id":"t_1"}',
            '{"type":"item.completed","item":{"type":"agent_message","text":"Hello."}}',
            '{"type":"turn.completed","usage":{"input_tokens":10,"cached_input_tokens":2,"output_tokens":3,"reasoning_output_tokens":0}}',
        ]
    )
    p = parse_codex_jsonl(raw)
    assert p.final_text == "Hello."
    assert p.thread_id == "t_1"
    assert p.usage.input_tokens == 10


def test_codex_jsonl_parser_malformed_line_warning() -> None:
    p = parse_codex_jsonl('not-json\n{"type":"turn.started"}')
    assert p.warnings


def test_model_test_accepts_positional_prompt() -> None:
    from shellforgeai import cli

    class _P:
        def complete(self, req):
            assert "Reply exactly" in req.prompt
            return ModelResponse(
                provider="openai-codex",
                model="gpt-5.5",
                text="ShellForgeAI Codex provider online.",
                ok=True,
                usage={
                    "input_tokens": 1,
                    "cached_input_tokens": 0,
                    "output_tokens": 1,
                    "reasoning_output_tokens": 0,
                },
            )

    cli.build_provider = lambda settings: _P()
    r = runner.invoke(app, ["model", "test", "Reply exactly: ShellForgeAI Codex provider online."])
    assert r.exit_code == 0
