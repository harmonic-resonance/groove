"""
viewers.py - Modal viewers for Groove chord sheets (CSML) and musicological studies (Markdown).
"""

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Header, Footer, Label, Markdown, Static


class ContentModal(ModalScreen):
    """Full-screen or large modal viewer for text/markdown files like README.md or chords.csml."""

    CSS = """
    ContentModal {
        align: center middle;
    }

    #modal-container {
        width: 85%;
        height: 85%;
        background: $surface;
        border: thick $accent;
        padding: 1 2;
    }

    #modal-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        border-bottom: solid $accent-darken-2;
    }

    #content-scroll {
        height: 1fr;
    }

    #raw-content {
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape,q", "close_modal", "Close", show=True),
        Binding("h", "close_modal", "Back", show=False),
    ]

    def __init__(
        self,
        title: str,
        content: str,
        is_markdown: bool = True,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.modal_title = title
        self.content = content
        self.is_markdown = is_markdown

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label(self.modal_title, id="modal-title")
            with ScrollableContainer(id="content-scroll"):
                if self.is_markdown:
                    yield Markdown(self.content)
                else:
                    yield Static(self.content, id="raw-content")

    def action_close_modal(self) -> None:
        self.dismiss()
