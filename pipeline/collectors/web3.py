"""Web3 数据采集（轻量）"""

import logging
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class Web3Collector:

    def __init__(self, config):
        self.config = config

    async def collect(self) -> dict:
        quests = await self._collect_quests()
        markets = await self._collect_polymarket()
        return {"quests": quests, "markets": markets}

    async def _collect_quests(self) -> list[dict]:
        """采集撸毛机会（多平台聚合）"""
        results = []

        async with httpx.AsyncClient(timeout=30) as client:
            # Galxe 热门活动
            galxe = await self._fetch_galxe(client)
            results.extend(galxe)

            # Layer3 任务
            layer3 = await self._fetch_layer3(client)
            results.extend(layer3)

        return results[:5]  # 最多 5 条

    async def _fetch_galxe(self, client: httpx.AsyncClient) -> list[dict]:
        """抓取 Galxe 热门活动"""
        try:
            # Galxe GraphQL API
            resp = await client.post(
                "https://graphigo.prd.galaxy.eco/query",
                json={
                    "query": """
                    query {
                        campaigns(input: {
                            forAdmin: false,
                            first: 10,
                            status: Active,
                            listType: Trending
                        }) {
                            list {
                                name
                                type
                                status
                                chain
                                endTime
                                space { name alias }
                            }
                        }
                    }
                    """,
                },
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            campaigns = data.get("data", {}).get("campaigns", {}).get("list", [])

            return [
                {
                    "platform": "Galxe",
                    "title": c.get("name", ""),
                    "task_type": "积分任务" if c.get("type") == "Points" else "测试网",
                    "cost_tag": "0成本",
                    "risk_tag": "较低",
                    "deadline": c.get("endTime"),
                    "url": f"https://galxe.com/{c.get('space', {}).get('alias', '')}",
                    "note": f"来自 {c.get('space', {}).get('name', '')} 的热门活动",
                }
                for c in campaigns[:3]
            ]
        except Exception as e:
            logger.warning(f"Galxe fetch failed: {e}")
            return []

    async def _fetch_layer3(self, client: httpx.AsyncClient) -> list[dict]:
        """抓取 Layer3 任务"""
        try:
            resp = await client.get(
                "https://layer3.xyz/api/quests",
                params={"limit": 5, "sort": "trending"},
            )
            if resp.status_code != 200:
                return []

            quests = resp.json() if isinstance(resp.json(), list) else resp.json().get("quests", [])
            return [
                {
                    "platform": "Layer3",
                    "title": q.get("title", ""),
                    "task_type": "积分任务",
                    "cost_tag": "0成本",
                    "risk_tag": "较低",
                    "deadline": q.get("endDate"),
                    "url": f"https://layer3.xyz/quests/{q.get('slug', '')}",
                    "note": q.get("description", "")[:80],
                }
                for q in quests[:2]
            ]
        except Exception as e:
            logger.warning(f"Layer3 fetch failed: {e}")
            return []

    async def _collect_polymarket(self) -> list[dict]:
        """采集 Polymarket 热门市场"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    "https://gamma-api.polymarket.com/markets",
                    params={
                        "limit": 10,
                        "active": True,
                        "order": "volume24hr",
                        "ascending": False,
                    },
                )
                if resp.status_code != 200:
                    return []

                markets = resp.json()
                # 筛选 AI/Tech 相关
                ai_keywords = ["ai", "artificial intelligence", "coding", "programming", "tech"]
                filtered = []
                for m in markets:
                    question = (m.get("question", "") + m.get("description", "")).lower()
                    if any(kw in question for kw in ai_keywords):
                        filtered.append({
                            "title": m.get("question", ""),
                            "summary": m.get("description", "")[:120],
                            "volume": f"${int(m.get('volume24hr', 0)):,}",
                            "odds_change": None,
                            "url": f"https://polymarket.com/event/{m.get('slug', '')}",
                        })

                return filtered[:2]
        except Exception as e:
            logger.warning(f"Polymarket fetch failed: {e}")
            return []
