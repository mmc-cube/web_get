"""全局配置"""

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    dashscope_api_key: str = ""
    github_token: str = ""
    twitter_scraper_key: str = ""

    # X 采集关键词
    twitter_keywords: dict = field(default_factory=lambda: {
        "ai_coding": [
            "claude code", "cursor", "copilot", "agentic coding",
            "coding agent", "dev workflow", "prompt-to-code",
            "tool calling", "MCP", "codegen", "terminal agent",
            "vibe coding", "AI IDE",
        ],
        "model_releases": [
            "new model", "model update", "released", "launched",
            "anthropic", "openai", "gemini", "llama", "mistral",
            "deepseek", "qwen",
        ],
        "big_labs": [
            "GPT-5", "GPT-4o", "o1", "o3", "o4-mini",
            "Claude 4", "Claude Opus", "Claude Sonnet",
            "Gemini 2", "Gemini Ultra", "Gemini Pro",
            "Llama 4", "Grok", "xAI",
            "Sora", "DALL-E", "Midjourney V7",
            "Sam Altman", "Dario Amodei", "Demis Hassabis",
        ],
        "tools_infra": [
            "eval", "RAG", "vector database", "fine-tuning",
            "inference", "deployment",
        ],
    })

    # 大厂官方账号（来自这些账号的内容自动加权）
    big_lab_handles: list = field(default_factory=lambda: [
        "@OpenAI", "@AnthropicAI", "@GoogleDeepMind", "@GoogleAI",
        "@xaboratory", "@Meta", "@MetaAI", "@MistralAI",
        "@deepaboratory", "@Alibaba_Qwen",
        "@sama", "@DarioAmodei", "@demaboratory",
        "@kaboratory", "@swyx", "@emollick",
    ])

    # Web3 关键词
    web3_keywords: list = field(default_factory=lambda: [
        "airdrop", "points", "testnet", "quest",
        "galxe", "zealy", "layer3", "polymarket",
    ])

    # 排序权重
    w_spread: float = 0.35
    w_discuss: float = 0.30
    w_dev: float = 0.25
    w_ad_penalty: float = 0.10

    # 主题列表
    themes: list = field(default_factory=lambda: [
        "Coding Agents",
        "IDE / Copilot Tools",
        "Workflow Automation",
        "Model Releases & Updates",
        "Tooling / Infra",
        "Evaluation / Evals",
        "RAG / Retrieval",
        "Demos / New Apps",
    ])

    # 输出路径
    output_dir: str = "output"
    data_dir: str = "data"

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", ""),
            github_token=os.getenv("GITHUB_TOKEN", ""),
            twitter_scraper_key=os.getenv("TWITTER_SCRAPER_KEY", ""),
            output_dir=os.getenv("OUTPUT_DIR", "output"),
            data_dir=os.getenv("DATA_DIR", "data"),
        )
