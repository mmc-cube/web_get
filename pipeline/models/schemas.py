"""数据模型定义"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Tweet:
    id: str
    author_name: str
    author_handle: str
    text: str
    lang: str  # "en" | "zh"
    created_at: datetime
    likes: int = 0
    reposts: int = 0
    replies: int = 0
    bookmarks: int = 0
    urls: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    is_ad_suspect: bool = False
    cluster_id: Optional[str] = None
    heat_score: float = 0.0


@dataclass
class Repo:
    name: str  # owner/repo
    owner: str
    description: str
    stars: int
    forks: int
    stars_24h: int
    created_at: datetime
    language: str
    topics: list[str] = field(default_factory=list)
    readme_summary: str = ""
    relevance_tags: list[str] = field(default_factory=list)
    is_new: bool = False  # 创建 ≤ 30 天
    trending_days: int = 1  # 连续在榜天数
    trend_status: str = ""  # "new" | "rising" | "steady" | "declining"
    watchers: int = 0
    open_issues: int = 0


@dataclass
class EventCluster:
    id: str
    title: str
    theme: str
    heat_score: float
    keywords: list[str]
    tweet_ids: list[str]
    repo_names: list[str] = field(default_factory=list)


@dataclass
class Quest:
    platform: str
    title: str
    task_type: str
    cost_tag: str
    risk_tag: str
    deadline: Optional[str] = None
    url: str = ""
    note: str = ""


@dataclass
class MarketSignal:
    title: str
    summary: str
    volume: Optional[str] = None
    odds_change: Optional[str] = None
    url: str = ""


@dataclass
class BriefItem:
    conclusion: str
    why_hot: str
    evidence_urls: list[str]
    category: str  # "ai" | "github" | "web3"


@dataclass
class DailyOutput:
    date: str
    generated_at: str
    brief: list[BriefItem]
    top_tweets: list[Tweet]
    github_trending: list[Repo]
    github_new: list[Repo]
    clusters: list[EventCluster]
    quests: list[Quest]
    markets: list[MarketSignal]
    meta: dict = field(default_factory=dict)
