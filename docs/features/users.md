# User Administration

## Viewing users

Click **Users** in the sidebar or navigate to the Users tab. Shows all users with their database and assigned roles.

## Creating a user

Click **Create** and fill in:

- Username
- Password
- Role (dropdown with all built-in MongoDB roles)
- Database (defaults to `admin`)

## Resetting passwords

Select a user, click **Password**, enter the new password.

## Granting roles

Select a user, click **Grant**, pick a role from the dropdown, specify the database.

## Revoking roles

Select a user, click **Revoke**, pick the role to remove.

## Deleting a user

Select a user, click **Delete**, confirm.

## Built-in roles

MongoTUI includes all standard MongoDB roles in the dropdown:

| Category | Roles |
|----------|-------|
| Database | `read`, `readWrite`, `dbAdmin`, `dbOwner`, `userAdmin` |
| Cluster | `clusterAdmin`, `clusterManager`, `clusterMonitor`, `hostManager` |
| All-DB | `readAnyDatabase`, `readWriteAnyDatabase`, `dbAdminAnyDatabase`, `userAdminAnyDatabase` |
| Backup | `backup`, `restore` |
| Super | `root` |
