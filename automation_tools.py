"""Jira Cloud native automation rules tools."""

import json
from jira_client import JiraCloudClient

def _fmt(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def register_automation_tools(mcp, client: JiraCloudClient):

    @mcp.tool()
    async def list_automation_rules(project_key: str = "") -> str:
        """List automation rules. If project_key given, list project rules; otherwise global."""
        if project_key:
            # Project-specific rules
            data = await client.raw_get(f"/rest/cb-automation/latest/project/{project_key}/rule")
        else:
            data = await client.raw_get("/rest/cb-automation/latest/rule")
        return _fmt(data)

    @mcp.tool()
    async def get_automation_rule(rule_id: str, project_key: str = "") -> str:
        """Get automation rule details — trigger, conditions, actions."""
        if project_key:
            data = await client.raw_get(f"/rest/cb-automation/latest/project/{project_key}/rule/{rule_id}")
        else:
            data = await client.raw_get(f"/rest/cb-automation/latest/rule/{rule_id}")
        return _fmt(data)

    @mcp.tool()
    async def enable_automation_rule(rule_id: str, project_key: str = "") -> str:
        """Enable an automation rule."""
        if project_key:
            data = await client.raw_put(f"/rest/cb-automation/latest/project/{project_key}/rule/{rule_id}/enable", {})
        else:
            data = await client.raw_put(f"/rest/cb-automation/latest/rule/{rule_id}/enable", {})
        return _fmt(data or {"status": "enabled", "ruleId": rule_id})

    @mcp.tool()
    async def disable_automation_rule(rule_id: str, project_key: str = "") -> str:
        """Disable an automation rule."""
        if project_key:
            data = await client.raw_put(f"/rest/cb-automation/latest/project/{project_key}/rule/{rule_id}/disable", {})
        else:
            data = await client.raw_put(f"/rest/cb-automation/latest/rule/{rule_id}/disable", {})
        return _fmt(data or {"status": "disabled", "ruleId": rule_id})
