"""Permission, notification, security, field config scheme tools for Jira Cloud."""

import json
from jira_client import JiraCloudClient

def _fmt(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def register_scheme_tools(mcp, client: JiraCloudClient):

    # --- Permission Schemes ---

    @mcp.tool()
    async def list_permission_schemes() -> str:
        """List all permission schemes."""
        data = await client.get("/permissionscheme")
        return _fmt(data.get("permissionSchemes", data))

    @mcp.tool()
    async def get_permission_scheme(scheme_id: str) -> str:
        """Get permission scheme with all grants."""
        data = await client.get(f"/permissionscheme/{scheme_id}", expand="permissions")
        return _fmt(data)

    @mcp.tool()
    async def create_permission_scheme(name: str, description: str = "") -> str:
        """Create a new permission scheme."""
        body = {"name": name, "description": description}
        data = await client.post("/permissionscheme", body)
        return _fmt(data)

    @mcp.tool()
    async def add_permission_grant(scheme_id: str, permission: str, holder_type: str, holder_parameter: str = "") -> str:
        """Add a permission grant.
        permission: e.g. 'BROWSE_PROJECTS', 'CREATE_ISSUES', 'ADMINISTER_PROJECTS'
        holder_type: 'group', 'projectRole', 'user', 'reporter', 'assignee'
        holder_parameter: group name, role id, or account id"""
        holder = {"type": holder_type}
        if holder_parameter:
            holder["parameter"] = holder_parameter
        body = {"holder": holder, "permission": permission}
        data = await client.post(f"/permissionscheme/{scheme_id}/permission", body)
        return _fmt(data)

    # --- Notification Schemes ---

    @mcp.tool()
    async def list_notification_schemes() -> str:
        """List all notification schemes."""
        data = await client.get("/notificationscheme")
        return _fmt(data.get("values", data))

    @mcp.tool()
    async def get_notification_scheme(scheme_id: str) -> str:
        """Get notification scheme with all event mappings."""
        data = await client.get(f"/notificationscheme/{scheme_id}", expand="all")
        return _fmt(data)

    # --- Issue Security Schemes ---

    @mcp.tool()
    async def list_issue_security_schemes() -> str:
        """List all issue security schemes."""
        data = await client.get("/issuesecurityschemes")
        return _fmt(data.get("issueSecuritySchemes", data))

    @mcp.tool()
    async def get_issue_security_scheme(scheme_id: str) -> str:
        """Get security scheme with levels and members."""
        data = await client.get(f"/issuesecurityschemes/{scheme_id}")
        # Also get levels
        try:
            levels = await client.get(f"/issuesecurityschemes/{scheme_id}/members")
            data["members"] = levels.get("values", [])
        except Exception:
            pass
        return _fmt(data)

    # --- Issue Type Schemes ---

    @mcp.tool()
    async def list_issue_type_schemes(search: str = "") -> str:
        """List all issue type schemes."""
        data = await client.get("/issuetypescheme")
        schemes = data.get("values", [])
        if search:
            s = search.lower()
            schemes = [sc for sc in schemes if s in (sc.get("name", "") or "").lower()]
        return _fmt(schemes)

    @mcp.tool()
    async def get_issue_type_scheme(scheme_id: str) -> str:
        """Get issue type scheme with mapped issue types."""
        data = await client.get(f"/issuetypescheme/mapping?issueTypeSchemeId={scheme_id}")
        return _fmt(data)

    # --- Field Configuration Schemes ---

    @mcp.tool()
    async def list_field_configurations(search: str = "") -> str:
        """List all field configurations."""
        data = await client.get("/fieldconfiguration")
        configs = data.get("values", [])
        if search:
            s = search.lower()
            configs = [c for c in configs if s in (c.get("name", "") or "").lower()]
        return _fmt(configs)

    @mcp.tool()
    async def get_field_configuration(config_id: str) -> str:
        """Get field configuration items (per-field settings)."""
        data = await client.get(f"/fieldconfiguration/{config_id}/fields")
        return _fmt(data)

    @mcp.tool()
    async def list_field_config_schemes(search: str = "") -> str:
        """List field configuration schemes."""
        data = await client.get("/fieldconfigurationscheme")
        schemes = data.get("values", [])
        if search:
            s = search.lower()
            schemes = [sc for sc in schemes if s in (sc.get("name", "") or "").lower()]
        return _fmt(schemes)
