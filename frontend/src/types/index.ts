export interface Tweet {
  id: string
  author_name: string
  author_handle: string
  text: string
  lang: 'en' | 'zh'
  created_at: string
  likes: number
  reposts: number
  replies: number
  bookmarks: number
  urls: string[]
  tags: string[]
  is_ad_suspect: boolean
  cluster_id?: string
  heat_score: number
}

export interface Repo {
  name: string
  owner: string
  description: string
  stars: number
  forks: number
  stars_24h: number
  created_at: string
  language: string
  topics: string[]
  readme_summary: string
  relevance_tags: string[]
  is_new: boolean
  trending_days: number
  trend_status: 'new' | 'rising' | 'steady' | 'declining' | ''
  watchers: number
  open_issues: number
}

export interface EventCluster {
  id: string
  title: string
  theme: string
  heat_score: number
  keywords: string[]
  tweet_ids: string[]
  repo_names: string[]
}

export interface Quest {
  platform: string
  title: string
  task_type: string
  cost_tag: string
  risk_tag: string
  deadline?: string
  url: string
  note: string
}

export interface MarketSignal {
  title: string
  summary: string
  volume?: string
  odds_change?: string
  url: string
}

export interface BriefItem {
  conclusion: string
  why_hot: string
  evidence_urls: string[]
  category: 'ai' | 'github' | 'web3'
}

export interface DailyData {
  date: string
  generated_at: string
  brief: BriefItem[]
  top_tweets: Tweet[]
  github_trending: Repo[]
  github_new: Repo[]
  clusters: EventCluster[]
  quests: Quest[]
  markets: MarketSignal[]
  meta: {
    degraded?: boolean
    degraded_modules?: string[]
    message?: string
  }
}
