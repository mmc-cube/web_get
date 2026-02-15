"""GitHub 趋势数据采集"""

import json
import re
import logging
from datetime import datetime, timedelta
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class GitHubCollector:

    TRENDING_URL = "https://github.com/trending"
    API_BASE = "https://api.github.com"

    def __init__(self, config):
        self.token = config.github_token
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        self.data_dir = Path(config.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def collect(self) -> dict:
        async with httpx.AsyncClient(timeout=30, headers=self.headers) as client:
            trending = await self._scrape_trending(client)
            detailed = await self._enrich_with_api(client, trending)

            # 与昨日数据对比，标注趋势状态
            detailed = self._compare_with_history(detailed)
            self._save_today_snapshot(detailed)

            new_repos = self._filter_new_repos(detailed)
            return {
                "trending": detailed[:15],
                "new": new_repos[:10],
            }

    async def _scrape_trending(self, client: httpx.AsyncClient) -> list[dict]:
        """解析 github.com/trending 页面"""
        repos = []
        for lang in ["", "python", "typescript", "rust"]:
            url = f"{self.TRENDING_URL}/{lang}?since=daily" if lang else f"{self.TRENDING_URL}?since=daily"
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                page_repos = self._parse_trending_page(resp.text)
                repos.extend(page_repos)
            except Exception as e:
                logger.warning(f"Failed to scrape trending/{lang}: {e}")

        # 去重
        seen = set()
        unique = []
        for r in repos:
            if r["name"] not in seen:
                seen.add(r["name"])
                unique.append(r)
        return unique

    def _parse_trending_page(self, html: str) -> list[dict]:
        """解析 trending 页面 HTML"""
        soup = BeautifulSoup(html, "lxml")
        repos = []

        for article in soup.select("article.Box-row"):
            try:
                h2 = article.select_one("h2 a")
                if not h2:
                    continue
                full_name = h2.get("href", "").strip("/")
                if "/" not in full_name:
                    continue
                owner, name = full_name.split("/", 1)

                desc_el = article.select_one("p")
                description = desc_el.get_text(strip=True) if desc_el else ""

                lang_el = article.select_one("[itemprop='programmingLanguage']")
                language = lang_el.get_text(strip=True) if lang_el else ""

                stars_el = article.select("a.Link--muted")
                stars = 0
                forks = 0
                if len(stars_el) >= 1:
                    stars = self._parse_number(stars_el[0].get_text(strip=True))
                if len(stars_el) >= 2:
                    forks = self._parse_number(stars_el[1].get_text(strip=True))

                stars_today_el = article.select_one("span.d-inline-block.float-sm-right")
                stars_24h = 0
                if stars_today_el:
                    match = re.search(r"([\d,]+)", stars_today_el.get_text())
                    if match:
                        stars_24h = int(match.group(1).replace(",", ""))

                repos.append({
                    "name": full_name,
                    "owner": owner,
                    "description": description,
                    "stars": stars,
                    "forks": forks,
                    "stars_24h": stars_24h,
                    "language": language,
                    "created_at": None,
                    "topics": [],
                    "readme_summary": "",
                    "watchers": 0,
                    "open_issues": 0,
                })
            except Exception as e:
                logger.debug(f"Parse error for article: {e}")
                continue

        return repos

    async def _enrich_with_api(self, client: httpx.AsyncClient, repos: list[dict]) -> list[dict]:
        """用 GitHub API 补充详细信息"""
        enriched = []
        for repo in repos[:20]:
            try:
                resp = await client.get(f"{self.API_BASE}/repos/{repo['name']}")
                if resp.status_code == 200:
                    data = resp.json()
                    repo["created_at"] = data.get("created_at")
                    repo["topics"] = data.get("topics", [])
                    repo["description"] = data.get("description") or repo["description"]
                    repo["stars"] = data.get("stargazers_count", repo["stars"])
                    repo["forks"] = data.get("forks_count", repo["forks"])
                    repo["watchers"] = data.get("subscribers_count", 0)
                    repo["open_issues"] = data.get("open_issues_count", 0)
                elif resp.status_code == 403:
                    logger.warning("GitHub API rate limited, skipping enrichment")
                    break
            except Exception as e:
                logger.debug(f"API enrich failed for {repo['name']}: {e}")
            enriched.append(repo)

        enriched.extend(repos[20:])
        return enriched

    def _compare_with_history(self, repos: list[dict]) -> list[dict]:
        """与昨日快照对比，计算连续在榜天数和趋势状态"""
        yesterday = self._load_yesterday_snapshot()
        yesterday_names = {r["name"] for r in yesterday}
        yesterday_map = {r["name"]: r for r in yesterday}

        today_names = {r["name"] for r in repos}

        for repo in repos:
            name = repo["name"]
            if name in yesterday_map:
                prev = yesterday_map[name]
                repo["trending_days"] = prev.get("trending_days", 1) + 1
                # 判断增长加速还是减速
                prev_stars_24h = prev.get("stars_24h", 0)
                if repo["stars_24h"] > prev_stars_24h * 1.2:
                    repo["trend_status"] = "rising"
                elif repo["stars_24h"] < prev_stars_24h * 0.5:
                    repo["trend_status"] = "declining"
                else:
                    repo["trend_status"] = "steady"
            else:
                repo["trending_days"] = 1
                repo["trend_status"] = "new"

        return repos

    def _load_yesterday_snapshot(self) -> list[dict]:
        """加载昨日快照"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        snapshot_file = self.data_dir / f"github_snapshot_{yesterday}.json"
        if snapshot_file.exists():
            try:
                return json.loads(snapshot_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return []

    def _save_today_snapshot(self, repos: list[dict]):
        """保存今日快照供明天对比"""
        today = datetime.now().strftime("%Y-%m-%d")
        snapshot_file = self.data_dir / f"github_snapshot_{today}.json"
        snapshot = [
            {
                "name": r["name"],
                "stars": r["stars"],
                "stars_24h": r["stars_24h"],
                "trending_days": r.get("trending_days", 1),
            }
            for r in repos
        ]
        snapshot_file.write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")

    def _filter_new_repos(self, repos: list[dict]) -> list[dict]:
        """筛选创建 ≤ 30 天的新 repo"""
        cutoff = datetime.now() - timedelta(days=30)
        new_repos = []
        for r in repos:
            if r.get("created_at"):
                try:
                    created = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
                    if created.replace(tzinfo=None) > cutoff:
                        r["is_new"] = True
                        new_repos.append(r)
                except Exception:
                    pass
        new_repos.sort(key=lambda r: r.get("stars_24h", 0), reverse=True)
        return new_repos

    def _parse_number(self, text: str) -> int:
        text = text.strip().replace(",", "")
        try:
            return int(text)
        except ValueError:
            return 0
