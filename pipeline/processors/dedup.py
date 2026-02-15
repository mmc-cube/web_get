"""去重处理器：基于 URL 和文本相似度去重"""

import hashlib
from pipeline.models.schemas import Tweet


class Deduplicator:
    """推文去重：URL 精确去重 + SimHash 近似去重"""

    SIMHASH_THRESHOLD = 3  # 海明距离阈值

    def dedup(self, tweets: list[Tweet]) -> list[Tweet]:
        seen_urls: set[frozenset] = set()
        seen_hashes: list[int] = []
        result = []

        for tweet in tweets:
            # 1. URL 去重
            tweet_urls = frozenset(tweet.urls)
            if tweet_urls and tweet_urls in seen_urls:
                continue

            # 2. 文本 SimHash 去重
            text_hash = self._simhash(tweet.text)
            is_dup = any(
                self._hamming_distance(text_hash, h) <= self.SIMHASH_THRESHOLD
                for h in seen_hashes
            )
            if is_dup:
                continue

            if tweet_urls:
                seen_urls.add(tweet_urls)
            seen_hashes.append(text_hash)
            result.append(tweet)

        return result

    def _simhash(self, text: str, hashbits: int = 64) -> int:
        """简易 SimHash 实现（不依赖外部库的降级方案）"""
        tokens = text.lower().split()
        v = [0] * hashbits

        for token in tokens:
            token_hash = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            for i in range(hashbits):
                bitmask = 1 << i
                if token_hash & bitmask:
                    v[i] += 1
                else:
                    v[i] -= 1

        fingerprint = 0
        for i in range(hashbits):
            if v[i] >= 0:
                fingerprint |= 1 << i
        return fingerprint

    def _hamming_distance(self, a: int, b: int) -> int:
        x = a ^ b
        count = 0
        while x:
            count += 1
            x &= x - 1
        return count
