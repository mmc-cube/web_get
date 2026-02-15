"""数据管道入口"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

import pytz

# 加载 .env 文件
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent.parent / ".env.example"
# 优先加载 .env，不存在则用 .env.example
real_env = env_path.parent / ".env"
load_dotenv(real_env if real_env.exists() else env_path)

# 将 pipeline 父目录加入 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.config import Config
from pipeline.collectors.twitter import TwitterCollector
from pipeline.collectors.github_trending import GitHubCollector
from pipeline.collectors.web3 import Web3Collector
from pipeline.processors.normalizer import Normalizer
from pipeline.processors.dedup import Deduplicator
from pipeline.processors.clusterer import Clusterer
from pipeline.processors.ranker import Ranker
from pipeline.generators.brief import BriefGenerator
from pipeline.generators.daily_json import DailyJsonGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def run_pipeline():
    config = Config.from_env()
    denver_tz = pytz.timezone("America/Denver")
    today = datetime.now(denver_tz)
    yesterday = today - timedelta(days=1)
    date_range = (
        yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
        yesterday.replace(hour=23, minute=59, second=59, microsecond=0),
    )
    date_str = yesterday.strftime("%Y-%m-%d")

    meta = {"degraded": False, "degraded_modules": [], "message": ""}

    # ===== 阶段 1：并行采集 =====
    logger.info("=" * 50)
    logger.info(f"Pipeline start — collecting data for {date_str}")
    logger.info("=" * 50)

    logger.info("Phase 1: Collecting data...")
    twitter_col = TwitterCollector(config)
    github_col = GitHubCollector(config)
    web3_col = Web3Collector(config)

    twitter_raw, github_raw, web3_raw = await asyncio.gather(
        twitter_col.collect(date_range=date_range),
        github_col.collect(),
        web3_col.collect(),
        return_exceptions=True,
    )

    # 处理采集失败
    if isinstance(twitter_raw, Exception):
        logger.error(f"Twitter collection failed: {twitter_raw}")
        twitter_raw = []
        meta["degraded_modules"].append("twitter")
    if isinstance(github_raw, Exception):
        logger.error(f"GitHub collection failed: {github_raw}")
        github_raw = {"trending": [], "new": []}
        meta["degraded_modules"].append("github")
    if isinstance(web3_raw, Exception):
        logger.error(f"Web3 collection failed: {web3_raw}")
        web3_raw = {"quests": [], "markets": []}
        meta["degraded_modules"].append("web3")

    if meta["degraded_modules"]:
        meta["degraded"] = True
        meta["message"] = f"部分数据源受限: {', '.join(meta['degraded_modules'])}"

    logger.info(
        f"Collected: {len(twitter_raw)} tweets, "
        f"{len(github_raw.get('trending', []))} trending repos, "
        f"{len(web3_raw.get('quests', []))} quests"
    )

    # ===== 阶段 2：标准化 =====
    logger.info("Phase 2: Normalizing...")
    normalizer = Normalizer()
    tweets = normalizer.normalize_tweets(twitter_raw)
    repos_trending = normalizer.normalize_repos(github_raw.get("trending", []))
    repos_new = normalizer.normalize_repos(github_raw.get("new", []))
    quests = normalizer.normalize_quests(web3_raw.get("quests", []))
    markets = normalizer.normalize_markets(web3_raw.get("markets", []))

    logger.info(f"Normalized: {len(tweets)} tweets, {len(repos_trending)} repos")

    # ===== 阶段 3：去重 + 聚类 =====
    logger.info("Phase 3: Dedup + Clustering...")
    dedup = Deduplicator()
    tweets = dedup.dedup(tweets)
    logger.info(f"After dedup: {len(tweets)} tweets")

    clusterer = Clusterer()
    clusters = clusterer.cluster_events(tweets)
    logger.info(f"Clusters: {len(clusters)}")

    # ===== 阶段 4：排序 =====
    logger.info("Phase 4: Ranking...")
    ranker = Ranker(
        w_spread=config.w_spread,
        w_discuss=config.w_discuss,
        w_dev=config.w_dev,
        w_ad_penalty=config.w_ad_penalty,
    )
    top_tweets = ranker.rank_tweets(tweets, clusters)
    logger.info(f"Top tweets: {len(top_tweets)}")

    # ===== 阶段 5：生成晨报 =====
    logger.info("Phase 5: Generating brief...")
    brief_gen = BriefGenerator(config.dashscope_api_key)
    brief = brief_gen.generate(clusters, top_tweets, repos_trending, quests)
    logger.info(f"Brief items: {len(brief)}")

    # ===== 输出 =====
    logger.info("Phase 6: Generating daily.json...")
    generator = DailyJsonGenerator()
    output_path = generator.generate(
        date=date_str,
        brief=brief,
        top_tweets=top_tweets,
        github_trending=repos_trending,
        github_new=repos_new,
        clusters=clusters,
        quests=quests,
        markets=markets,
        meta=meta,
        output_dir=config.output_dir,
    )

    logger.info(f"Output: {output_path}")
    logger.info("=" * 50)
    logger.info("Pipeline completed!")
    logger.info("=" * 50)


def main():
    asyncio.run(run_pipeline())


if __name__ == "__main__":
    main()
