"""Custom field tools for Jira Cloud."""

import json
from jira_client import JiraCloudClient

def _fmt(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def register_field_tools(mcp, client: JiraCloudClient):

    @mcp.tool()
    async def list_custom_fields(search: str = "") -> str:
        """List all custom fields. Use 'search' to filter by name."""
        data = await client.get("/field")
        fields = [f for f in data if f.get("custom", False)]
        if search:
            s = search.lower()
            fields = [f for f in fields if s in (f.get("name", "") or "").lower()]
        return _fmt(fields)

    @mcp.tool()
    async def get_custom_field(field_id: str) -> str:
        """Get custom field details including contexts."""
        # Field info
        all_fields = await client.get("/field")
        field = next((f for f in all_fields if f.get("id") == field_id), None)
        if not field:
            return _fmt({"error": f"Field {field_id} not found"})
        # Contexts
        field_num = field_id.replace("customfield_", "")
        try:
            contexts = await client.get(f"/field/{field_id}/context")
            field["contexts"] = contexts.get("values", [])
        except Exception:
            field["contexts"] = []
        return _fmt(field)

    @mcp.tool()
    async def get_field_options(field_id: str, context_id: str = "") -> str:
        """Get options for a select/radio/checkbox field."""
        if context_id:
            data = await client.get(f"/field/{field_id}/context/{context_id}/option")
        else:
            # Get first context
            contexts = await client.get(f"/field/{field_id}/context")
            ctx_list = contexts.get("values", [])
            if not ctx_list:
                return _fmt({"error": "No contexts found"})
            ctx_id = ctx_list[0]["id"]
            data = await client.get(f"/field/{field_id}/context/{ctx_id}/option")
        return _fmt(data)

    @mcp.tool()
    async def create_custom_field(name: str, type_key: str, description: str = "") -> str:
        """Create a new custom field.
        type_key examples: 'com.atlassian.jira.plugin.system.customfieldtypes:textfield',
        'com.atlassian.jira.plugin.system.customfieldtypes:select'"""
        body = {"name": name, "type": type_key, "searcherKey": ""}
        if description:
            body["description"] = description
        data = await client.post("/field", body)
        return _fmt(data)

    @mcp.tool()
    async def update_custom_field(field_id: str, name: str = "", description: str = "") -> str:
        """Update custom field name/description."""
        body = {}
        if name:
            body["name"] = name
        if description:
            body["description"] = description
        await client.put(f"/field/{field_id}", body)
        return _fmt({"status": "updated", "fieldId": field_id})

    @mcp.tool()
    async def delete_custom_field(field_id: str) -> str:
        """Delete a custom field. IRREVERSIBLE."""
        await client.delete(f"/field/{field_id}")
        return _fmt({"status": "deleted", "fieldId": field_id})

    @mcp.tool()
    async def add_field_option(field_id: str, context_id: str, value: str) -> str:
        """Add option to a select/radio/checkbox field."""
        body = {"options": [{"value": value}]}
        data = await client.post(f"/field/{field_id}/context/{context_id}/option", body)
        return _fmt(data)

    @mcp.tool()
    async def list_system_fields() -> str:
        """List all fields (system + custom)."""
        data = await client.get("/field")
        system = [f for f in data if not f.get("custom", False)]
        return _fmt(system)
