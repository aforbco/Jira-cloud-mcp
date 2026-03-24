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

    # --- Workflow transition rules (post-functions, validators, conditions, properties) ---

    @mcp.tool()
    async def create_workflow(workflow_json: str) -> str:
        """Create a new workflow via Cloud API.

        Args:
            workflow_json: Full workflow definition as JSON string. Must contain:
                - statuses: array of {"id": "status_id", "properties": {}}
                - workflows: array with one workflow object containing:
                  - name, description
                  - statuses: array of {"statusReference": "status_id"}
                  - transitions: array of transition objects with name, from, to, type, rules
        Example transition types: 'initial' (create), 'directed' (normal)
        """
        body = json.loads(workflow_json)
        data = await client.post("/workflows/create", body)
        return _fmt(data)

    async def _get_workflow_full(workflow_name: str) -> dict:
        """Get full workflow with transitions and rules for modification."""
        data = await client.get("/workflow/search", workflowName=workflow_name,
                                expand="transitions.rules,transitions.properties,statuses")
        workflows = data.get("values", [])
        if not workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        return workflows[0]

    async def _update_workflow(workflow: dict) -> dict:
        """Update workflow via Cloud API. Sends full workflow definition."""
        entity_id = workflow["id"]["entityId"]
        body = {
            "workflows": [workflow],
            "payload": {
                "scope": {"type": "GLOBAL"}
            }
        }
        return await client.post("/workflows/update", body)

    @mcp.tool()
    async def get_workflow_transition(workflow_name: str, transition_id: str) -> str:
        """Get a specific workflow transition with all rules (post-functions, validators, conditions, properties).

        Args:
            workflow_name: Workflow name
            transition_id: Transition ID (e.g. '11', '21')
        """
        wf = await _get_workflow_full(workflow_name)
        for t in wf.get("transitions", []):
            if str(t["id"]) == str(transition_id):
                return _fmt(t)
        return _fmt({"error": f"Transition {transition_id} not found", "available": [
            {"id": t["id"], "name": t["name"]} for t in wf.get("transitions", [])
        ]})

    @mcp.tool()
    async def add_post_function(workflow_name: str, transition_id: str,
                                function_type: str, configuration: str = "{}") -> str:
        """Add a post-function to a workflow transition.

        Args:
            workflow_name: Workflow name
            transition_id: Transition ID
            function_type: Built-in type, e.g.:
                'AssignToCurrentUserFunction', 'UpdateIssueFieldFunction',
                'CreateCommentFunction', 'FireIssueEventFunction',
                'CopyValueFromOtherFieldPostFunction', 'SetIssueSecurityFromRoleFunction',
                'UpdateIssueStatusFunction', 'GenerateChangeHistoryFunction',
                'IssueReindexFunction', 'UpdateIssueCustomFieldPostFunction'
            configuration: JSON config, e.g. '{"fieldId": "resolution", "fieldValue": ""}' for UpdateIssueFieldFunction
        """
        wf = await _get_workflow_full(workflow_name)
        config = json.loads(configuration) if configuration and configuration != "{}" else None
        for t in wf.get("transitions", []):
            if str(t["id"]) == str(transition_id):
                pf = {"type": function_type}
                if config:
                    pf["configuration"] = config
                t.setdefault("rules", {}).setdefault("postFunctions", []).append(pf)
                result = await _update_workflow(wf)
                return _fmt({"status": "added", "type": function_type, "transition": t["name"]})
        return _fmt({"error": f"Transition {transition_id} not found"})

    @mcp.tool()
    async def add_validator(workflow_name: str, transition_id: str,
                            validator_type: str, configuration: str = "{}") -> str:
        """Add a validator to a workflow transition.

        Args:
            workflow_name: Workflow name
            transition_id: Transition ID
            validator_type: Built-in type, e.g.:
                'PermissionValidator' (config: {"permissionKey": "CREATE_ISSUES"}),
                'FieldRequiredValidator' (config: {"fieldId": "assignee"}),
                'FieldHasSingleValueValidator', 'RegexpFieldValidator',
                'ParentStatusValidator', 'PreviousStatusValidator',
                'WindowsDateValidator'
            configuration: JSON config for the validator
        """
        wf = await _get_workflow_full(workflow_name)
        config = json.loads(configuration) if configuration and configuration != "{}" else None
        for t in wf.get("transitions", []):
            if str(t["id"]) == str(transition_id):
                v = {"type": validator_type}
                if config:
                    v["configuration"] = config
                t.setdefault("rules", {}).setdefault("validators", []).append(v)
                result = await _update_workflow(wf)
                return _fmt({"status": "added", "type": validator_type, "transition": t["name"]})
        return _fmt({"error": f"Transition {transition_id} not found"})

    @mcp.tool()
    async def set_condition(workflow_name: str, transition_id: str,
                            conditions_json: str) -> str:
        """Set conditions on a workflow transition (replaces existing conditions).

        Args:
            workflow_name: Workflow name
            transition_id: Transition ID
            conditions_json: JSON condition tree. Examples:
                Simple: '{"nodeType": "simple", "type": "AllowOnlyAssignee"}'
                Permission: '{"nodeType": "simple", "type": "PermissionCondition", "configuration": {"permissionKey": "RESOLVE_ISSUES"}}'
                AND compound: '{"nodeType": "compound", "operator": "AND", "conditions": [...]}'
                Group: '{"nodeType": "simple", "type": "InGroupCondition", "configuration": {"group": "jira-admins"}}'
                Status: '{"nodeType": "simple", "type": "StatusCondition", "configuration": {"statusId": "1"}}'
        """
        wf = await _get_workflow_full(workflow_name)
        conditions = json.loads(conditions_json)
        for t in wf.get("transitions", []):
            if str(t["id"]) == str(transition_id):
                t.setdefault("rules", {})["conditionsTree"] = conditions
                result = await _update_workflow(wf)
                return _fmt({"status": "set", "transition": t["name"]})
        return _fmt({"error": f"Transition {transition_id} not found"})

    @mcp.tool()
    async def set_transition_property(workflow_name: str, transition_id: str,
                                      key: str, value: str) -> str:
        """Set a property on a workflow transition.

        Args:
            workflow_name: Workflow name
            transition_id: Transition ID
            key: Property key (e.g. 'jira.field.resolution.include', 'jira.issue.editable')
            value: Property value
        """
        wf = await _get_workflow_full(workflow_name)
        for t in wf.get("transitions", []):
            if str(t["id"]) == str(transition_id):
                props = t.setdefault("properties", {})
                props[key] = value
                result = await _update_workflow(wf)
                return _fmt({"status": "set", "key": key, "value": value, "transition": t["name"]})
        return _fmt({"error": f"Transition {transition_id} not found"})

    @mcp.tool()
    async def remove_post_function(workflow_name: str, transition_id: str,
                                   function_type: str) -> str:
        """Remove a post-function from a workflow transition by type.

        Args:
            workflow_name: Workflow name
            transition_id: Transition ID
            function_type: Type to remove (e.g. 'AssignToCurrentUserFunction')
        """
        wf = await _get_workflow_full(workflow_name)
        for t in wf.get("transitions", []):
            if str(t["id"]) == str(transition_id):
                pfs = t.get("rules", {}).get("postFunctions", [])
                before = len(pfs)
                t["rules"]["postFunctions"] = [pf for pf in pfs if pf.get("type") != function_type]
                after = len(t["rules"]["postFunctions"])
                if before == after:
                    return _fmt({"error": f"Post-function '{function_type}' not found on transition"})
                result = await _update_workflow(wf)
                return _fmt({"status": "removed", "type": function_type, "removed": before - after})
        return _fmt({"error": f"Transition {transition_id} not found"})

    @mcp.tool()
    async def remove_validator(workflow_name: str, transition_id: str,
                               validator_type: str) -> str:
        """Remove a validator from a workflow transition by type.

        Args:
            workflow_name: Workflow name
            transition_id: Transition ID
            validator_type: Type to remove (e.g. 'PermissionValidator')
        """
        wf = await _get_workflow_full(workflow_name)
        for t in wf.get("transitions", []):
            if str(t["id"]) == str(transition_id):
                vs = t.get("rules", {}).get("validators", [])
                before = len(vs)
                t["rules"]["validators"] = [v for v in vs if v.get("type") != validator_type]
                after = len(t["rules"]["validators"])
                if before == after:
                    return _fmt({"error": f"Validator '{validator_type}' not found on transition"})
                result = await _update_workflow(wf)
                return _fmt({"status": "removed", "type": validator_type, "removed": before - after})
        return _fmt({"error": f"Transition {transition_id} not found"})

    @mcp.tool()
    async def remove_condition(workflow_name: str, transition_id: str) -> str:
        """Remove all conditions from a workflow transition.

        Args:
            workflow_name: Workflow name
            transition_id: Transition ID
        """
        wf = await _get_workflow_full(workflow_name)
        for t in wf.get("transitions", []):
            if str(t["id"]) == str(transition_id):
                if "conditionsTree" in t.get("rules", {}):
                    del t["rules"]["conditionsTree"]
                    result = await _update_workflow(wf)
                    return _fmt({"status": "removed", "transition": t["name"]})
                return _fmt({"error": "No conditions on this transition"})
        return _fmt({"error": f"Transition {transition_id} not found"})

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
