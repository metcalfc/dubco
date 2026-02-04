"""Sidebar navigation widget."""

from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import Static, Tree

from dubco_cli.tui.state import FilterState, FilterType


class FilterChanged(Message):
    """Message sent when filter selection changes."""

    def __init__(self, filter_state: FilterState) -> None:
        self.filter_state = filter_state
        super().__init__()


class Sidebar(Static):
    """Navigation sidebar with filter tree."""

    DEFAULT_CSS = """
    Sidebar {
        width: 30;
        height: 100%;
        dock: left;
        border-right: solid $primary;
        padding: 1;
    }

    Sidebar Tree {
        height: 100%;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._tags: list[str] = []
        self._domains: list[str] = []

    def compose(self) -> ComposeResult:
        tree = Tree("Navigation", id="nav-tree")
        tree.root.expand()
        yield tree

    def on_mount(self) -> None:
        """Build initial tree structure."""
        self._build_tree()

    def _build_tree(self) -> None:
        """Build the navigation tree."""
        tree = self.query_one("#nav-tree", Tree)
        tree.clear()

        # All Links
        all_node = tree.root.add("All Links", data={"type": FilterType.ALL})
        all_node.allow_expand = False

        # By Tag
        tag_node = tree.root.add("By Tag", data={"type": "tag_parent"})
        for tag in self._tags:
            child = tag_node.add(f"  {tag}", data={"type": FilterType.TAG, "value": tag})
            child.allow_expand = False

        # By Domain
        domain_node = tree.root.add("By Domain", data={"type": "domain_parent"})
        for domain in self._domains:
            data = {"type": FilterType.DOMAIN, "value": domain}
            child = domain_node.add(f"  {domain}", data=data)
            child.allow_expand = False

        # Archived
        archived_node = tree.root.add("Archived", data={"type": FilterType.ARCHIVED})
        archived_node.allow_expand = False

        # Expand parent nodes
        tag_node.expand()
        domain_node.expand()

    def update_metadata(self, tags: list[str], domains: list[str]) -> None:
        """Update tags and domains in the tree."""
        self._tags = tags
        self._domains = domains
        self._build_tree()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle node selection."""
        node = event.node
        if node.data is None:
            return

        node_type = node.data.get("type")
        if node_type in ("tag_parent", "domain_parent"):
            return

        filter_state = FilterState()

        if node_type == FilterType.ALL:
            filter_state.filter_type = FilterType.ALL
        elif node_type == FilterType.TAG:
            filter_state.filter_type = FilterType.TAG
            filter_state.tag_name = node.data.get("value")
        elif node_type == FilterType.DOMAIN:
            filter_state.filter_type = FilterType.DOMAIN
            filter_state.domain = node.data.get("value")
        elif node_type == FilterType.ARCHIVED:
            filter_state.filter_type = FilterType.ARCHIVED

        self.post_message(FilterChanged(filter_state))
