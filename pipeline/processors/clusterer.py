"""事件级聚类 + 主题级归类"""

import re
import hashlib
from collections import defaultdict
from urllib.parse import urlparse

from pipeline.models.schemas import Tweet, EventCluster


class Clusterer:

    THEME_KEYWORDS = {
        "Coding Agents": ["agent", "agentic", "coding agent", "autonomous", "自主"],
        "IDE / Copilot Tools": ["cursor", "copilot", "IDE", "editor", "vscode", "编辑器"],
        "Workflow Automation": ["workflow", "automation", "CI/CD", "pipeline", "自动化"],
        "Model Releases & Updates": ["released", "launched", "model", "update", "版本", "发布", "模型"],
        "Tooling / Infra": ["tool", "infra", "framework", "library", "SDK", "MCP"],
        "Evaluation / Evals": ["eval", "benchmark", "leaderboard", "score", "评测"],
        "RAG / Retrieval": ["RAG", "retrieval", "embedding", "vector", "检索"],
        "Demos / New Apps": ["demo", "app", "showcase", "built with", "演示"],
    }

    # 已知实体（用于实体聚类）
    KNOWN_ENTITIES = [
        "claude", "gpt", "gemini", "copilot", "cursor", "codex",
        "llama", "mistral", "deepseek", "qwen", "anthropic", "openai",
        "langchain", "langgraph", "vercel", "bolt.new", "browser-use",
        "mcp", "swe-bench", "alphacode",
    ]

    def cluster_events(self, tweets: list[Tweet]) -> list[EventCluster]:
        if not tweets:
            return []

        # 阶段 1：按共享 URL 分组
        url_groups, ungrouped = self._group_by_shared_urls(tweets)

        # 阶段 2：按关键实体分组
        entity_groups, still_ungrouped = self._group_by_entities(ungrouped)

        # 合并所有分组
        all_groups = url_groups + entity_groups

        # 每个未分组的推文单独成一个 cluster
        for tweet in still_ungrouped:
            all_groups.append([tweet])

        # 构建 EventCluster 对象
        clusters = []
        for i, group in enumerate(all_groups):
            if not group:
                continue
            cluster = self._build_cluster(f"cluster_{i:03d}", group)
            clusters.append(cluster)

        # 按热度排序
        clusters.sort(key=lambda c: c.heat_score, reverse=True)
        return clusters

    def _group_by_shared_urls(self, tweets: list[Tweet]):
        """按共享外链分组"""
        url_to_tweets: dict[str, list[Tweet]] = defaultdict(list)
        ungrouped = []

        for tweet in tweets:
            matched = False
            for url in tweet.urls:
                normalized = self._normalize_url(url)
                if normalized:
                    url_to_tweets[normalized].append(tweet)
                    matched = True
            if not matched:
                ungrouped.append(tweet)

        groups = [group for group in url_to_tweets.values() if len(group) >= 1]
        return groups, ungrouped

    def _group_by_entities(self, tweets: list[Tweet]):
        """按关键实体分组"""
        entity_to_tweets: dict[str, list[Tweet]] = defaultdict(list)
        ungrouped = []

        for tweet in tweets:
            text_lower = tweet.text.lower()
            matched_entities = [
                e for e in self.KNOWN_ENTITIES if e in text_lower
            ]
            if matched_entities:
                # 用第一个匹配的实体作为 key
                primary = matched_entities[0]
                entity_to_tweets[primary].append(tweet)
            else:
                ungrouped.append(tweet)

        groups = list(entity_to_tweets.values())
        return groups, ungrouped

    def _normalize_url(self, url: str) -> str:
        """URL 标准化：去掉 query 参数和 fragment"""
        try:
            parsed = urlparse(url)
            # 忽略通用短链和社交平台自身链接
            if parsed.netloc in ("t.co", "bit.ly", "x.com", "twitter.com"):
                return ""
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
        except Exception:
            return ""

    def _build_cluster(self, cluster_id: str, tweets: list[Tweet]) -> EventCluster:
        """从一组推文构建 EventCluster"""
        # 合并文本用于主题归类
        combined_text = " ".join(t.text for t in tweets)

        # 提取关键词（简单词频）
        keywords = self._extract_keywords(combined_text)

        # 归类主题
        theme = self._assign_theme(combined_text)

        # 生成标题
        title = self._generate_title(tweets, keywords)

        # 计算热度（取组内最高）
        heat_score = max((t.heat_score for t in tweets), default=0)
        if heat_score == 0:
            # 用互动量估算
            total_engagement = sum(
                t.likes + t.reposts * 2 + t.replies + t.bookmarks * 1.5
                for t in tweets
            )
            heat_score = min(total_engagement / 1000, 10.0)

        # 提取关联 repo
        repo_names = []
        for t in tweets:
            for url in t.urls:
                match = re.search(r"github\.com/([^/]+/[^/\s?#]+)", url)
                if match:
                    repo_names.append(match.group(1))
        repo_names = list(set(repo_names))[:2]

        # 设置 cluster_id 到推文
        for t in tweets:
            t.cluster_id = cluster_id

        return EventCluster(
            id=cluster_id,
            title=title,
            theme=theme,
            heat_score=round(heat_score, 1),
            keywords=keywords[:8],
            tweet_ids=[t.id for t in tweets[:3]],  # 代表推文最多 3 条
            repo_names=repo_names,
        )

    def _assign_theme(self, text: str) -> str:
        scores = {}
        text_lower = text.lower()
        for theme, keywords in self.THEME_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text_lower)
            scores[theme] = score
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "Demos / New Apps"

    def _extract_keywords(self, text: str, top_n: int = 8) -> list[str]:
        """简单关键词提取：词频统计"""
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "can", "shall", "to", "of",
            "in", "for", "on", "with", "at", "by", "from", "as", "into",
            "through", "during", "before", "after", "and", "but", "or",
            "not", "no", "so", "if", "than", "too", "very", "just",
            "about", "up", "out", "that", "this", "it", "its", "i",
            "my", "your", "we", "they", "he", "she", "you", "me",
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
        }
        words = re.findall(r"[a-zA-Z]{3,}|[\u4e00-\u9fff]{2,}", text.lower())
        freq: dict[str, int] = {}
        for w in words:
            if w not in stop_words:
                freq[w] = freq.get(w, 0) + 1
        sorted_words = sorted(freq, key=freq.get, reverse=True)
        return sorted_words[:top_n]

    def _generate_title(self, tweets: list[Tweet], keywords: list[str]) -> str:
        """生成 cluster 标题：取第一条推文的前 50 字符 + 关键词"""
        if tweets:
            first_text = tweets[0].text[:60]
            if len(tweets[0].text) > 60:
                first_text += "..."
            return first_text
        return " / ".join(keywords[:3])
