"""Issue CRUD + search tools for Jira Cloud."""

import json
from jira_client import JiraCloudClient


def _fmt(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def register_issue_tools(mcp, client: JiraCloudClient):

    @mcp.tool()
    async def jql_search(jql: str, fields: str = "summary,status,assignee,reporter,issuetype,priority,created,updated", max_results: int = 50) -> str:
        """Search Jira issues using JQL.
        Examples: 'project = HR', 'assignee = currentUser() AND status != Done'.
        Use fields to limit response size. Max 100 results."""
        data = await client.get("/search", jql=jql, fields=fields, maxResults=min(max_results, 100))
        return _fmt(data)

    @mcp.tool()
    async def get_issue(issue_key: str, fields: str = "", expand: str = "") -> str:
        """Get full issue details by key (e.g. 'PROJ-123').
        Use expand='changelog' for history, 'renderedFields' for HTML."""
        params = {}
        if fields:
            params["fields"] = fields
        if expand:
            params["expand"] = expand
        data = await client.get(f"/issue/{issue_key}", **params)
        return _fmt(data)

    @mcp.tool()
    async def create_issue(project_key: str, summary: str, issue_type: str = "Task",
                           description: str = "", assignee: str = "", priority: str = "",
                           labels: str = "", components: str = "", custom_fields: str = "") -> str:
        """Create a new Jira issue.
        Args:
            custom_fields: JSON string e.g. '{"customfield_10100": "value"}'
        """
        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
        if description:
            fields["description"] = {
                "type": "doc", "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]
            }
        if assignee:
            fields["assignee"] = {"accountId": assignee}
        if priority:
            fields["priority"] = {"name": priority}
        if labels:
            fields["labels"] = [l.strip() for l in labels.split(",")]
        if components:
            fields["components"] = [{"name": c.strip()} for c in components.split(",")]
        if custom_fields:
            fields.update(json.loads(custom_fields))
        data = await client.post("/issue", {"fields": fields})
        return _fmt(data)

    @mcp.tool()
    async def update_issue(issue_key: str, summary: str = "", description: str = "",
                           assignee: str = "", priority: str = "", labels: str = "",
                           custom_fields: str = "") -> str:
        """Update issue fields. Only non-empty fields are changed."""
        fields = {}
        if summary:
            fields["summary"] = summary
        if description:
            fields["description"] = {
                "type": "doc", "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]
            }
        if assignee:
            fields["assignee"] = {"accountId": assignee} if assignee != "__unassign__" else None
        if priority:
            fields["priority"] = {"name": priority}
        if labels:
            fields["labels"] = [l.strip() for l in labels.split(",")]
        if custom_fields:
            fields.update(json.loads(custom_fields))
        await client.put(f"/issue/{issue_key}", {"fields": fields})
        return _fmt({"status": "updated", "key": issue_key})

    @mcp.tool()
    async def transition_issue(issue_key: str, transition_name: str, comment: str = "",
                               resolution: str = "") -> str:
        """Move issue to a new status via workflow transition."""
        # Find transition ID by name
        transitions = await client.get(f"/issue/{issue_key}/transitions")
        target = None
        for t in transitions.get("transitions", []):
            if t["name"].lower() == transition_name.lower():
                target = t
                break
        if not target:
            available = [t["name"] for t in transitions.get("transitions", [])]
            return _fmt({"error": f"Transition '{transition_name}' not found", "available": available})
        body = {"transition": {"id": target["id"]}}
        if comment:
            body["update"] = {"comment": [{"add": {"body": {
                "type": "doc", "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment}]}]
            }}}]}
        if resolution:
            body.setdefault("fields", {})["resolution"] = {"name": resolution}
        await client.post(f"/issue/{issue_key}/transitions", body)
        return _fmt({"status": "transitioned", "key": issue_key, "to": target["to"]["name"]})

    @mcp.tool()
    async def assign_issue(issue_key: str, assignee: str) -> str:
        """Assign issue. Use empty string to unassign."""
        body = {"accountId": assignee if assignee else None}
        await client.put(f"/issue/{issue_key}/assignee", body)
        return _fmt({"status": "assigned", "key": issue_key, "assignee": assignee or "unassigned"})

    @mcp.tool()
    async def add_comment(issue_key: str, body: str) -> str:
        """Add a comment to an issue."""
        comment_body = {
            "body": {
                "type": "doc", "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": body}]}]
            }
        }
        data = await client.post(f"/issue/{issue_key}/comment", comment_body)
        return _fmt(data)

    @mcp.tool()
    async def get_issue_comments(issue_key: str, max_results: int = 50) -> str:
        """Get comments on an issue."""
        data = await client.get(f"/issue/{issue_key}/comment", maxResults=max_results)
        return _fmt(data)

    @mcp.tool()
    async def get_issue_changelog(issue_key: str, max_results: int = 50) -> str:
        """Get change history of an issue — who changed what and when."""
        data = await client.get(f"/issue/{issue_key}/changelog", maxResults=max_results)
        return _fmt(data)

    @mcp.tool()
    async def get_issue_transitions(issue_key: str) -> str:
        """Get available transitions for an issue."""
        data = await client.get(f"/issue/{issue_key}/transitions")
        return _fmt(data)

    @mcp.tool()
    async def get_issue_worklogs(issue_key: str, max_results: int = 50) -> str:
        """Get work logs for an issue."""
        data = await client.get(f"/issue/{issue_key}/worklog", maxResults=max_results)
        return _fmt(data)

    @mcp.tool()
    async def add_worklog(issue_key: str, time_spent_seconds: int, comment: str = "") -> str:
        """Add a worklog entry."""
        body = {"timeSpentSeconds": time_spent_seconds}
        if comment:
            body["comment"] = {
                "type": "doc", "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment}]}]
            }
        data = await client.post(f"/issue/{issue_key}/worklog", body)
        return _fmt(data)

    @mcp.tool()
    async def link_issues(inward_key: str, outward_key: str, link_type: str = "Relates") -> str:
        """Link two issues."""
        body = {
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_key},
            "outwardIssue": {"key": outward_key},
        }
        await client.post("/issueLink", body)
        return _fmt({"status": "linked", "inward": inward_key, "outward": outward_key, "type": link_type})

    @mcp.tool()
    async def delete_issue(issue_key: str, delete_subtasks: bool = False) -> str:
        """Delete an issue. IRREVERSIBLE."""
        await client.delete(f"/issue/{issue_key}?deleteSubtasks={str(delete_subtasks).lower()}")
        return _fmt({"status": "deleted", "key": issue_key})

    @mcp.tool()
    async def bulk_transition(jql: str, transition_name: str, comment: str = "", max_issues: int = 50) -> str:
        """Bulk transition issues matching JQL. Max 50."""
        search = await client.get("/search", jql=jql, fields="key", maxResults=min(max_issues, 50))
        results = []
        for issue in search.get("issues", []):
            key = issue["key"]
            try:
                transitions = await client.get(f"/issue/{key}/transitions")
                target = None
                for t in transitions.get("transitions", []):
                    if t["name"].lower() == transition_name.lower():
                        target = t
                        break
                if target:
                    body = {"transition": {"id": target["id"]}}
                    if comment:
                        body["update"] = {"comment": [{"add": {"body": {
                            "type": "doc", "version": 1,
                            "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment}]}]
                        }}}]}
                    await client.post(f"/issue/{key}/transitions", body)
                    results.append({"key": key, "status": "ok", "to": target["to"]["name"]})
                else:
                    results.append({"key": key, "status": "skip", "reason": "transition not available"})
            except Exception as e:
                results.append({"key": key, "status": "error", "reason": str(e)})
        return _fmt({"transitioned": len([r for r in results if r["status"] == "ok"]), "results": results})
