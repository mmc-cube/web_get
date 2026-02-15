"""热度排序"""

from pipeline.models.schemas import Tweet, EventCluster


# 大厂关键词 — 命中则加权
BIG_LAB_KEYWORDS = [
    "openai", "gpt-5", "gpt-4o", "o1", "o3", "o4",
    "anthropic", "claude", "sonnet", "opus",
    "google", "gemini", "deepmind",
    "meta", "llama",
    "mistral",
    "deepseek",
    "xai", "grok",
    "sora", "dall-e",
    "sam altman", "dario amodei", "demis hassabis",
]

# 大厂官方账号
BIG_LAB_HANDLES = {
    "@openai", "@anthropicai", "@googledeepmind", "@googleai",
    "@xai", "@meta", "@metaai", "@mistralai",
    "@deepseek_ai", "@alibaba_qwen",
    "@sama", "@darioamodei",
    "@karpathy", "@swyx", "@emollick",
}


class Ranker:

    def __init__(self, w_spread=0.35, w_discuss=0.30, w_dev=0.25, w_ad_penalty=0.10):
        self.w_spread = w_spread
        self.w_discuss = w_discuss
        self.w_dev = w_dev
        self.w_ad_penalty = w_ad_penalty

    def rank_tweets(self, tweets: list[Tweet], clusters: list[EventCluster]) -> list[Tweet]:
        # 构建 cluster 作者数映射
        cluster_author_count = self._build_cluster_author_map(tweets, clusters)

        for tweet in tweets:
            tweet.heat_score = self._calc_heat(tweet, cluster_author_count)

        ranked = sorted(tweets, key=lambda t: t.heat_score, reverse=True)

        # 最低热度门槛：过滤掉太水的内容
        min_heat = 0.05
        ranked = [t for t in ranked if t.heat_score >= min_heat]

        ranked = self._cap_per_cluster(ranked, max_per_cluster=2)
        ranked = self._ensure_language_mix(ranked, min_zh=2, top_n=10)
        return ranked[:10]

    def _calc_heat(self, tweet: Tweet, cluster_author_count: dict) -> float:
        # 传播热
        spread = (tweet.likes + tweet.reposts * 2 + tweet.bookmarks * 1.5) / 1000

        # 讨论热
        authors_in_cluster = cluster_author_count.get(tweet.cluster_id, 1)
        discuss = (tweet.replies / 100) + (authors_in_cluster / 10)

        # 开发热
        dev = 1.0 if any("github.com" in u for u in tweet.urls) else 0.0

        # 广告惩罚
        ad_penalty = 1.0 if tweet.is_ad_suspect else 0.0

        heat = (
            self.w_spread * spread
            + self.w_discuss * discuss
            + self.w_dev * dev
            - self.w_ad_penalty * ad_penalty
        )

        # 大厂加权：官方账号 or 内容命中大厂关键词
        big_lab_boost = self._big_lab_boost(tweet)
        heat *= (1.0 + big_lab_boost)

        return round(max(heat, 0), 2)

    def _big_lab_boost(self, tweet: Tweet) -> float:
        """大厂内容加权倍率"""
        boost = 0.0
        handle_lower = tweet.author_handle.lower()
        text_lower = tweet.text.lower()

        # 官方账号发的 → +80%
        if handle_lower in BIG_LAB_HANDLES:
            boost += 0.8

        # 内容命中大厂关键词 → +30%
        matched = sum(1 for kw in BIG_LAB_KEYWORDS if kw in text_lower)
        if matched >= 2:
            boost += 0.5  # 命中多个关键词，更可能是重大更新
        elif matched == 1:
            boost += 0.3

        return min(boost, 1.5)  # 最多 +150%

    def _build_cluster_author_map(self, tweets: list[Tweet], clusters: list[EventCluster]) -> dict:
        """统计每个 cluster 内不同作者数"""
        cluster_tweets: dict[str, set] = {}
        for tweet in tweets:
            if tweet.cluster_id:
                cluster_tweets.setdefault(tweet.cluster_id, set()).add(tweet.author_handle)
        return {cid: len(authors) for cid, authors in cluster_tweets.items()}

    def _cap_per_cluster(self, tweets: list[Tweet], max_per_cluster: int = 2) -> list[Tweet]:
        """同 cluster 最多占 max_per_cluster 条"""
        cluster_count: dict[str, int] = {}
        result = []
        for tweet in tweets:
            cid = tweet.cluster_id or tweet.id
            cluster_count[cid] = cluster_count.get(cid, 0) + 1
            if cluster_count[cid] <= max_per_cluster:
                result.append(tweet)
        return result

    def _ensure_language_mix(self, tweets: list[Tweet], min_zh: int = 2, top_n: int = 10) -> list[Tweet]:
        """尽量保证 Top N 中中文至少 min_zh 条"""
        top = tweets[:top_n]
        rest = tweets[top_n:]

        zh_count = sum(1 for t in top if t.lang == "zh")
        if zh_count >= min_zh:
            return tweets

        # 从剩余中找中文推文补充
        zh_from_rest = [t for t in rest if t.lang == "zh"]
        needed = min_zh - zh_count

        for zh_tweet in zh_from_rest[:needed]:
            # 替换 top 中热度最低的英文推文
            en_in_top = [i for i, t in enumerate(top) if t.lang == "en"]
            if en_in_top:
                replace_idx = en_in_top[-1]  # 替换最后一个英文（热度最低）
                top[replace_idx] = zh_tweet

        return top + [t for t in rest if t not in top]
