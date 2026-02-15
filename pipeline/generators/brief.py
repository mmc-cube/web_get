"""晨报生成器：LLM 优先（Qwen）+ 模板降级"""

import json
import logging

from pipeline.models.schemas import BriefItem, EventCluster, Tweet, Repo, Quest

logger = logging.getLogger(__name__)


class BriefGenerator:

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.client = None
        if api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                )
            except ImportError:
                logger.warning("openai package not installed, using template mode")

    def generate(
        self,
        clusters: list[EventCluster],
        top_tweets: list[Tweet],
        repos: list[Repo],
        quests: list[Quest],
    ) -> list[BriefItem]:
        if self.client:
            try:
                return self._generate_with_llm(clusters, top_tweets, repos, quests)
            except Exception as e:
                logger.warning(f"LLM brief generation failed: {e}")

        return self._generate_with_template(clusters, top_tweets, repos, quests)

    def _generate_with_llm(self, clusters, top_tweets, repos, quests) -> list[BriefItem]:
        context = self._build_context(clusters, top_tweets, repos, quests)

        response = self.client.chat.completions.create(
            model="qwen-max",
            messages=[{
                "role": "user",
                "content": f"""你是一位资深 AI 行业分析师，基于以下今日数据生成 10-12 条高质量晨报要点。

要求：
- AI 编程热点 5-6 条（关注大厂动态、模型发布、工具更新等事件级内容）
- GitHub Trending 2-3 条（关注连续在榜项目、增长加速项目、新项目爆发）
- Web3 1-2 条（可行动机会/情报）
- 每条包含：
  - conclusion: 一句话结论（中文，≤140字，要有信息量，不要泛泛而谈）
  - why_hot: 为什么重要（1句话，点明趋势意义或影响）
  - evidence_urls: 证据链接数组（1-3个）
  - category: "ai" 或 "github" 或 "web3"
- 优先报道：大厂官方动态 > 重大模型发布 > 连续多天热门项目 > 增长加速项目
- 对于连续在榜的 GitHub 项目，请指出连续在榜天数和增长趋势
- 直接输出 JSON 数组，不要其他文字

数据：
{context}""",
            }],
            max_tokens=3000,
        )

        text = response.choices[0].message.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        items_data = json.loads(text)
        return [
            BriefItem(
                conclusion=item["conclusion"],
                why_hot=item["why_hot"],
                evidence_urls=item.get("evidence_urls", []),
                category=item.get("category", "ai"),
            )
            for item in items_data
        ]

    def _generate_with_template(self, clusters, top_tweets, repos, quests) -> list[BriefItem]:
        """降级：模板化生成"""
        items = []

        # AI 事件 5-6 条
        for cluster in clusters[:6]:
            evidence = []
            for tweet in top_tweets:
                if tweet.cluster_id == cluster.id and tweet.urls:
                    evidence.extend(tweet.urls[:2])
            if not evidence and cluster.repo_names:
                evidence = [f"https://github.com/{r}" for r in cluster.repo_names]

            items.append(BriefItem(
                conclusion=cluster.title,
                why_hot=f"热度 {cluster.heat_score}，{len(cluster.tweet_ids)} 条相关讨论，主题: {cluster.theme}",
                evidence_urls=evidence[:3],
                category="ai",
            ))

        # GitHub 2-3 条（优先连续在榜 + 增长加速）
        sorted_repos = sorted(repos, key=lambda r: (r.trending_days, r.stars_24h), reverse=True)
        for repo in sorted_repos[:3]:
            trend_label = {
                "new": "新项目爆发",
                "rising": f"连续在榜{repo.trending_days}天，增长加速",
                "steady": f"连续在榜{repo.trending_days}天，稳定增长",
                "declining": "热度回落中",
            }.get(repo.trend_status, "")

            items.append(BriefItem(
                conclusion=f"{repo.name} 24h +{repo.stars_24h} stars — {repo.description[:60]}",
                why_hot=f"{trend_label}，语言: {repo.language}，总 stars: {repo.stars:,}",
                evidence_urls=[f"https://github.com/{repo.name}"],
                category="github",
            ))

        # Web3 1-2 条
        for quest in quests[:2]:
            items.append(BriefItem(
                conclusion=f"[{quest.platform}] {quest.title}（{quest.cost_tag}）",
                why_hot=quest.note or f"{quest.task_type}，风险{quest.risk_tag}",
                evidence_urls=[quest.url] if quest.url else [],
                category="web3",
            ))

        return items[:12]

    def _build_context(self, clusters, top_tweets, repos, quests) -> str:
        """构建 LLM 输入上下文（含趋势分析维度）"""
        parts = []

        parts.append("## Top Clusters:")
        for c in clusters[:8]:
            parts.append(f"- [{c.theme}] {c.title} (热度: {c.heat_score})")

        parts.append("\n## Top Tweets:")
        for t in top_tweets[:10]:
            tags_str = ", ".join(t.tags) if t.tags else ""
            parts.append(f"- {t.author_handle}: {t.text[:150]} [{tags_str}]")
            if t.urls:
                parts.append(f"  链接: {', '.join(t.urls[:2])}")

        parts.append("\n## GitHub Trending:")
        for r in repos[:8]:
            trend_info = f"连续在榜{r.trending_days}天" if r.trending_days > 1 else "今日新上榜"
            status_label = {"rising": "↑加速", "steady": "→稳定", "declining": "↓减速", "new": "★新"}.get(r.trend_status, "")
            parts.append(
                f"- {r.name} (+{r.stars_24h} stars, 总{r.stars:,}) "
                f"[{trend_info} {status_label}] "
                f"{r.language} | {r.description[:80]}"
            )
            if r.topics:
                parts.append(f"  标签: {', '.join(r.topics[:5])}")

        parts.append("\n## Web3 Quests:")
        for q in quests[:3]:
            parts.append(f"- [{q.platform}] {q.title}: {q.note}")

        return "\n".join(parts)
