"""
sort_modal.py - Modal screen for selecting a DataTable column to sort.
Directly adapted from Seer Navigator.
"""

from typing import Dict, List, Optional, Tuple, Union

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView
from textual.widgets._data_table import ColumnKey


class SortModal(ModalScreen[Optional[ColumnKey]]):
    """Modal dialog for selecting a column to sort. Returns the selected ColumnKey or None."""

    CSS = """
    SortModal {
        align: center middle;
    }

    #dialog {
        padding: 1 2;
        width: auto;
        min-width: 32;
        max-width: 60;
        height: auto;
        max-height: 80%;
        border: thick $accent;
        background: $surface;
    }

    #dialog > Label {
        width: 100%;
        text-align: center;
        margin-bottom: 1;
        text-style: bold;
    }

    #sort-list {
        border: none;
        background: $surface;
        height: auto;
        max-height: 15;
    }

    #sort-list > ListItem {
        padding: 0 1;
        height: 1;
    }

    #sort-list > ListItem.--highlight {
        background: $accent;
        color: $text;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel_sort", "Cancel", show=True),
        Binding("q", "cancel_sort", "Cancel", show=False),
    ]

    def __init__(
        self,
        columns: Dict[ColumnKey, object],
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.column_options: List[Tuple[str, ColumnKey]] = []

        for col_key, column_obj in columns.items():
            column_label = "Unknown"
            if hasattr(column_obj, "label"):
                label_obj = column_obj.label
                column_label = getattr(label_obj, "plain", str(label_obj))
            elif hasattr(column_obj, "name"):
                column_label = column_obj.name
            else:
                column_label = str(col_key)

            self.column_options.append((column_label, col_key))

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("Sort By Column:")
            with ListView(id="sort-list"):
                for idx, (label, col_key) in enumerate(self.column_options):
                    yield ListItem(Label(label), id=f"col-{idx}")

    def on_mount(self) -> None:
        list_view = self.query_one(ListView)
        list_view.focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected_index = self.query_one(ListView).index
        if selected_index is not None and 0 <= selected_index < len(self.column_options):
            selected_key = self.column_options[selected_index][1]
            self.dismiss(selected_key)
        else:
            self.dismiss(None)

    def action_cancel_sort(self) -> None:
        self.dismiss(None)
