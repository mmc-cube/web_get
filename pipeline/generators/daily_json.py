"""组装最终 daily.json 输出"""

import json
import os
from dataclasses import asdict
from datetime import datetime

from pipeline.models.schemas import (
    DailyOutput, BriefItem, Tweet, Repo, EventCluster, Quest, MarketSignal,
)


class DailyJsonGenerator:

    def generate(
        self,
        date: str,
        brief: list[BriefItem],
        top_tweets: list[Tweet],
        github_trending: list[Repo],
        github_new: list[Repo],
        clusters: list[EventCluster],
        quests: list[Quest],
        markets: list[MarketSignal],
        meta: dict,
        output_dir: str = "output",
    ) -> str:
        output = DailyOutput(
            date=date,
            generated_at=datetime.now().isoformat(),
            brief=brief,
            top_tweets=top_tweets,
            github_trending=github_trending,
            github_new=github_new,
            clusters=clusters,
            quests=quests,
            markets=markets,
            meta=meta,
        )

        # 序列化
        data = asdict(output)
        # datetime 对象转字符串
        data = self._serialize_datetimes(data)

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "daily.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return output_path

    def _serialize_datetimes(self, obj):
        if isinstance(obj, dict):
            return {k: self._serialize_datetimes(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetimes(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return obj
