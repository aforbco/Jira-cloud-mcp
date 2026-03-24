"""Screen, screen scheme, and ITSS tools for Jira Cloud."""

import json
from jira_client import JiraCloudClient

def _fmt(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def register_screen_tools(mcp, client: JiraCloudClient):

    @mcp.tool()
    async def list_screens(search: str = "") -> str:
        """List all screens."""
        params = {"maxResults": 100}
        if search:
            params["queryString"] = search
        data = await client.get("/screens", **params)
        return _fmt(data.get("values", []))

    @mcp.tool()
    async def get_screen(screen_id: str) -> str:
        """Get screen tabs with their fields."""
        tabs = await client.get(f"/screens/{screen_id}/tabs")
        result = {"id": screen_id, "tabs": []}
        for tab in tabs:
            fields = await client.get(f"/screens/{screen_id}/tabs/{tab['id']}/fields")
            result["tabs"].append({"tab": tab, "fields": fields})
        return _fmt(result)

    @mcp.tool()
    async def create_screen(name: str, description: str = "") -> str:
        """Create a new screen."""
        body = {"name": name}
        if description:
            body["description"] = description
        data = await client.post("/screens", body)
        return _fmt(data)

    @mcp.tool()
    async def add_field_to_screen(screen_id: str, tab_id: str, field_id: str) -> str:
        """Add a field to a screen tab."""
        data = await client.post(f"/screens/{screen_id}/tabs/{tab_id}/fields", {"fieldId": field_id})
        return _fmt(data)

    @mcp.tool()
    async def remove_field_from_screen(screen_id: str, tab_id: str, field_id: str) -> str:
        """Remove a field from a screen tab."""
        await client.delete(f"/screens/{screen_id}/tabs/{tab_id}/fields/{field_id}")
        return _fmt({"status": "removed", "fieldId": field_id})

    @mcp.tool()
    async def list_screen_schemes(search: str = "") -> str:
        """List screen schemes."""
        data = await client.get("/screenscheme", maxResults=100)
        schemes = data.get("values", [])
        if search:
            s = search.lower()
            schemes = [sc for sc in schemes if s in (sc.get("name", "") or "").lower()]
        return _fmt(schemes)

    @mcp.tool()
    async def list_issue_type_screen_schemes(search: str = "") -> str:
        """List issue type screen schemes."""
        data = await client.get("/issuetypescreenscheme", maxResults=100)
        schemes = data.get("values", [])
        if search:
            s = search.lower()
            schemes = [sc for sc in schemes if s in (sc.get("name", "") or "").lower()]
        return _fmt(schemes)
