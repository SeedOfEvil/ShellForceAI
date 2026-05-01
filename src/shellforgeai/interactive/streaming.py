from __future__ import annotations

from rich.console import Console


class StreamRenderer:
    def __init__(self, console: Console, raw: bool = False) -> None:
        self.console = console
        self.raw = raw

    def render(self, text: str, raw_text: str | None = None) -> None:
        self.console.print(text)
        if self.raw and raw_text:
            self.console.print(raw_text)
