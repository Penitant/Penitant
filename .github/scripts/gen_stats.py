import os
import requests
from datetime import datetime, timedelta, timezone


GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
USERNAME = os.environ.get("STATS_USERNAME", "penitant")

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}


def get_streak():
    pushed_dates = set()
    for page in range(1, 4):
        url = f"https://api.github.com/users/{USERNAME}/events?per_page=100&page={page}"
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            break
        events = resp.json()
        if not events:
            break
        for event in events:
            if event.get("type") == "PushEvent":
                pushed_dates.add(event["created_at"][:10])

    today = datetime.now(timezone.utc).date()
    anchor = today if today.isoformat() in pushed_dates else today - timedelta(days=1)

    streak = 0
    check = anchor
    while check.isoformat() in pushed_dates:
        streak += 1
        check -= timedelta(days=1)
    return streak


def get_year_contributions():
    year = datetime.now(timezone.utc).year
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
        }
      }
    }
    """
    variables = {
        "login": USERNAME,
        "from": f"{year}-01-01T00:00:00Z",
        "to": f"{year}-12-31T23:59:59Z",
    }
    resp = requests.post(
        "https://api.github.com/graphql",
        headers={**headers, "Content-Type": "application/json"},
        json={"query": query, "variables": variables},
        timeout=15,
    )
    if resp.status_code != 200:
        return 0
    col = (
        resp.json()
        .get("data", {})
        .get("user", {})
        .get("contributionsCollection", {})
    )
    return (
        col.get("totalCommitContributions", 0)
        + col.get("totalIssueContributions", 0)
        + col.get("totalPullRequestContributions", 0)
        + col.get("totalPullRequestReviewContributions", 0)
    )


def write_svg(streak, contributions):
    year = datetime.now(timezone.utc).year
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="80" viewBox="0 0 400 80">
  <rect width="400" height="80" rx="6" fill="#1a0a2e"/>
  <rect x="1" y="1" width="398" height="78" rx="5" fill="none" stroke="#2d1b4e" stroke-width="1"/>

  <text x="100" y="30" fill="#555566" font-family="ui-monospace,SFMono-Regular,monospace" font-size="11" text-anchor="middle">current streak</text>
  <text x="100" y="58" fill="#00c853" font-family="ui-monospace,SFMono-Regular,monospace" font-size="32" font-weight="bold" text-anchor="middle">{streak}</text>
  <text x="100" y="72" fill="#444455" font-family="ui-monospace,SFMono-Regular,monospace" font-size="10" text-anchor="middle">days</text>

  <rect x="200" y="14" width="1" height="52" fill="#2d1b4e"/>

  <text x="300" y="30" fill="#555566" font-family="ui-monospace,SFMono-Regular,monospace" font-size="11" text-anchor="middle">{year} contributions</text>
  <text x="300" y="58" fill="#8bc4e8" font-family="ui-monospace,SFMono-Regular,monospace" font-size="32" font-weight="bold" text-anchor="middle">{contributions}</text>
  <text x="300" y="72" fill="#444455" font-family="ui-monospace,SFMono-Regular,monospace" font-size="10" text-anchor="middle">total</text>
</svg>"""
    with open("stats.svg", "w") as f:
        f.write(svg)
    print(f"stats.svg updated — streak={streak}, contributions={contributions}")


if __name__ == "__main__":
    write_svg(get_streak(), get_year_contributions())
