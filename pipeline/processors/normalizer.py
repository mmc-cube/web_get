"""标准化处理器：将各数据源原始数据转换为统一模型"""

import re
import hashlib
from datetime import datetime
from typing import Optional

from dateutil import parser as dateparser

from pipeline.models.schemas import Tweet, Repo, Quest, MarketSignal


class Normalizer:

    def normalize_tweets(self, raw_tweets: list[dict]) -> list[Tweet]:
        results = []
        for raw in raw_tweets:
            try:
                tweet = Tweet(
                    id=raw.get("id") or self._generate_id(raw),
                    author_name=raw.get("author_name", "Unknown"),
                    author_handle=raw.get("author_handle", "@unknown"),
                    text=self._clean_text(raw.get("text", "")),
                    lang=self._detect_lang(raw.get("text", "")),
                    created_at=self._parse_time(raw.get("created_at")),
                    likes=int(raw.get("likes", 0)),
                    reposts=int(raw.get("reposts", 0)),
                    replies=int(raw.get("replies", 0)),
                    bookmarks=int(raw.get("bookmarks", 0)),
                    urls=self._extract_urls(raw.get("text", "")),
                    tags=self._classify_tags(raw.get("text", "")),
                    is_ad_suspect=self._detect_ad(raw.get("text", "")),
                )
                results.append(tweet)
            except Exception as e:
                print(f"[Normalizer] Skip tweet: {e}")
        return results

    def normalize_repos(self, raw_repos: list[dict]) -> list[Repo]:
        results = []
        for raw in raw_repos:
            try:
                created = self._parse_time(raw.get("created_at"))
                # 统一去掉时区信息再比较
                created_naive = created.replace(tzinfo=None) if created else None
                is_new = (datetime.now() - created_naive).days <= 30 if created_naive else False
                repo = Repo(
                    name=raw.get("name", ""),
                    owner=raw.get("owner", ""),
                    description=raw.get("description", ""),
                    stars=int(raw.get("stars", 0)),
                    forks=int(raw.get("forks", 0)),
                    stars_24h=int(raw.get("stars_24h", 0)),
                    created_at=created,
                    language=raw.get("language", ""),
                    topics=raw.get("topics", []),
                    readme_summary=raw.get("readme_summary", ""),
                    relevance_tags=self._tag_repo(raw),
                    is_new=is_new,
                    trending_days=int(raw.get("trending_days", 1)),
                    trend_status=raw.get("trend_status", "new"),
                    watchers=int(raw.get("watchers", 0)),
                    open_issues=int(raw.get("open_issues", 0)),
                )
                results.append(repo)
            except Exception as e:
                print(f"[Normalizer] Skip repo: {e}")
        return results

    def normalize_quests(self, raw_quests: list[dict]) -> list[Quest]:
        return [
            Quest(
                platform=q.get("platform", ""),
                title=q.get("title", ""),
                task_type=q.get("task_type", ""),
                cost_tag=q.get("cost_tag", "未知"),
                risk_tag=q.get("risk_tag", "未知"),
                deadline=q.get("deadline"),
                url=q.get("url", ""),
                note=q.get("note", ""),
            )
            for q in raw_quests
        ]

    def normalize_markets(self, raw_markets: list[dict]) -> list[MarketSignal]:
        return [
            MarketSignal(
                title=m.get("title", ""),
                summary=m.get("summary", ""),
                volume=m.get("volume"),
                odds_change=m.get("odds_change"),
                url=m.get("url", ""),
            )
            for m in raw_markets
        ]

    # ---- 内部方法 ----

    def _generate_id(self, raw: dict) -> str:
        text = raw.get("text", "") + raw.get("author_handle", "")
        return hashlib.md5(text.encode()).hexdigest()[:16]

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"https?://\S+", "", text)  # 移除 URL（单独存 urls 字段）
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _detect_lang(self, text: str) -> str:
        chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        return "zh" if chinese_chars / max(len(text), 1) > 0.3 else "en"

    def _parse_time(self, raw_time) -> datetime:
        if raw_time is None:
            return datetime.now()
        if isinstance(raw_time, datetime):
            return raw_time
        try:
            return dateparser.parse(str(raw_time))
        except Exception:
            return datetime.now()

    def _extract_urls(self, text: str) -> list[str]:
        return re.findall(r"https?://[^\s)<>\"]+", text)

    def _classify_tags(self, text: str) -> list[str]:
        tags = []
        t = text.lower()
        if any(w in t for w in ["released", "launched", "发布", "上线", "announcing"]):
            tags.append("发布")
        if any(w in t for w in ["tutorial", "教程", "how to", "guide", "step by step"]):
            tags.append("教程")
        if "github.com" in t:
            tags.append("repo")
        if any(w in t for w in ["demo", "演示", "showcase", "built with"]):
            tags.append("demo")
        if any(w in t for w in ["opinion", "观点", "i think", "hot take", "我认为"]):
            tags.append("观点")
        if any(w in t for w in ["update", "更新", "v0.", "v1.", "v2.", "changelog"]):
            tags.append("工具更新")
        if any(w in t for w in ["model", "模型", "gpt", "claude", "gemini", "llama"]):
            tags.append("模型更新")
        return tags or ["观点"]

    def _detect_ad(self, text: str) -> bool:
        ad_signals = [
            "referral", "promo code", "discount", "合约地址",
            "airdrop claim", "limited time", "返佣",
            "use my link", "sign up with", "exclusive offer",
            "free tokens", "whitelist spot",
        ]
        t = text.lower()
        score = sum(1 for s in ad_signals if s in t)
        return score >= 2

    def _tag_repo(self, raw: dict) -> list[str]:
        tags = []
        desc = (raw.get("description", "") + " " + " ".join(raw.get("topics", []))).lower()
        tag_map = {
            "coding agent": ["agent", "coding agent", "agentic"],
            "IDE": ["ide", "editor", "copilot", "cursor"],
            "workflow": ["workflow", "automation", "ci/cd", "pipeline"],
            "eval": ["eval", "benchmark", "leaderboard"],
            "RAG": ["rag", "retrieval", "embedding", "vector"],
            "tooling": ["tool", "framework", "library", "sdk", "infra"],
        }
        for tag, keywords in tag_map.items():
            if any(kw in desc for kw in keywords):
                tags.append(tag)
        return tags or ["tooling"]
