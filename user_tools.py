"""User, group, and role management tools for Jira Cloud."""

import json
from jira_client import JiraCloudClient

def _fmt(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def register_user_tools(mcp, client: JiraCloudClient):

    @mcp.tool()
    async def search_users(query: str, max_results: int = 50) -> str:
        """Search users by name or email."""
        data = await client.get("/user/search", query=query, maxResults=max_results)
        return _fmt(data)

    @mcp.tool()
    async def get_user(account_id: str) -> str:
        """Get user details by account ID."""
        data = await client.get("/user", accountId=account_id)
        return _fmt(data)

    @mcp.tool()
    async def list_groups(search: str = "") -> str:
        """List all groups."""
        params = {"maxResults": 200}
        if search:
            params["query"] = search
        data = await client.get("/group/bulk", **params)
        return _fmt(data.get("values", []))

    @mcp.tool()
    async def get_group_members(group_name: str, max_results: int = 50) -> str:
        """Get group members."""
        data = await client.get("/group/member", groupname=group_name, maxResults=max_results)
        return _fmt(data.get("values", []))

    @mcp.tool()
    async def create_group(group_name: str) -> str:
        """Create a new group."""
        data = await client.post("/group", {"name": group_name})
        return _fmt(data)

    @mcp.tool()
    async def add_user_to_group(group_name: str, account_id: str) -> str:
        """Add user to a group."""
        data = await client.post(f"/group/user?groupname={group_name}", {"accountId": account_id})
        return _fmt(data)

    @mcp.tool()
    async def remove_user_from_group(group_name: str, account_id: str) -> str:
        """Remove user from a group."""
        await client.delete(f"/group/user?groupname={group_name}&accountId={account_id}")
        return _fmt({"status": "removed", "group": group_name, "accountId": account_id})

    @mcp.tool()
    async def get_myself() -> str:
        """Get current authenticated user info."""
        data = await client.get("/myself")
        return _fmt(data)
