from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.containers import Vertical, Horizontal, Center
from textual.widgets import (
    Header, Footer, Static, Input, Button, DataTable, Label, Select,
)
from textual.binding import Binding
from textual_plotext import PlotextPlot

from mongotui.mongo import MongoAdmin

MAX_HISTORY = 60


class ConnectScreen(Screen):
    BINDINGS = [Binding("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Center():
            with Vertical(id="connect-form"):
                yield Label("MongoDB Connection URI")
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
                status.update("Hint: add ?authSource=admin to your URI")
                return
            try:
                admin = MongoAdmin(uri)
                if admin.ping():
                    self.app.mongo = admin
                    self.app.push_screen(MainScreen())
                else:
                    status.update("Authentication failed. Check credentials and authSource.")
            except Exception as e:
                status.update(f"Error: {e}")


class MainScreen(Screen):
    BINDINGS = [
        Binding("1", "show_stats", "Server Stats"),
        Binding("2", "show_databases", "Databases"),
        Binding("3", "show_users", "Users"),
        Binding("4", "show_roles", "Roles"),
        Binding("5", "show_replicaset", "Replica Set"),
        Binding("6", "show_monitor", "Live Monitor"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Center():
            with Vertical(id="main-menu"):
                yield Label("MongoTUI — Main Menu", id="menu-title")
                yield Button("[1] Server Stats", id="btn-stats")
                yield Button("[2] Databases", id="btn-databases")
                yield Button("[3] Users", id="btn-users")
                yield Button("[4] Roles", id="btn-roles")
                yield Button("[5] Replica Set", id="btn-replicaset")
                yield Button("[6] Live Monitor", id="btn-monitor")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "btn-stats":
                self.app.push_screen(StatsScreen())
            case "btn-databases":
                self.app.push_screen(DatabasesScreen())
            case "btn-users":
                self.app.push_screen(UsersScreen())
            case "btn-roles":
                self.app.push_screen(RolesScreen())
            case "btn-replicaset":
                self.app.push_screen(ReplicaSetScreen())
            case "btn-monitor":
                self.app.push_screen(MonitorScreen())

    def action_show_stats(self) -> None:
        self.app.push_screen(StatsScreen())

    def action_show_databases(self) -> None:
        self.app.push_screen(DatabasesScreen())

    def action_show_users(self) -> None:
        self.app.push_screen(UsersScreen())

    def action_show_roles(self) -> None:
        self.app.push_screen(RolesScreen())

    def action_show_replicaset(self) -> None:
        self.app.push_screen(ReplicaSetScreen())

    def action_show_monitor(self) -> None:
        self.app.push_screen(MonitorScreen())


class ReplicaSetScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="rs-info")
        yield DataTable(id="rs-table")
        yield Footer()

    def on_mount(self) -> None:
        self._load_status()

    def _load_status(self) -> None:
        info = self.query_one("#rs-info", Static)
        table = self.query_one("#rs-table", DataTable)
        table.clear(columns=True)

        status = self.app.mongo.replica_set_status()
        if not status:
            info.update("Not a replica set or insufficient permissions.")
            return

        rs_name = status.get("set", "N/A")
        my_state = status.get("myState", "N/A")
        states = {0: "STARTUP", 1: "PRIMARY", 2: "SECONDARY", 3: "RECOVERING",
                  5: "STARTUP2", 6: "UNKNOWN", 7: "ARBITER", 8: "DOWN", 9: "ROLLBACK", 10: "REMOVED"}
        info.update(f"Replica Set: {rs_name} | My State: {states.get(my_state, my_state)}")

        table.add_columns("Name", "State", "Health", "Uptime (s)", "Optime", "Lag (s)")
        table.cursor_type = "row"

        members = status.get("members", [])
        primary_optime = None
        for m in members:
            if m.get("stateStr") == "PRIMARY":
                optime = m.get("optime", {})
                primary_optime = optime.get("ts") if isinstance(optime, dict) else optime
                break

        for m in members:
            name = m.get("name", "")
            state_str = m.get("stateStr", "UNKNOWN")
            health = "✅" if m.get("health") == 1 else "❌"
            uptime = str(m.get("uptime", "N/A"))
            optime = m.get("optime", {})
            optime_ts = optime.get("ts") if isinstance(optime, dict) else optime
            optime_display = str(optime_ts.time) if optime_ts else "N/A"

            lag = ""
            if primary_optime and optime_ts and state_str != "PRIMARY":
                lag = str(primary_optime.time - optime_ts.time)
            elif state_str == "PRIMARY":
                lag = "0"

            table.add_row(name, state_str, health, uptime, optime_display, lag, key=name)

    def action_refresh(self) -> None:
        self._load_status()
        self.notify("Refreshed")

    def action_back(self) -> None:
        self.app.pop_screen()


class StatsScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="stats-table")
        yield Footer()

    def on_mount(self) -> None:
        self._load_stats()

    def _load_stats(self) -> None:
        table = self.query_one("#stats-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Metric", "Value")
        try:
            status = self.app.mongo.server_status()
            table.add_row("Host", status.get("host", "N/A"))
            table.add_row("Version", status.get("version", "N/A"))
            table.add_row("Uptime (s)", str(status.get("uptime", "N/A")))
            table.add_row("Current Connections", str(status.get("connections", {}).get("current", "N/A")))
            table.add_row("Available Connections", str(status.get("connections", {}).get("available", "N/A")))
            mem = status.get("mem", {})
            table.add_row("Resident Memory (MB)", str(mem.get("resident", "N/A")))
            table.add_row("Virtual Memory (MB)", str(mem.get("virtual", "N/A")))
            opcounters = status.get("opcounters", {})
            table.add_row("Inserts", str(opcounters.get("insert", 0)))
            table.add_row("Queries", str(opcounters.get("query", 0)))
            table.add_row("Updates", str(opcounters.get("update", 0)))
            table.add_row("Deletes", str(opcounters.get("delete", 0)))
            table.add_row("Storage Engine", status.get("storageEngine", {}).get("name", "N/A"))
        except Exception as e:
            table.add_row("Error", str(e))

    def action_refresh(self) -> None:
        self._load_stats()
        self.notify("Refreshed")

    def action_back(self) -> None:
        self.app.pop_screen()


class DatabasesScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("d", "drop_db", "Drop Database"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="db-table")
        yield Footer()

    def on_mount(self) -> None:
        self._load_databases()

    def _load_databases(self) -> None:
        table = self.query_one("#db-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Database", "Collections", "Size (MB)")
        table.cursor_type = "row"
        try:
            for db_name in self.app.mongo.list_databases():
                stats = self.app.mongo.db_stats(db_name)
                collections = len(self.app.mongo.list_collections(db_name))
                size_mb = f"{stats.get('dataSize', 0) / (1024 * 1024):.2f}"
                table.add_row(db_name, str(collections), size_mb, key=db_name)
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def _selected_db(self) -> str | None:
        table = self.query_one("#db-table", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        return str(row_key.value)

    def action_drop_db(self) -> None:
        db_name = self._selected_db()
        if not db_name:
            return

        def on_confirm(result: bool) -> None:
            if result:
                try:
                    self.app.mongo.drop_database(db_name)
                    self._load_databases()
                    self.notify(f"Dropped {db_name}")
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")

        self.app.push_screen(ConfirmDropDBModal(db_name), callback=on_confirm)

    def action_refresh(self) -> None:
        self._load_databases()
        self.notify("Refreshed")

    def action_back(self) -> None:
        self.app.pop_screen()


class ConfirmDropDBModal(ModalScreen[bool]):
    def __init__(self, db_name: str):
        super().__init__()
        self.db_name = db_name

    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label(f"Drop database '{self.db_name}'? This cannot be undone.")
            with Horizontal():
                yield Button("Drop", variant="error", id="drop-confirm")
                yield Button("Cancel", id="drop-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "drop-confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)


MONGO_ROLES = [
    "read", "readWrite", "dbAdmin", "dbOwner", "userAdmin",
    "clusterAdmin", "clusterManager", "clusterMonitor", "hostManager",
    "readAnyDatabase", "readWriteAnyDatabase", "dbAdminAnyDatabase",
    "userAdminAnyDatabase", "backup", "restore", "root",
]

ROLE_OPTIONS = [(role, role) for role in MONGO_ROLES]

MONGO_ACTIONS = [
    "find", "insert", "remove", "update", "createCollection",
    "dropCollection", "createIndex", "dropIndex", "collStats",
    "dbStats", "listCollections", "listDatabases",
]


class RolesScreen(Screen):
    BINDINGS = [
        Binding("c", "create_role", "Create Role"),
        Binding("d", "drop_role", "Drop Role"),
        Binding("f", "toggle_filter", "Toggle Filter"),
        Binding("r", "refresh", "Refresh"),
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self._filter = "all"  # "all", "custom", "builtin"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Filter: All roles [f to toggle]", id="roles-filter-label")
        yield DataTable(id="roles-table")
        yield Footer()

    def on_mount(self) -> None:
        self._load_roles()

    def _load_roles(self) -> None:
        table = self.query_one("#roles-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Role", "Database", "Type", "Privileges", "Inherited Roles")
        table.cursor_type = "row"
        try:
            roles = self.app.mongo.list_roles()
            for role in roles:
                is_builtin = role.get("isBuiltin", False)
                role_type = "built-in" if is_builtin else "custom"
                if self._filter == "custom" and is_builtin:
                    continue
                if self._filter == "builtin" and not is_builtin:
                    continue
                privs = ", ".join(
                    f"{','.join(p.get('actions', []))}@{p.get('resource', {}).get('db', '*')}"
                    for p in role.get("privileges", [])
                )
                inherited = ", ".join(
                    f"{r['role']}@{r['db']}" for r in role.get("roles", [])
                )
                table.add_row(role["role"], role.get("db", ""), role_type, privs, inherited, key=role["role"])
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def action_toggle_filter(self) -> None:
        cycle = {"all": "custom", "custom": "builtin", "builtin": "all"}
        self._filter = cycle[self._filter]
        labels = {"all": "All roles", "custom": "Custom only", "builtin": "Built-in only"}
        self.query_one("#roles-filter-label", Static).update(f"Filter: {labels[self._filter]} [f to toggle]")
        self._load_roles()

    def _selected_role(self) -> str | None:
        table = self.query_one("#roles-table", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        return str(row_key.value)

    def action_create_role(self) -> None:
        def on_dismiss(result: bool) -> None:
            if result:
                self._load_roles()
                self.notify("Role created")
        self.app.push_screen(CreateRoleModal(), callback=on_dismiss)

    def action_drop_role(self) -> None:
        role_name = self._selected_role()
        if not role_name:
            return

        def on_confirm(result: bool) -> None:
            if result:
                try:
                    self.app.mongo.drop_role(role_name)
                    self._load_roles()
                    self.notify(f"Dropped role {role_name}")
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")

        self.app.push_screen(ConfirmDropRoleModal(role_name), callback=on_confirm)

    def action_refresh(self) -> None:
        self._load_roles()
        self.notify("Refreshed")

    def action_back(self) -> None:
        self.app.pop_screen()


class CreateRoleModal(ModalScreen[bool]):
    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label("Create Custom Role")
            yield Input(placeholder="Role name", id="role-name")
            yield Input(placeholder="Actions (comma-sep: find,insert,update)", id="role-actions")
            yield Input(placeholder="Resource database (e.g. mydb or empty for all)", id="role-res-db")
            yield Input(placeholder="Resource collection (empty for all)", id="role-res-col")
            yield Select(ROLE_OPTIONS, prompt="Inherit from role (optional)", id="role-inherit")
            with Horizontal():
                yield Button("Create", variant="primary", id="crole-confirm")
                yield Button("Cancel", id="crole-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "crole-confirm":
            name = self.query_one("#role-name", Input).value
            if not name:
                self.notify("Role name required", severity="warning")
                return
            actions_str = self.query_one("#role-actions", Input).value
            actions = [a.strip() for a in actions_str.split(",") if a.strip()] if actions_str else []
            res_db = self.query_one("#role-res-db", Input).value or ""
            res_col = self.query_one("#role-res-col", Input).value or ""
            privileges = []
            if actions:
                privileges.append({
                    "resource": {"db": res_db, "collection": res_col},
                    "actions": actions,
                })
            inherit_select = self.query_one("#role-inherit", Select)
            roles = []
            if inherit_select.value != Select.BLANK:
                roles.append({"role": inherit_select.value, "db": "admin"})
            try:
                self.app.mongo.create_role(name, privileges, roles)
                self.dismiss(True)
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")
        else:
            self.dismiss(False)


class ConfirmDropRoleModal(ModalScreen[bool]):
    def __init__(self, role_name: str):
        super().__init__()
        self.role_name = role_name

    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label(f"Drop role '{self.role_name}'? This cannot be undone.")
            with Horizontal():
                yield Button("Drop", variant="error", id="droprole-confirm")
                yield Button("Cancel", id="droprole-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "droprole-confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)


class CreateUserModal(ModalScreen[bool]):
    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label("Create New User")
            yield Input(placeholder="Username", id="new-username")
            yield Input(placeholder="Password", password=True, id="new-password")
            yield Select(ROLE_OPTIONS, prompt="Select role", id="new-role")
            yield Input(placeholder="Database (e.g. admin)", id="new-db")
            with Horizontal():
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


class ResetPasswordModal(ModalScreen[bool]):
    def __init__(self, username: str):
        super().__init__()
        self.username = username

    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label(f"Reset password for: {self.username}")
            yield Input(placeholder="New password", password=True, id="reset-pw")
            with Horizontal():
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


class GrantRoleModal(ModalScreen[bool]):
    def __init__(self, username: str):
        super().__init__()
        self.username = username

    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label(f"Grant role to: {self.username}")
            yield Select(ROLE_OPTIONS, prompt="Select role", id="grant-role")
            yield Input(placeholder="Database (e.g. admin)", id="grant-db")
            with Horizontal():
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


class RevokeRoleModal(ModalScreen[bool]):
    def __init__(self, username: str):
        super().__init__()
        self.username = username

    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label(f"Revoke role from: {self.username}")
            yield Select(ROLE_OPTIONS, prompt="Select role", id="revoke-role")
            yield Input(placeholder="Database", id="revoke-db")
            with Horizontal():
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


class ConfirmDeleteModal(ModalScreen[bool]):
    def __init__(self, username: str):
        super().__init__()
        self.username = username

    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label(f"Delete user '{self.username}'? This cannot be undone.")
            with Horizontal():
                yield Button("Delete", variant="error", id="del-confirm")
                yield Button("Cancel", id="del-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "del-confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)


class UsersScreen(Screen):
    BINDINGS = [
        Binding("c", "create_user", "Create User"),
        Binding("d", "delete_user", "Delete User"),
        Binding("p", "reset_password", "Reset Password"),
        Binding("g", "grant_role", "Grant Role"),
        Binding("v", "revoke_role", "Revoke Role"),
        Binding("r", "refresh", "Refresh"),
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="users-table")
        yield Footer()

    def on_mount(self) -> None:
        try:
            self._load_users()
        except Exception as e:
            self.notify(f"Error loading users: {e}", severity="error")

    def _load_users(self) -> None:
        table = self.query_one("#users-table", DataTable)
        table.clear(columns=True)
        table.add_columns("User", "Database", "Roles")
        table.cursor_type = "row"
        for user in self.app.mongo.list_users():
            roles = ", ".join(f"{r['role']}@{r['db']}" for r in user.get("roles", []))
            table.add_row(user["user"], user.get("db", ""), roles, key=user["user"])

    def _selected_user(self) -> str | None:
        table = self.query_one("#users-table", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        return str(row_key.value)

    def action_create_user(self) -> None:
        def on_dismiss(result: bool) -> None:
            if result:
                self._load_users()
                self.notify("User created")
        self.app.push_screen(CreateUserModal(), callback=on_dismiss)

    def action_delete_user(self) -> None:
        username = self._selected_user()
        if not username:
            return

        def on_confirm(result: bool) -> None:
            if result:
                try:
                    self.app.mongo.delete_user(username)
                    self._load_users()
                    self.notify(f"Deleted {username}")
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")

        self.app.push_screen(ConfirmDeleteModal(username), callback=on_confirm)

    def action_reset_password(self) -> None:
        username = self._selected_user()
        if not username:
            return

        def on_dismiss(result: bool) -> None:
            if result:
                self.notify(f"Password reset for {username}")

        self.app.push_screen(ResetPasswordModal(username), callback=on_dismiss)

    def action_grant_role(self) -> None:
        username = self._selected_user()
        if not username:
            return

        def on_dismiss(result: bool) -> None:
            if result:
                self._load_users()
                self.notify("Role granted")

        self.app.push_screen(GrantRoleModal(username), callback=on_dismiss)

    def action_revoke_role(self) -> None:
        username = self._selected_user()
        if not username:
            return

        def on_dismiss(result: bool) -> None:
            if result:
                self._load_users()
                self.notify("Role revoked")

        self.app.push_screen(RevokeRoleModal(username), callback=on_dismiss)

    def action_refresh(self) -> None:
        self._load_users()
        self.notify("Refreshed")

    def action_back(self) -> None:
        self.app.pop_screen()


class MonitorScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self._connections: list[int] = []
        self._ops: list[int] = []
        self._memory: list[int] = []
        self._prev_ops = 0

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield PlotextPlot(id="plot-connections")
            yield PlotextPlot(id="plot-ops")
            yield PlotextPlot(id="plot-memory")
        yield Footer()

    def on_mount(self) -> None:
        self._sample()
        self.set_interval(2, self._sample)

    def _sample(self) -> None:
        try:
            status = self.app.mongo.server_status()
        except Exception:
            return

        conns = status.get("connections", {}).get("current", 0)
        self._connections.append(conns)
        if len(self._connections) > MAX_HISTORY:
            self._connections = self._connections[-MAX_HISTORY:]

        opcounters = status.get("opcounters", {})
        total_ops = sum(opcounters.get(k, 0) for k in ("insert", "query", "update", "delete"))
        ops_diff = total_ops - self._prev_ops if self._prev_ops else 0
        self._prev_ops = total_ops
        self._ops.append(max(ops_diff, 0))
        if len(self._ops) > MAX_HISTORY:
            self._ops = self._ops[-MAX_HISTORY:]

        mem = status.get("mem", {}).get("resident", 0)
        self._memory.append(mem)
        if len(self._memory) > MAX_HISTORY:
            self._memory = self._memory[-MAX_HISTORY:]

        self._render_plots()

    def _render_plots(self) -> None:
        # Connections
        plot_conn = self.query_one("#plot-connections", PlotextPlot)
        plt = plot_conn.plt
        plt.clear_data()
        plt.clear_figure()
        plt.title("Connections")
        plt.xlabel("Time (2s intervals)")
        plt.plot(self._connections, marker="braille")
        plot_conn.refresh()

        # Operations/sec
        plot_ops = self.query_one("#plot-ops", PlotextPlot)
        plt = plot_ops.plt
        plt.clear_data()
        plt.clear_figure()
        plt.title("Operations / 2s")
        plt.xlabel("Time (2s intervals)")
        plt.plot(self._ops, marker="braille")
        plot_ops.refresh()

        # Memory
        plot_mem = self.query_one("#plot-memory", PlotextPlot)
        plt = plot_mem.plt
        plt.clear_data()
        plt.clear_figure()
        plt.title("Resident Memory (MB)")
        plt.xlabel("Time (2s intervals)")
        plt.plot(self._memory, marker="braille")
        plot_mem.refresh()

    def action_back(self) -> None:
        self.app.pop_screen()


class MongoTUI(App):
    CSS = """
    #connect-form { width: 60; padding: 2; margin-top: 4; }
    #main-menu { width: 40; padding: 2; margin-top: 4; }
    #menu-title { text-align: center; text-style: bold; margin-bottom: 1; }
    #modal { width: 50; padding: 2; background: $surface; border: thick $primary; }
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
                    self.push_screen(MainScreen())
                else:
                    self.notify("Authentication failed", severity="error")
                    self.push_screen(ConnectScreen())
            except Exception as e:
                self.notify(f"Connection error: {e}", severity="error")
                self.push_screen(ConnectScreen())
        else:
            self.push_screen(ConnectScreen())
