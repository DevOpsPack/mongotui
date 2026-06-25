from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.containers import Vertical, Horizontal, Center, Container
from textual.widgets import (
    Header, Footer, Static, Input, Button, DataTable, Label, Select,
    Tree, TabbedContent, TabPane, ContentSwitcher,
)
from textual.binding import Binding
from textual.reactive import reactive
from textual_plotext import PlotextPlot

from mongotui.mongo import MongoAdmin

MAX_HISTORY = 60

MONGO_ROLES = [
    "read", "readWrite", "dbAdmin", "dbOwner", "userAdmin",
    "clusterAdmin", "clusterManager", "clusterMonitor", "hostManager",
    "readAnyDatabase", "readWriteAnyDatabase", "dbAdminAnyDatabase",
    "userAdminAnyDatabase", "backup", "restore", "root",
]
ROLE_OPTIONS = [(role, role) for role in MONGO_ROLES]


# ─── Connect Screen ─────────────────────────────────────────────────────────

class ConnectScreen(Screen):
    BINDINGS = [Binding("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Center():
            with Vertical(id="connect-form"):
                yield Static("🍃 MongoTUI", id="connect-logo")
                yield Label("New Connection")
                yield Input(
                    value="mongodb://admin:admin@localhost:27017/?authSource=admin",
                    placeholder="mongodb://user:pass@host:port/?authSource=admin",
                    id="uri-input",
                )
                yield Button("Connect", variant="primary", id="connect-btn")
                yield Static("", id="connect-status")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "connect-btn":
            uri = self.query_one("#uri-input", Input).value
            status = self.query_one("#connect-status", Static)
            if "authSource" not in uri and "@" in uri:
                status.update("⚠ Add ?authSource=admin to your URI")
                return
            try:
                admin = MongoAdmin(uri)
                if admin.ping():
                    self.app.mongo = admin
                    self.app.push_screen(DashboardScreen())
                else:
                    status.update("✗ Authentication failed")
            except Exception as e:
                status.update(f"✗ {e}")


# ─── Dashboard (Compass-like layout) ────────────────────────────────────────

class DashboardScreen(Screen):
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="dashboard"):
            with Vertical(id="sidebar"):
                yield Static("Navigation", id="sidebar-title")
                yield Tree("Server", id="nav-tree")
            with Vertical(id="content"):
                with TabbedContent(id="tabs"):
                    with TabPane("Overview", id="tab-overview"):
                        yield DataTable(id="overview-table")
                    with TabPane("Databases", id="tab-databases"):
                        with Horizontal(id="db-toolbar"):
                            yield Button("Create DB", variant="primary", id="btn-create-db")
                            yield Button("Drop DB", variant="error", id="btn-drop-db")
                        yield DataTable(id="db-table")
                    with TabPane("Collections", id="tab-collections"):
                        yield Static("Select a database from the sidebar", id="col-hint")
                        yield DataTable(id="col-table")
                    with TabPane("Documents", id="tab-documents"):
                        yield Static("Select a collection from the sidebar", id="doc-hint")
                        with Horizontal(id="doc-toolbar"):
                            yield Input(placeholder='Filter JSON (e.g. {"name": "test"})', id="doc-filter")
                            yield Button("Find", variant="primary", id="btn-find")
                        yield DataTable(id="doc-table")
                    with TabPane("Document", id="tab-doc-detail"):
                        yield Static("Select a row in Documents tab", id="doc-detail-hint")
                        yield Static("", id="doc-detail")
                    with TabPane("Aggregation", id="tab-aggregation"):
                        yield Static("Select a collection, then enter pipeline", id="agg-hint")
                        yield Input(
                            placeholder='Pipeline JSON (e.g. [{"$match": {"status": "A"}}, {"$group": {"_id": "$city", "total": {"$sum": 1}}}])',
                            id="agg-input",
                        )
                        yield Button("Run Pipeline", variant="primary", id="btn-run-agg")
                        yield DataTable(id="agg-table")
                    with TabPane("Indexes", id="tab-indexes"):
                        yield Static("Select a collection from the sidebar", id="idx-hint")
                        with Horizontal(id="idx-toolbar"):
                            yield Button("Create", variant="primary", id="btn-create-idx")
                            yield Button("Drop", variant="error", id="btn-drop-idx")
                            yield Button("+ Search", id="btn-create-search-idx")
                            yield Button("x Search", variant="error", id="btn-drop-search-idx")
                        yield DataTable(id="idx-table")
                        yield Static("", id="search-idx-hint")
                        yield DataTable(id="search-idx-table")
                    with TabPane("Users", id="tab-users"):
                        with Horizontal(id="users-toolbar"):
                            yield Button("Create", variant="primary", id="btn-create-user")
                            yield Button("Password", id="btn-reset-pwd")
                            yield Button("Grant", id="btn-grant-role")
                            yield Button("Revoke", id="btn-revoke-role")
                            yield Button("Delete", variant="error", id="btn-delete-user")
                        yield DataTable(id="users-table")
                    with TabPane("Performance", id="tab-perf"):
                        with Vertical(id="perf-charts"):
                            yield PlotextPlot(id="plot-connections")
                            yield PlotextPlot(id="plot-ops")
                            yield PlotextPlot(id="plot-memory")
        yield Footer()

    def on_mount(self) -> None:
        self._build_tree()
        self._load_overview()
        self._load_databases()
        self._load_users()
        self._perf_history = {"connections": [], "ops": [], "memory": [], "prev_ops": 0}
        self._sample_perf()
        self.set_interval(2, self._sample_perf)

    def _build_tree(self) -> None:
        tree = self.query_one("#nav-tree", Tree)
        tree.clear()
        tree.root.expand()

        tree.root.add("Overview", data="overview")
        tree.root.add("Users", data="users")
        tree.root.add("Performance", data="perf")

        db_node = tree.root.add("Databases", data="databases")
        db_node.expand()
        try:
            for db_name in self.app.mongo.list_databases():
                db_child = db_node.add(db_name, data=f"db:{db_name}")
                try:
                    for col_name in self.app.mongo.list_collections(db_name):
                        db_child.add(col_name, data=f"col:{db_name}:{col_name}")
                except Exception:
                    pass
        except Exception:
            pass

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        data = event.node.data
        if not data:
            return
        tabs = self.query_one("#tabs", TabbedContent)
        if data == "overview":
            tabs.active = "tab-overview"
        elif data == "databases":
            tabs.active = "tab-databases"
        elif data == "users":
            tabs.active = "tab-users"
        elif data == "perf":
            tabs.active = "tab-perf"
        elif data.startswith("db:"):
            db_name = data.split(":", 1)[1]
            self._load_collections(db_name)
            tabs.active = "tab-collections"
        elif data.startswith("col:"):
            _, db_name, col_name = data.split(":", 2)
            self._load_documents(db_name, col_name)
            self._load_indexes(db_name, col_name)
            tabs.active = "tab-documents"

    # ── Overview Tab ──

    def _load_overview(self) -> None:
        table = self.query_one("#overview-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Metric", "Value")
        try:
            status = self.app.mongo.server_status()
            table.add_row("Host", status.get("host", "N/A"))
            table.add_row("Version", status.get("version", "N/A"))
            table.add_row("Uptime", f"{status.get('uptime', 0)} seconds")
            conns = status.get("connections", {})
            table.add_row("Connections", f"{conns.get('current', 0)} / {conns.get('available', 0)}")
            mem = status.get("mem", {})
            table.add_row("Memory (resident)", f"{mem.get('resident', 0)} MB")
            table.add_row("Memory (virtual)", f"{mem.get('virtual', 0)} MB")
            table.add_row("Storage Engine", status.get("storageEngine", {}).get("name", "N/A"))
            opcounters = status.get("opcounters", {})
            table.add_row("Total Operations",
                          f"I:{opcounters.get('insert', 0)} Q:{opcounters.get('query', 0)} "
                          f"U:{opcounters.get('update', 0)} D:{opcounters.get('delete', 0)}")

            rs = self.app.mongo.replica_set_status()
            if rs:
                table.add_row("Replica Set", rs.get("set", "N/A"))
                members = len(rs.get("members", []))
                table.add_row("RS Members", str(members))
            else:
                table.add_row("Replica Set", "Standalone")

            dbs = self.app.mongo.list_databases()
            table.add_row("Databases", str(len(dbs)))
        except Exception as e:
            table.add_row("Error", str(e))

    # ── Databases Tab ──

    def _load_databases(self) -> None:
        table = self.query_one("#db-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Database", "Collections", "Size (MB)", "Storage (MB)")
        table.cursor_type = "row"
        try:
            for db_name in self.app.mongo.list_databases():
                stats = self.app.mongo.db_stats(db_name)
                collections = len(self.app.mongo.list_collections(db_name))
                data_size = f"{stats.get('dataSize', 0) / (1024 * 1024):.2f}"
                storage_size = f"{stats.get('storageSize', 0) / (1024 * 1024):.2f}"
                table.add_row(db_name, str(collections), data_size, storage_size, key=db_name)
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    # ── Collections Tab ──

    def _load_collections(self, db_name: str) -> None:
        self.query_one("#col-hint", Static).update(f"Database: {db_name}")
        table = self.query_one("#col-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Collection", "Documents", "Size (KB)")
        table.cursor_type = "row"
        try:
            db = self.app.mongo.client[db_name]
            for col_name in self.app.mongo.list_collections(db_name):
                stats = db.command("collStats", col_name)
                count = stats.get("count", 0)
                size_kb = f"{stats.get('size', 0) / 1024:.2f}"
                table.add_row(col_name, str(count), size_kb, key=f"{db_name}:{col_name}")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    # ── Documents Tab ──

    def _load_documents(self, db_name: str, col_name: str, query_filter: dict | None = None) -> None:
        self._doc_db = db_name
        self._doc_col = col_name
        filter_desc = f" | filter: {query_filter}" if query_filter else ""
        self.query_one("#doc-hint", Static).update(f"{db_name}.{col_name} (limit 50){filter_desc}")
        table = self.query_one("#doc-table", DataTable)
        table.clear(columns=True)
        try:
            db = self.app.mongo.client[db_name]
            self._docs = list(db[col_name].find(query_filter or {}).limit(50))
            if not self._docs:
                table.add_columns("Info")
                table.add_row("No documents found")
                return
            keys = list(self._docs[0].keys())[:8]
            table.add_columns(*keys)
            for i, doc in enumerate(self._docs):
                row = [str(doc.get(k, ""))[:50] for k in keys]
                table.add_row(*row, key=str(i))
        except Exception as e:
            table.add_columns("Error")
            table.add_row(str(e))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id == "doc-table" and hasattr(self, "_docs"):
            import json
            try:
                idx = int(str(event.row_key.value))
                doc = self._docs[idx]
                # Convert ObjectId etc. to string for display
                formatted = json.dumps(doc, indent=2, default=str)
                self.query_one("#doc-detail-hint", Static).update(
                    f"{self._doc_db}.{self._doc_col} - Document {idx}"
                )
                self.query_one("#doc-detail", Static).update(formatted)
                self.query_one("#tabs", TabbedContent).active = "tab-doc-detail"
            except (ValueError, IndexError):
                pass

    # ── Aggregation Tab ──

    def _run_aggregation(self, pipeline: list) -> None:
        table = self.query_one("#agg-table", DataTable)
        table.clear(columns=True)
        if not hasattr(self, "_doc_db"):
            table.add_columns("Error")
            table.add_row("Select a collection first")
            return
        try:
            db = self.app.mongo.client[self._doc_db]
            results = list(db[self._doc_col].aggregate(pipeline))
            if not results:
                table.add_columns("Info")
                table.add_row("No results")
                return
            keys = list(results[0].keys())[:10]
            table.add_columns(*keys)
            for doc in results[:100]:
                row = [str(doc.get(k, ""))[:60] for k in keys]
                table.add_row(*row)
            self.query_one("#agg-hint", Static).update(
                f"{self._doc_db}.{self._doc_col} | {len(results)} results"
            )
        except Exception as e:
            table.add_columns("Error")
            table.add_row(str(e))

    # ── Indexes Tab ──

    def _load_indexes(self, db_name: str, col_name: str) -> None:
        self._idx_db = db_name
        self._idx_col = col_name
        stats = self.app.mongo.index_stats(db_name, col_name)
        total_size = stats["totalIndexSize"]
        self.query_one("#idx-hint", Static).update(
            f"{db_name}.{col_name} | {stats['nindexes']} indexes | "
            f"Total size: {total_size / 1024:.1f} KB"
        )
        table = self.query_one("#idx-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Name", "Keys", "Unique", "Size (KB)")
        table.cursor_type = "row"
        try:
            index_sizes = stats["indexSizes"]
            for idx in self.app.mongo.list_indexes(db_name, col_name):
                name = idx.get("name", "")
                keys = ", ".join(f"{k}:{v}" for k, v in idx.get("key", {}).items())
                unique = "Yes" if idx.get("unique", False) else "No"
                size_kb = f"{index_sizes.get(name, 0) / 1024:.2f}"
                table.add_row(name, keys, unique, size_kb, key=name)
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

        # Search indexes
        search_table = self.query_one("#search-idx-table", DataTable)
        search_table.clear(columns=True)
        search_table.add_columns("Name", "Status", "Type", "Fields")
        search_table.cursor_type = "row"
        try:
            for sidx in self.app.mongo.list_search_indexes(db_name, col_name):
                name = sidx.get("name", "")
                status = sidx.get("status", "N/A")
                idx_type = sidx.get("type", "search")
                mappings = sidx.get("latestDefinition", {}).get("mappings", {})
                if mappings.get("dynamic", False):
                    fields = "dynamic"
                else:
                    fields = ", ".join(mappings.get("fields", {}).keys())
                search_table.add_row(name, status, idx_type, fields, key=name)
            count = search_table.row_count
            self.query_one("#search-idx-hint", Static).update(f"Search Indexes: {count}")
        except Exception:
            self.query_one("#search-idx-hint", Static).update("Search Indexes: N/A (requires mongot)")

    def _selected_index(self) -> str | None:
        table = self.query_one("#idx-table", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        return str(row_key.value)

    def _selected_search_index(self) -> str | None:
        table = self.query_one("#search-idx-table", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        return str(row_key.value)

    # ── Users Tab ──

    def _load_users(self) -> None:
        table = self.query_one("#users-table", DataTable)
        table.clear(columns=True)
        table.add_columns("User", "Database", "Roles")
        table.cursor_type = "row"
        try:
            for user in self.app.mongo.list_users():
                roles = ", ".join(f"{r['role']}@{r['db']}" for r in user.get("roles", []))
                table.add_row(user["user"], user.get("db", ""), roles, key=user["user"])
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def _selected_user(self) -> str | None:
        table = self.query_one("#users-table", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        return str(row_key.value)

    # ── Performance Tab ──

    def _sample_perf(self) -> None:
        try:
            status = self.app.mongo.server_status()
        except Exception:
            return

        h = self._perf_history
        h["connections"].append(status.get("connections", {}).get("current", 0))
        if len(h["connections"]) > MAX_HISTORY:
            h["connections"] = h["connections"][-MAX_HISTORY:]

        opcounters = status.get("opcounters", {})
        total_ops = sum(opcounters.get(k, 0) for k in ("insert", "query", "update", "delete"))
        ops_diff = total_ops - h["prev_ops"] if h["prev_ops"] else 0
        h["prev_ops"] = total_ops
        h["ops"].append(max(ops_diff, 0))
        if len(h["ops"]) > MAX_HISTORY:
            h["ops"] = h["ops"][-MAX_HISTORY:]

        h["memory"].append(status.get("mem", {}).get("resident", 0))
        if len(h["memory"]) > MAX_HISTORY:
            h["memory"] = h["memory"][-MAX_HISTORY:]

        self._render_perf()

    def _render_perf(self) -> None:
        h = self._perf_history

        plot_conn = self.query_one("#plot-connections", PlotextPlot)
        plt = plot_conn.plt
        plt.clear_data()
        plt.clear_figure()
        plt.title("Connections")
        plt.plot(h["connections"], marker="braille")
        plot_conn.refresh()

        plot_ops = self.query_one("#plot-ops", PlotextPlot)
        plt = plot_ops.plt
        plt.clear_data()
        plt.clear_figure()
        plt.title("Operations / 2s")
        plt.plot(h["ops"], marker="braille")
        plot_ops.refresh()

        plot_mem = self.query_one("#plot-memory", PlotextPlot)
        plt = plot_mem.plt
        plt.clear_data()
        plt.clear_figure()
        plt.title("Memory (MB)")
        plt.plot(h["memory"], marker="braille")
        plot_mem.refresh()

    # ── Button handlers ──

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "btn-create-user":
                self.app.push_screen(CreateUserModal(), callback=self._on_user_change)
            case "btn-delete-user":
                username = self._selected_user()
                if username:
                    self.app.push_screen(ConfirmDeleteModal(username), callback=self._on_delete_user)
            case "btn-reset-pwd":
                username = self._selected_user()
                if username:
                    self.app.push_screen(ResetPasswordModal(username), callback=self._on_user_change)
            case "btn-grant-role":
                username = self._selected_user()
                if username:
                    self.app.push_screen(GrantRoleModal(username), callback=self._on_user_change)
            case "btn-revoke-role":
                username = self._selected_user()
                if username:
                    self.app.push_screen(RevokeRoleModal(username), callback=self._on_user_change)
            case "btn-create-idx":
                if hasattr(self, "_idx_db"):
                    self.app.push_screen(
                        CreateIndexModal(self._idx_db, self._idx_col),
                        callback=self._on_index_change,
                    )
            case "btn-drop-idx":
                idx_name = self._selected_index()
                if idx_name and hasattr(self, "_idx_db"):
                    if idx_name == "_id_":
                        self.notify("Cannot drop _id_ index", severity="warning")
                    else:
                        try:
                            self.app.mongo.drop_index(self._idx_db, self._idx_col, idx_name)
                            self._load_indexes(self._idx_db, self._idx_col)
                            self.notify(f"Dropped index {idx_name}")
                        except Exception as e:
                            self.notify(f"Error: {e}", severity="error")
            case "btn-create-db":
                self.app.push_screen(CreateDBModal(), callback=self._on_db_change)
            case "btn-drop-db":
                db_name = self._selected_db()
                if db_name:
                    self.app.push_screen(ConfirmDropDBModal(db_name), callback=self._on_drop_db)
            case "btn-create-search-idx":
                if hasattr(self, "_idx_db"):
                    self.app.push_screen(
                        CreateSearchIndexModal(self._idx_db, self._idx_col),
                        callback=self._on_index_change,
                    )
            case "btn-drop-search-idx":
                name = self._selected_search_index()
                if name and hasattr(self, "_idx_db"):
                    try:
                        self.app.mongo.drop_search_index(self._idx_db, self._idx_col, name)
                        self._load_indexes(self._idx_db, self._idx_col)
                        self.notify(f"Dropped search index {name}")
                    except Exception as e:
                        self.notify(f"Error: {e}", severity="error")
            case "btn-find":
                if hasattr(self, "_doc_db"):
                    import json
                    filter_str = self.query_one("#doc-filter", Input).value.strip()
                    try:
                        query_filter = json.loads(filter_str) if filter_str else None
                    except json.JSONDecodeError:
                        self.notify("Invalid JSON filter", severity="warning")
                        return
                    self._load_documents(self._doc_db, self._doc_col, query_filter)
            case "btn-run-agg":
                import json
                pipeline_str = self.query_one("#agg-input", Input).value.strip()
                if not pipeline_str:
                    self.notify("Enter a pipeline", severity="warning")
                    return
                try:
                    pipeline = json.loads(pipeline_str)
                except json.JSONDecodeError:
                    self.notify("Invalid JSON pipeline", severity="warning")
                    return
                if not isinstance(pipeline, list):
                    self.notify("Pipeline must be a JSON array", severity="warning")
                    return
                self._run_aggregation(pipeline)

    def _on_user_change(self, result: bool) -> None:
        if result:
            self._load_users()
            self.notify("Done")

    def _on_index_change(self, result: bool) -> None:
        if result and hasattr(self, "_idx_db"):
            self._load_indexes(self._idx_db, self._idx_col)
            self.notify("Index created")

    def _on_db_change(self, result: bool) -> None:
        if result:
            self._load_databases()
            self._build_tree()
            self.notify("Database created")

    def _on_drop_db(self, result: bool) -> None:
        if result:
            db_name = self._selected_db()
            if db_name:
                try:
                    self.app.mongo.drop_database(db_name)
                    self._load_databases()
                    self._build_tree()
                    self.notify(f"Dropped {db_name}")
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")

    def _selected_db(self) -> str | None:
        table = self.query_one("#db-table", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        return str(row_key.value)

    def _on_delete_user(self, result: bool) -> None:
        if result:
            username = self._selected_user()
            if username:
                try:
                    self.app.mongo.delete_user(username)
                    self._load_users()
                    self.notify(f"Deleted {username}")
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")

    def action_refresh(self) -> None:
        self._build_tree()
        self._load_overview()
        self._load_databases()
        self._load_users()
        self.notify("Refreshed")


# ─── Modals ──────────────────────────────────────────────────────────────────

class CreateUserModal(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label("Create New User")
            yield Input(placeholder="Username", id="new-username")
            yield Input(placeholder="Password", password=True, id="new-password")
            yield Select(ROLE_OPTIONS, prompt="Select role", id="new-role")
            yield Input(placeholder="Database (e.g. admin)", id="new-db")
            with Horizontal(id="modal-buttons"):
                yield Button("Create", variant="primary", id="create-confirm")
                yield Button("Cancel", id="create-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create-confirm":
            username = self.query_one("#new-username", Input).value
            password = self.query_one("#new-password", Input).value
            role_select = self.query_one("#new-role", Select)
            role = role_select.value if role_select.value != Select.BLANK else "readWrite"
            db = self.query_one("#new-db", Input).value or "admin"
            try:
                self.app.mongo.create_user(username, password, [{"role": role, "db": db}])
                self.dismiss(True)
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")
        else:
            self.dismiss(False)

    def action_cancel(self) -> None:
        self.dismiss(False)


class ResetPasswordModal(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, username: str):
        super().__init__()
        self.username = username

    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label(f"Reset password: {self.username}")
            yield Input(placeholder="New password", password=True, id="reset-pw")
            with Horizontal(id="modal-buttons"):
                yield Button("Reset", variant="warning", id="reset-confirm")
                yield Button("Cancel", id="reset-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "reset-confirm":
            pw = self.query_one("#reset-pw", Input).value
            try:
                self.app.mongo.reset_password(self.username, pw)
                self.dismiss(True)
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")
        else:
            self.dismiss(False)

    def action_cancel(self) -> None:
        self.dismiss(False)


class GrantRoleModal(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, username: str):
        super().__init__()
        self.username = username

    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label(f"Grant role to: {self.username}")
            yield Select(ROLE_OPTIONS, prompt="Select role", id="grant-role")
            yield Input(placeholder="Database (e.g. admin)", id="grant-db")
            with Horizontal(id="modal-buttons"):
                yield Button("Grant", variant="primary", id="grant-confirm")
                yield Button("Cancel", id="grant-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "grant-confirm":
            role_select = self.query_one("#grant-role", Select)
            role = role_select.value if role_select.value != Select.BLANK else None
            if not role:
                self.notify("Select a role", severity="warning")
                return
            db = self.query_one("#grant-db", Input).value or "admin"
            try:
                self.app.mongo.grant_roles(self.username, [{"role": role, "db": db}])
                self.dismiss(True)
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")
        else:
            self.dismiss(False)

    def action_cancel(self) -> None:
        self.dismiss(False)


class RevokeRoleModal(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, username: str):
        super().__init__()
        self.username = username

    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label(f"Revoke role from: {self.username}")
            yield Select(ROLE_OPTIONS, prompt="Select role", id="revoke-role")
            yield Input(placeholder="Database", id="revoke-db")
            with Horizontal(id="modal-buttons"):
                yield Button("Revoke", variant="error", id="revoke-confirm")
                yield Button("Cancel", id="revoke-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "revoke-confirm":
            role_select = self.query_one("#revoke-role", Select)
            role = role_select.value if role_select.value != Select.BLANK else None
            if not role:
                self.notify("Select a role", severity="warning")
                return
            db = self.query_one("#revoke-db", Input).value or "admin"
            try:
                self.app.mongo.revoke_roles(self.username, [{"role": role, "db": db}])
                self.dismiss(True)
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")
        else:
            self.dismiss(False)


    def action_cancel(self) -> None:
        self.dismiss(False)


class ConfirmDeleteModal(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, username: str):
        super().__init__()
        self.username = username

    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label(f"⚠ Delete user '{self.username}'? This cannot be undone.")
            with Horizontal(id="modal-buttons"):
                yield Button("Delete", variant="error", id="del-confirm")
                yield Button("Cancel", id="del-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "del-confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_cancel(self) -> None:
        self.dismiss(False)


class CreateDBModal(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label("Create Database")
            yield Input(placeholder="Database name", id="new-db-name")
            yield Input(placeholder="Initial collection name", id="new-col-name")
            with Horizontal(id="modal-buttons"):
                yield Button("Create", variant="primary", id="cdb-confirm")
                yield Button("Cancel", id="cdb-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cdb-confirm":
            db_name = self.query_one("#new-db-name", Input).value
            col_name = self.query_one("#new-col-name", Input).value or "default"
            if not db_name:
                self.notify("Database name required", severity="warning")
                return
            try:
                self.app.mongo.client[db_name].create_collection(col_name)
                self.dismiss(True)
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")
        else:
            self.dismiss(False)

    def action_cancel(self) -> None:
        self.dismiss(False)


class ConfirmDropDBModal(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, db_name: str):
        super().__init__()
        self.db_name = db_name

    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label(f"Drop database '{self.db_name}'? This cannot be undone.")
            with Horizontal(id="modal-buttons"):
                yield Button("Drop", variant="error", id="dropdb-confirm")
                yield Button("Cancel", id="dropdb-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "dropdb-confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_cancel(self) -> None:
        self.dismiss(False)


class CreateSearchIndexModal(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, db_name: str, col_name: str):
        super().__init__()
        self.db_name = db_name
        self.col_name = col_name

    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label(f"Create Search Index on {self.db_name}.{self.col_name}")
            yield Input(placeholder="Index name", id="sidx-name")
            yield Select(
                [("Search (text)", "search"), ("Vector Search", "vectorSearch")],
                prompt="Index type",
                id="sidx-index-type",
            )
            yield Select(
                [("Dynamic (all fields)", "dynamic"), ("Static (specify fields)", "static")],
                prompt="Mapping type (for text search)",
                id="sidx-type",
            )
            yield Input(placeholder="Fields (comma-sep: name,email)", id="sidx-fields")
            yield Input(placeholder="Analyzer (default: lucene.standard)", id="sidx-analyzer")
            yield Static("-- Vector fields (for vector search) --", id="sidx-vector-label")
            yield Input(placeholder="Vector field name (e.g. embedding)", id="sidx-vec-field")
            yield Input(placeholder="Dimensions (e.g. 1536)", id="sidx-vec-dims")
            yield Select(
                [("cosine", "cosine"), ("euclidean", "euclidean"), ("dotProduct", "dotProduct")],
                prompt="Similarity",
                id="sidx-vec-similarity",
            )
            yield Input(placeholder="Filter fields (comma-sep, optional)", id="sidx-vec-filters")
            with Horizontal(id="modal-buttons"):
                yield Button("Create", variant="primary", id="sidx-confirm")
                yield Button("Cancel", id="sidx-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "sidx-confirm":
            name = self.query_one("#sidx-name", Input).value
            if not name:
                self.notify("Index name required", severity="warning")
                return

            index_type_select = self.query_one("#sidx-index-type", Select)
            index_type = index_type_select.value if index_type_select.value != Select.BLANK else "search"

            if index_type == "vectorSearch":
                vec_field = self.query_one("#sidx-vec-field", Input).value
                dims_str = self.query_one("#sidx-vec-dims", Input).value
                sim_select = self.query_one("#sidx-vec-similarity", Select)
                similarity = sim_select.value if sim_select.value != Select.BLANK else "cosine"

                if not vec_field or not dims_str:
                    self.notify("Vector field and dimensions required", severity="warning")
                    return
                try:
                    dims = int(dims_str)
                except ValueError:
                    self.notify("Dimensions must be a number", severity="warning")
                    return

                fields = [{
                    "type": "vector",
                    "path": vec_field,
                    "numDimensions": dims,
                    "similarity": similarity,
                }]

                # Add filter fields
                filters_str = self.query_one("#sidx-vec-filters", Input).value
                if filters_str:
                    for f in filters_str.split(","):
                        f = f.strip()
                        if f:
                            fields.append({"type": "filter", "path": f})

                definition = {"fields": fields}
                try:
                    self.app.mongo.client[self.db_name][self.col_name].create_search_index(
                        {"name": name, "type": "vectorSearch", "definition": definition}
                    )
                    self.dismiss(True)
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")
            else:
                type_select = self.query_one("#sidx-type", Select)
                mapping_type = type_select.value if type_select.value != Select.BLANK else "dynamic"
                analyzer = self.query_one("#sidx-analyzer", Input).value or "lucene.standard"

                if mapping_type == "dynamic":
                    definition = {"mappings": {"dynamic": True}}
                else:
                    fields_str = self.query_one("#sidx-fields", Input).value
                    if not fields_str:
                        self.notify("Fields required for static mapping", severity="warning")
                        return
                    fields = {}
                    for f in fields_str.split(","):
                        f = f.strip()
                        if f:
                            fields[f] = {"type": "string", "analyzer": analyzer}
                    definition = {"mappings": {"dynamic": False, "fields": fields}}

                try:
                    self.app.mongo.create_search_index(self.db_name, self.col_name, name, definition)
                    self.dismiss(True)
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")
        else:
            self.dismiss(False)

    def action_cancel(self) -> None:
        self.dismiss(False)


class CreateIndexModal(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, db_name: str, col_name: str):
        super().__init__()
        self.db_name = db_name
        self.col_name = col_name

    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label(f"Create Index on {self.db_name}.{self.col_name}")
            yield Input(placeholder="Fields (e.g. name:1,age:-1)", id="idx-fields")
            yield Select(
                [("No", "no"), ("Yes", "yes")],
                prompt="Unique?",
                id="idx-unique",
            )
            with Horizontal(id="modal-buttons"):
                yield Button("Create", variant="primary", id="idx-confirm")
                yield Button("Cancel", id="idx-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "idx-confirm":
            fields_str = self.query_one("#idx-fields", Input).value
            if not fields_str:
                self.notify("Fields required (e.g. name:1)", severity="warning")
                return
            try:
                keys = []
                for part in fields_str.split(","):
                    field, direction = part.strip().rsplit(":", 1)
                    keys.append((field.strip(), int(direction.strip())))
            except (ValueError, IndexError):
                self.notify("Format: field:1,field:-1", severity="warning")
                return
            unique_select = self.query_one("#idx-unique", Select)
            unique = unique_select.value == "yes" if unique_select.value != Select.BLANK else False
            try:
                self.app.mongo.create_index(self.db_name, self.col_name, keys, unique=unique)
                self.dismiss(True)
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")
        else:
            self.dismiss(False)

    def action_cancel(self) -> None:
        self.dismiss(False)


# ─── App ─────────────────────────────────────────────────────────────────────

class MongoTUI(App):
    CSS = """
    /* Connect Screen */
    #connect-form {
        width: 70;
        padding: 2 4;
        margin-top: 3;
        border: round $primary;
    }
    #connect-logo {
        text-align: center;
        text-style: bold;
        color: $success;
        margin-bottom: 1;
    }

    /* Dashboard Layout */
    #dashboard {
        height: 1fr;
        overflow: hidden;
    }
    #sidebar {
        width: 30;
        dock: left;
        border-right: solid $primary;
        padding: 1;
        overflow: hidden;
    }
    #sidebar-title {
        text-style: bold;
        margin-bottom: 1;
        color: $success;
    }
    #nav-tree {
        height: 1fr;
        overflow-x: hidden;
        overflow-y: auto;
        max-width: 28;
        scrollbar-size: 0 0;
    }
    #content {
        width: 1fr;
        height: 1fr;
        overflow: hidden;
        padding: 0 1;
    }

    /* Tabs */
    #tabs {
        height: 1fr;
    }

    /* Users toolbar */
    #users-toolbar, #idx-toolbar, #db-toolbar, #doc-toolbar {
        height: 3;
        min-height: 3;
        max-height: 3;
        overflow: hidden;
    }
    #users-toolbar Button, #idx-toolbar Button, #db-toolbar Button, #doc-toolbar Button {
        margin: 0 1;
        min-width: 8;
        max-width: 12;
    }
    #doc-filter, #agg-input {
        width: 1fr;
    }
    #doc-detail {
        overflow-y: auto;
        height: 1fr;
        padding: 1;
    }

    /* Performance */
    #perf-charts {
        height: 1fr;
    }
    PlotextPlot {
        height: 1fr;
    }

    /* Modals */
    #modal {
        width: 55;
        padding: 2 3;
        background: $surface;
        border: thick $primary;
        margin: 2 0;
    }
    #modal-buttons {
        margin-top: 1;
    }
    #modal-buttons Button {
        margin-right: 1;
    }
    """

    TITLE = "MongoTUI"
    BINDINGS = [Binding("ctrl+c", "quit", "Quit", priority=True)]

    def __init__(self, uri: str | None = None):
        super().__init__()
        self.mongo: MongoAdmin | None = None
        self._uri = uri

    def on_mount(self) -> None:
        if self._uri:
            try:
                self.mongo = MongoAdmin(self._uri)
                if self.mongo.ping():
                    self.push_screen(DashboardScreen())
                else:
                    self.notify("Authentication failed", severity="error")
                    self.push_screen(ConnectScreen())
            except Exception as e:
                self.notify(f"Connection error: {e}", severity="error")
                self.push_screen(ConnectScreen())
        else:
            self.push_screen(ConnectScreen())
