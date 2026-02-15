"""X/Twitter 数据采集 — 多策略切换"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


class FetchStrategy(ABC):
    @abstractmethod
    async def fetch(self, keywords: list[str], date_range: tuple) -> list[dict]:
        ...


class ApifyStrategy(FetchStrategy):
    """Apify Tweet Scraper V2 (apidojo/tweet-scraper)"""

    ACTOR_URL = "https://api.apify.com/v2/acts/apidojo~tweet-scraper/run-sync-get-dataset-items"

    def __init__(self, config):
        self.api_key = config.twitter_scraper_key

    async def fetch(self, keywords: list[str], date_range: tuple) -> list[dict]:
        if not self.api_key:
            raise ValueError("Apify API key not configured")

        # 每组取几个关键词 OR 连接，分批搜索
        search_terms = []
        batch_size = 4
        for i in range(0, min(len(keywords), 12), batch_size):
            batch = keywords[i:i + batch_size]
            search_terms.append(" OR ".join(f'"{kw}"' for kw in batch))

        start_date, end_date = date_range

        all_items = []
        async with httpx.AsyncClient(timeout=300) as client:
            # 不设 tweetLanguage，同时抓中英文
            resp = await client.post(
                self.ACTOR_URL,
                params={"token": self.api_key},
                json={
                    "searchTerms": search_terms,
                    "maxItems": 100,
                    "sort": "Top",
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                },
            )
            resp.raise_for_status()
            all_items = resp.json()

        return [self._normalize(item) for item in all_items if self._has_text(item)]

    def _has_text(self, item: dict) -> bool:
        return bool(item.get("text") or item.get("full_text") or item.get("tweetText"))

    def _normalize(self, item: dict) -> dict:
        # Tweet Scraper V2 输出字段兼容多种格式
        text = item.get("full_text") or item.get("text") or item.get("tweetText", "")
        user = item.get("user") or item.get("author") or {}

        # 作者信息可能在不同字段
        author_name = user.get("name") or item.get("authorName", "")
        author_handle = user.get("screen_name") or user.get("userName") or item.get("authorHandle", "")
        if author_handle and not author_handle.startswith("@"):
            author_handle = "@" + author_handle

        return {
            "id": item.get("id_str") or item.get("tweetId") or item.get("id", ""),
            "author_name": author_name,
            "author_handle": author_handle,
            "text": text,
            "created_at": item.get("created_at") or item.get("createdAt") or item.get("timestamp", ""),
            "likes": item.get("favorite_count") or item.get("likeCount") or item.get("likes", 0),
            "reposts": item.get("retweet_count") or item.get("retweetCount") or item.get("reposts", 0),
            "replies": item.get("reply_count") or item.get("replyCount") or item.get("replies", 0),
            "bookmarks": item.get("bookmark_count") or item.get("bookmarkCount") or item.get("bookmarks", 0),
        }


class SocialDataStrategy(FetchStrategy):
    """SocialData.tools API"""

    BASE_URL = "https://api.socialdata.tools"

    def __init__(self, config):
        self.api_key = config.twitter_scraper_key

    async def fetch(self, keywords: list[str], date_range: tuple) -> list[dict]:
        if not self.api_key:
            raise ValueError("SocialData API key not configured")

        query = " OR ".join(keywords[:5])
        start_date, end_date = date_range

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(
                f"{self.BASE_URL}/twitter/search",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={
                    "query": query,
                    "type": "Latest",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        tweets = data.get("tweets", [])
        return [self._normalize(t) for t in tweets if t.get("full_text")]

    def _normalize(self, item: dict) -> dict:
        user = item.get("user", {})
        return {
            "id": str(item.get("id_str", "")),
            "author_name": user.get("name", ""),
            "author_handle": "@" + user.get("screen_name", ""),
            "text": item.get("full_text", ""),
            "created_at": item.get("tweet_created_at", ""),
            "likes": item.get("favorite_count", 0),
            "reposts": item.get("retweet_count", 0),
            "replies": item.get("reply_count", 0),
            "bookmarks": item.get("bookmark_count", 0),
        }


class HackerNewsStrategy(FetchStrategy):
    """Hacker News API 降级方案 — 获取 AI 相关帖子"""

    HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"

    async def fetch(self, keywords: list[str], date_range: tuple) -> list[dict]:
        start_ts = int(date_range[0].timestamp())
        end_ts = int(date_range[1].timestamp())

        results = []
        search_terms = [
            "AI coding", "LLM", "Claude", "GPT",
            "Cursor", "Copilot", "OpenAI", "Gemini",
            "Anthropic", "DeepSeek", "Llama", "Mistral",
        ]

        async with httpx.AsyncClient(timeout=30) as client:
            for term in search_terms:
                try:
                    resp = await client.get(
                        self.HN_SEARCH_URL,
                        params={
                            "query": term,
                            "tags": "story",
                            "numericFilters": f"created_at_i>{start_ts},created_at_i<{end_ts}",
                            "hitsPerPage": 10,
                        },
                    )
                    resp.raise_for_status()
                    hits = resp.json().get("hits", [])
                    for hit in hits:
                        results.append({
                            "id": f"hn_{hit.get('objectID', '')}",
                            "author_name": hit.get("author", ""),
                            "author_handle": f"@{hit.get('author', '')}",
                            "text": f"{hit.get('title', '')}. {hit.get('url', '')}",
                            "created_at": hit.get("created_at", ""),
                            "likes": hit.get("points", 0),
                            "reposts": 0,
                            "replies": hit.get("num_comments", 0),
                            "bookmarks": 0,
                        })
                except Exception as e:
                    logger.debug(f"HN search failed for '{term}': {e}")

        # 去重
        seen_ids = set()
        unique = []
        for r in results:
            if r["id"] not in seen_ids:
                seen_ids.add(r["id"])
                unique.append(r)
        return unique


class TwitterCollector:
    """多策略切换的 X 采集器"""

    def __init__(self, config):
        self.config = config
        self.strategies: list[FetchStrategy] = [
            ApifyStrategy(config),
            SocialDataStrategy(config),
            HackerNewsStrategy(),  # 降级
        ]
        self.all_keywords = []
        for group in config.twitter_keywords.values():
            self.all_keywords.extend(group)

    async def collect(self, date_range: tuple) -> list[dict]:
        for strategy in self.strategies:
            try:
                logger.info(f"Trying {strategy.__class__.__name__}...")
                results = await strategy.fetch(self.all_keywords, date_range)
                if results:
                    logger.info(f"{strategy.__class__.__name__} returned {len(results)} items")
                    return results
            except Exception as e:
                logger.warning(f"{strategy.__class__.__name__} failed: {e}")
                continue

        logger.error("All Twitter strategies failed")
        return []
