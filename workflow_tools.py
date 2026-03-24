"""Workflow tools for Jira Cloud."""

import json
from jira_client import JiraCloudClient

def _fmt(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def register_workflow_tools(mcp, client: JiraCloudClient):

    @mcp.tool()
    async def list_workflows(search: str = "") -> str:
        """List all workflows."""
        data = await client.get("/workflow/search", api="v3")
        workflows = data.get("values", [])
        if search:
            s = search.lower()
            workflows = [w for w in workflows if s in (w.get("id", {}).get("name", "") or "").lower()]
        return _fmt(workflows)

    @mcp.tool()
    async def get_workflow(workflow_name: str) -> str:
        """Get workflow details — statuses, transitions."""
        data = await client.get("/workflow/search", workflowName=workflow_name, expand="transitions.rules,statuses")
        workflows = data.get("values", [])
        return _fmt(workflows[0] if workflows else {"error": f"Workflow '{workflow_name}' not found"})

    @mcp.tool()
    async def list_statuses(search: str = "") -> str:
        """List all statuses with categories."""
        data = await client.get("/statuses/search", api="v3")
        statuses = data.get("values", [])
        if search:
            s = search.lower()
            statuses = [st for st in statuses if s in (st.get("name", "") or "").lower()]
        return _fmt(statuses)

    @mcp.tool()
    async def list_workflow_schemes(search: str = "") -> str:
        """List all workflow schemes."""
        data = await client.get("/workflowscheme", api="v3")
        schemes = data.get("values", data) if isinstance(data, dict) else data
        if search and isinstance(schemes, list):
            s = search.lower()
            schemes = [sc for sc in schemes if s in (sc.get("name", "") or "").lower()]
        return _fmt(schemes)

    @mcp.tool()
    async def get_workflow_scheme(scheme_id: str) -> str:
        """Get workflow scheme — default workflow and issue type mappings."""
        data = await client.get(f"/workflowscheme/{scheme_id}")
        return _fmt(data)

    @mcp.tool()
    async def list_priorities() -> str:
        """List all priorities."""
        data = await client.get("/priority")
        return _fmt(data)

    @mcp.tool()
    async def list_resolutions() -> str:
        """List all resolutions."""
        data = await client.get("/resolution")
        return _fmt(data)

    @mcp.tool()
    async def list_issue_types() -> str:
        """List all issue types."""
        data = await client.get("/issuetype")
        return _fmt(data)

    @mcp.tool()
    async def list_issue_link_types() -> str:
        """List all issue link types."""
        data = await client.get("/issueLinkType")
        return _fmt(data)
