"""Global admin tools — server info, audit log, dashboards, filters."""

import json
from jira_client import JiraCloudClient

def _fmt(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def register_admin_tools(mcp, client: JiraCloudClient):

    @mcp.tool()
    async def get_server_info() -> str:
        """Get Jira Cloud instance info — version, URL, deployment type."""
        data = await client.get("/serverInfo")
        return _fmt(data)

    @mcp.tool()
    async def get_audit_log(limit: int = 50, offset: int = 0, from_date: str = "", to_date: str = "", search: str = "") -> str:
        """Get audit log records. Shows admin actions, permission changes, scheme modifications.
        Dates in ISO format (e.g. '2026-03-01')."""
        params = {"maxResults": limit, "startAt": offset}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        if search:
            params["filter"] = search
        data = await client.get("/auditing/record", **params)
        return _fmt(data)

    @mcp.tool()
    async def list_shared_filters(search: str = "") -> str:
        """List shared/saved filters."""
        params = {"maxResults": 100}
        if search:
            params["filterName"] = search
        data = await client.get("/filter/search", **params)
        return _fmt(data.get("values", []))

    @mcp.tool()
    async def get_filter(filter_id: str) -> str:
        """Get filter details — JQL, owner, permissions."""
        data = await client.get(f"/filter/{filter_id}")
        return _fmt(data)

    @mcp.tool()
    async def list_dashboards(search: str = "") -> str:
        """List dashboards."""
        params = {"maxResults": 100}
        if search:
            params["filter"] = search
        data = await client.get("/dashboard/search", **params)
        return _fmt(data.get("values", []))

    @mcp.tool()
    async def get_dashboard(dashboard_id: str) -> str:
        """Get dashboard details."""
        data = await client.get(f"/dashboard/{dashboard_id}")
        return _fmt(data)

    @mcp.tool()
    async def list_project_categories() -> str:
        """List all project categories."""
        data = await client.get("/projectCategory")
        return _fmt(data)

    @mcp.tool()
    async def list_event_types() -> str:
        """List all event types (Issue Created, Updated, etc.)."""
        data = await client.get("/events", api="v2")
        return _fmt(data)

    @mcp.tool()
    async def get_global_permissions() -> str:
        """Get all global permission holders."""
        data = await client.get("/permissions")
        return _fmt(data)

    @mcp.tool()
    async def get_application_properties(search: str = "") -> str:
        """Get Jira application properties (global settings)."""
        params = {}
        if search:
            params["key"] = search
        data = await client.get("/application-properties", **params)
        return _fmt(data)
