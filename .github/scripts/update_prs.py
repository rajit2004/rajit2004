"""
update_prs.py
-------------
Fetches all merged PRs by rajit2004 on external repos
and updates the Open Source Contributions section in profile README.

Runs via GitHub Actions — needs GITHUB_TOKEN secret.
"""

import os
import re
import requests
from datetime import datetime

USERNAME   = "rajit2004"
README     = "README.md"
GH_TOKEN   = os.environ.get("GITHUB_TOKEN", "")

HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Repos to skip (own repos and noise)
OWN_REPOS = {
    "rajit2004/java_progress", "rajit2004/rajit2004", "rajit2004/InnerCircle",
    "rajit2004/DeepSeekWidget", "rajit2004/LeetCode-Tracker",
    "rajit2004/PARKING-MANAGEMENT-SYSTEM-Enhanced-v2.0",
    "rajit2004/animal-disease-predictor", "rajit2004/student-performance-prediction",
    "rajit2004/yt-analytics-tracker", "rajit2004/ModedRepo_ParkingSystem",
    "rajit2004/postgresql-mastery", "rajit2004/hello_devs",
    "rajit2004/local_to_remote", "rajit2004/.github",
    "rajit2004/Rhythma", "rajit2004/ss_ai", "rajit2004/linkid",
    "rajit2004/ChatApp", "rajit2004/Memori", "rajit2004/awesome-deepseek-integration",
    "rajit2004/github-readme-stats", "rajit2004/awesome-deepseek-integration",
}

def fetch_merged_prs() -> list[dict]:
    """Search GitHub for all merged PRs by the user on external repos."""
    prs = []
    page = 1
    while True:
        url = "https://api.github.com/search/issues"
        params = {
            "q": f"type:pr author:{USERNAME} is:merged is:closed",
            "sort": "updated",
            "order": "desc",
            "per_page": 100,
            "page": page,
        }
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        items = data.get("items", [])
        if not items:
            break
        prs.extend(items)
        if len(prs) >= data.get("total_count", 0):
            break
        page += 1

    # Filter out own repos
    result = []
    for pr in prs:
        repo = pr["repository_url"].replace("https://api.github.com/repos/", "")
        if repo not in OWN_REPOS:
            pr["_repo"] = repo
            result.append(pr)

    return result


def build_section(prs: list[dict]) -> str:
    """Build the markdown table for the contributions section."""

    # Group by repo
    by_repo: dict[str, list] = {}
    for pr in prs:
        repo = pr["_repo"]
        by_repo.setdefault(repo, []).append(pr)

    rows = []
    for repo, repo_prs in sorted(by_repo.items()):
        count = len(repo_prs)
        # Most recent PR date
        dates = [pr.get("closed_at") or pr.get("updated_at") for pr in repo_prs]
        latest = max(d for d in dates if d)[:10]  # YYYY-MM-DD

        # Best PR title (longest/most descriptive)
        titles = sorted(repo_prs, key=lambda p: len(p["title"]), reverse=True)
        sample = titles[0]["title"][:60] + ("…" if len(titles[0]["title"]) > 60 else "")

        repo_url = f"https://github.com/{repo}"
        rows.append(
            f"| [{repo}]({repo_url}) | {count} | {sample} | {latest} |"
        )

    total = sum(len(v) for v in by_repo.values())
    updated = datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")

    table = "\n".join(rows)
    return f"""<!-- CONTRIBUTIONS_START -->
## 🤝 Open Source Contributions

> **{total} merged PRs** across **{len(by_repo)} repositories** · Auto-updated {updated}

| Repository | PRs Merged | Latest Contribution | Date |
|------------|:----------:|---------------------|------|
{table}
<!-- CONTRIBUTIONS_END -->"""


def update_readme(new_section: str) -> None:
    with open(README, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"<!-- CONTRIBUTIONS_START -->.*?<!-- CONTRIBUTIONS_END -->"
    if re.search(pattern, content, flags=re.DOTALL):
        updated = re.sub(pattern, new_section, content, flags=re.DOTALL)
    else:
        # Insert before the Support section
        anchor = "## 💖 Support My Work"
        updated = content.replace(anchor, new_section + "\n\n---\n\n" + anchor)

    with open(README, "w", encoding="utf-8") as f:
        f.write(updated)
    print(f"[+] README updated — {new_section.count('|') // 5} repos listed.")


def main():
    print("Fetching merged PRs...")
    prs = fetch_merged_prs()
    print(f"  Found {len(prs)} merged PRs on external repos.")
    section = build_section(prs)
    update_readme(section)


if __name__ == "__main__":
    main()
