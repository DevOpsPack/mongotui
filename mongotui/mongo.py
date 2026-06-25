from pymongo import MongoClient
from pymongo.errors import OperationFailure


class MongoAdmin:
    def __init__(self, uri: str):
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.db = self.client["admin"]

    def list_users(self) -> list[dict]:
        result = self.db.command("usersInfo")
        return result.get("users", [])

    def create_user(self, username: str, password: str, roles: list[dict]) -> None:
        self.db.command("createUser", username, pwd=password, roles=roles)

    def delete_user(self, username: str) -> None:
        self.db.command("dropUser", username)

    def reset_password(self, username: str, new_password: str) -> None:
        self.db.command("updateUser", username, pwd=new_password)

    def grant_roles(self, username: str, roles: list[dict]) -> None:
        self.db.command("grantRolesToUser", username, roles=roles)

    def revoke_roles(self, username: str, roles: list[dict]) -> None:
        self.db.command("revokeRolesFromUser", username, roles=roles)

    def list_roles(self) -> list[dict]:
        result = self.db.command("rolesInfo", 1, showBuiltinRoles=True)
        return result.get("roles", [])

    def create_role(self, role_name: str, privileges: list[dict], roles: list[dict]) -> None:
        self.db.command("createRole", role_name, privileges=privileges, roles=roles)

    def drop_role(self, role_name: str) -> None:
        self.db.command("dropRole", role_name)

    def list_custom_roles(self) -> list[dict]:
        result = self.db.command("rolesInfo", 1, showBuiltinRoles=False)
        return result.get("roles", [])

    def server_status(self) -> dict:
        return self.db.command("serverStatus")

    def list_databases(self) -> list[dict]:
        return self.client.list_database_names()

    def db_stats(self, db_name: str) -> dict:
        return self.client[db_name].command("dbStats")

    def drop_database(self, db_name: str) -> None:
        self.client.drop_database(db_name)

    def list_collections(self, db_name: str) -> list[str]:
        return self.client[db_name].list_collection_names()

    def drop_collection(self, db_name: str, collection: str) -> None:
        self.client[db_name].drop_collection(collection)

    def replica_set_status(self) -> dict | None:
        try:
            return self.db.command("replSetGetStatus")
        except OperationFailure:
            return None

    def replica_set_config(self) -> dict | None:
        try:
            return self.db.command("replSetGetConfig").get("config", {})
        except OperationFailure:
            return None

    def ping(self) -> bool:
        try:
            self.client.admin.command("ping")
            return True
        except Exception:
            return False
