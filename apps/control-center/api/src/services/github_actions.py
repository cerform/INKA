"""Services layer: GitHub Actions API integration."""
from __future__ import annotations

import httpx
from typing import Any

from ..config import settings


class GitHubActionsService:
    def __init__(self):
        self.base_url = settings.GITHUB_API_URL
        self.headers = {
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def trigger_workflow(
        self,
        owner: str,
        repo: str,
        workflow_file: str,
        ref: str = "main",
        inputs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Trigger a workflow_dispatch event on the given repo."""
        url = f"{self.base_url}/repos/{owner}/{repo}/actions/workflows/{workflow_file}/dispatches"
        payload: dict[str, Any] = {"ref": ref}
        if inputs:
            payload["inputs"] = inputs

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            resp.raise_for_status()

        # workflow_dispatch returns 204 — no body; get the latest run
        return {"message": "Workflow dispatched", "status": resp.status_code}

    async def get_latest_run(
        self,
        owner: str,
        repo: str,
        workflow_file: str,
    ) -> dict[str, Any] | None:
        """Return the most recent run for the given workflow."""
        url = f"{self.base_url}/repos/{owner}/{repo}/actions/workflows/{workflow_file}/runs"
        params = {"per_page": 1, "page": 1}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=self.headers, params=params)
            resp.raise_for_status()
        data = resp.json()
        runs = data.get("workflow_runs", [])
        return runs[0] if runs else None

    def build_run_url(self, owner: str, repo: str, run_id: str) -> str:
        return f"https://github.com/{owner}/{repo}/actions/runs/{run_id}"


github_actions = GitHubActionsService()
