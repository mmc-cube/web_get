import { useState } from 'react'
import { useDailyData } from './hooks/useDailyData'
import {
  Zap, GitBranch, Globe, Star, ArrowUp, ExternalLink,
  ChevronLeft, ChevronRight, Loader2, AlertCircle,
  Flame, MessageSquare, Heart, Bookmark, Repeat2,
  TrendingUp, Clock,
} from 'lucide-react'
import type { BriefItem, Tweet, Repo, EventCluster } from './types'

// ========== 分类图标 & 颜色 ==========
const categoryConfig = {
  ai: { icon: Zap, color: 'text-blue-500', bg: 'bg-blue-50', label: 'AI' },
  github: { icon: GitBranch, color: 'text-purple-500', bg: 'bg-purple-50', label: 'GitHub' },
  web3: { icon: Globe, color: 'text-green-500', bg: 'bg-green-50', label: 'Web3' },
}

// ========== 晨报条目 ==========
function BriefRow({ item, index }: { item: BriefItem; index: number }) {
  const cat = categoryConfig[item.category] || categoryConfig.ai
  const Icon = cat.icon
  const mainUrl = item.evidence_urls[0] || null
  return (
    <div className="flex items-start gap-3 py-2.5 px-3 rounded-lg hover:bg-gray-50 transition-colors group">
      <span className="flex-shrink-0 w-5 h-5 rounded-full bg-gray-100 text-[11px] font-bold text-gray-500 flex items-center justify-center mt-0.5">
        {index + 1}
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 mb-0.5">
          <span className={`inline-flex items-center gap-0.5 text-[10px] font-medium px-1.5 py-0.5 rounded ${cat.bg} ${cat.color}`}>
            <Icon size={10} />
            {cat.label}
          </span>
        </div>
        {mainUrl ? (
          <a href={mainUrl} target="_blank" rel="noreferrer"
            className="text-sm text-gray-900 leading-snug hover:text-blue-600 hover:underline cursor-pointer block">
            {item.conclusion}
            <ExternalLink size={11} className="inline ml-1 opacity-0 group-hover:opacity-50" />
          </a>
        ) : (
          <p className="text-sm text-gray-900 leading-snug">{item.conclusion}</p>
        )}
        <p className="text-xs text-gray-400 mt-0.5">{item.why_hot}</p>
        {item.evidence_urls.length > 1 && (
          <div className="flex gap-2 mt-1">
            {item.evidence_urls.slice(1, 3).map((url, i) => {
              let host = ''
              try { host = new URL(url).hostname.replace('www.', '') } catch { host = 'link' }
              return (
                <a key={i} href={url} target="_blank" rel="noreferrer"
                  className="text-[10px] text-blue-400 hover:text-blue-600 flex items-center gap-0.5 truncate max-w-[180px]">
                  <ExternalLink size={9} />
                  {host}
                </a>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

// ========== 热点条目 ==========
function TweetRow({ tweet, index }: { tweet: Tweet; index: number }) {
  // 优先用 urls 里的第一个链接，否则用 HN 链接
  const mainUrl = tweet.urls?.[0] || null
  return (
    <div className="flex items-start gap-3 py-2 px-3 rounded-lg hover:bg-gray-50 transition-colors group">
      <span className="flex-shrink-0 w-5 h-5 rounded-full bg-orange-50 text-[11px] font-bold text-orange-500 flex items-center justify-center mt-0.5">
        {index + 1}
      </span>
      <div className="flex-1 min-w-0">
        {mainUrl ? (
          <a href={mainUrl} target="_blank" rel="noreferrer"
            className="text-sm text-gray-900 leading-snug line-clamp-2 hover:text-blue-600 hover:underline cursor-pointer block">
            {tweet.text}
            <ExternalLink size={11} className="inline ml-1 opacity-0 group-hover:opacity-50" />
          </a>
        ) : (
          <p className="text-sm text-gray-900 leading-snug line-clamp-2">{tweet.text}</p>
        )}
        <div className="flex items-center gap-3 mt-1 text-[11px] text-gray-400">
          <span className="font-medium text-gray-500">{tweet.author_handle}</span>
          <span className="flex items-center gap-0.5"><Heart size={10} />{tweet.likes}</span>
          <span className="flex items-center gap-0.5"><Repeat2 size={10} />{tweet.reposts}</span>
          <span className="flex items-center gap-0.5"><MessageSquare size={10} />{tweet.replies}</span>
          <span className="flex items-center gap-0.5"><Bookmark size={10} />{tweet.bookmarks}</span>
          {tweet.heat_score > 0 && (
            <span className="flex items-center gap-0.5 text-orange-400"><Flame size={10} />{tweet.heat_score.toFixed(1)}</span>
          )}
        </div>
      </div>
    </div>
  )
}

// ========== Repo 条目 ==========
function RepoRow({ repo, index }: { repo: Repo; index: number }) {
  const trendBadge = () => {
    const days = repo.trending_days || 1
    const status = repo.trend_status || ''
    if (days > 1 && status === 'rising') {
      return <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-orange-100 text-orange-600 flex items-center gap-0.5"><TrendingUp size={9} />{days}天↑</span>
    }
    if (days > 1 && status === 'steady') {
      return <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-blue-50 text-blue-500 flex items-center gap-0.5"><Clock size={9} />{days}天</span>
    }
    if (status === 'new') {
      return <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-green-100 text-green-600">NEW</span>
    }
    return null
  }
  return (
    <div className="flex items-start gap-3 py-2 px-3 rounded-lg hover:bg-gray-50 transition-colors">
      <span className="flex-shrink-0 w-5 h-5 rounded-full bg-purple-50 text-[11px] font-bold text-purple-500 flex items-center justify-center mt-0.5">
        {index + 1}
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <a href={`https://github.com/${repo.name}`} target="_blank" rel="noreferrer"
            className="text-sm font-medium text-blue-600 hover:underline truncate">
            {repo.name}
          </a>
          {trendBadge()}
          {repo.language && (
            <span className="text-[10px] text-gray-400">{repo.language}</span>
          )}
        </div>
        <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{repo.description}</p>
        <div className="flex items-center gap-3 mt-1 text-[11px] text-gray-400">
          <span className="flex items-center gap-0.5"><Star size={10} className="text-yellow-400" />{repo.stars.toLocaleString()}</span>
          {repo.stars_24h > 0 && (
            <span className="flex items-center gap-0.5 text-green-500"><ArrowUp size={10} />+{repo.stars_24h}</span>
          )}
          {repo.topics.slice(0, 3).map(t => (
            <span key={t} className="px-1.5 py-0.5 rounded bg-gray-100 text-[10px]">{t}</span>
          ))}
        </div>
      </div>
    </div>
  )
}

// ========== 聚类标签 ==========
function ClusterTag({ cluster }: { cluster: EventCluster }) {
  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white border border-gray-100 hover:border-blue-200 hover:bg-blue-50/30 transition-colors cursor-default text-xs">
      <span className="font-medium text-gray-700">{cluster.title}</span>
      <span className="text-[10px] text-gray-400">{cluster.theme}</span>
      {cluster.heat_score > 0 && (
        <span className="text-[10px] text-orange-400 flex items-center gap-0.5">
          <Flame size={9} />{cluster.heat_score.toFixed(0)}
        </span>
      )}
    </div>
  )
}

// ========== 主应用 ==========
export default function App() {
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().slice(0, 10))
  const { data, loading, error } = useDailyData(selectedDate)

  const prevDay = () => {
    const d = new Date(selectedDate)
    d.setDate(d.getDate() - 1)
    setSelectedDate(d.toISOString().slice(0, 10))
  }
  const nextDay = () => {
    const d = new Date(selectedDate)
    d.setDate(d.getDate() + 1)
    const today = new Date().toISOString().slice(0, 10)
    if (d.toISOString().slice(0, 10) <= today) {
      setSelectedDate(d.toISOString().slice(0, 10))
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white/90 backdrop-blur border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 py-2.5 flex items-center justify-between">
          <h1 className="text-base font-bold text-gray-900 flex items-center gap-2">
            <Zap size={18} className="text-blue-500" />
            AI Daily
          </h1>
          <div className="flex items-center gap-1">
            <button onClick={prevDay} className="p-1.5 rounded hover:bg-gray-100 text-gray-400">
              <ChevronLeft size={16} />
            </button>
            <input
              type="date"
              value={selectedDate}
              max={new Date().toISOString().slice(0, 10)}
              onChange={e => setSelectedDate(e.target.value)}
              className="text-sm text-gray-600 border border-gray-200 rounded px-2 py-1"
            />
            <button onClick={nextDay} className="p-1.5 rounded hover:bg-gray-100 text-gray-400">
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-4">
        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="animate-spin text-blue-500" size={28} />
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="flex flex-col items-center justify-center py-20 text-gray-400">
            <AlertCircle size={32} className="mb-2" />
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Content: 三栏布局 */}
        {data && !loading && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">

            {/* 左栏：晨报速览 */}
            <div className="lg:col-span-4">
              <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
                <div className="px-4 py-2.5 border-b border-gray-50 flex items-center justify-between">
                  <h2 className="text-sm font-bold text-gray-800">晨报速览</h2>
                  <span className="text-[10px] text-gray-400">{data.brief.length} 条</span>
                </div>
                <div className="divide-y divide-gray-50">
                  {data.brief.map((item, i) => (
                    <BriefRow key={i} item={item} index={i} />
                  ))}
                </div>
              </div>
            </div>

            {/* 中栏：AI 热点 + 聚类 */}
            <div className="lg:col-span-4 space-y-4">
              {/* AI 热点 */}
              {data.top_tweets.length > 0 && (
                <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
                  <div className="px-4 py-2.5 border-b border-gray-50 flex items-center justify-between">
                    <h2 className="text-sm font-bold text-gray-800">AI 热点</h2>
                    <span className="text-[10px] text-gray-400">Top {data.top_tweets.length}</span>
                  </div>
                  <div className="divide-y divide-gray-50">
                    {data.top_tweets.map((tweet, i) => (
                      <TweetRow key={tweet.id} tweet={tweet} index={i} />
                    ))}
                  </div>
                </div>
              )}

              {/* 话题聚类 */}
              {data.clusters.length > 0 && (
                <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
                  <div className="px-4 py-2.5 border-b border-gray-50">
                    <h2 className="text-sm font-bold text-gray-800">话题聚类</h2>
                  </div>
                  <div className="p-3 flex flex-wrap gap-2">
                    {data.clusters.slice(0, 20).map(cluster => (
                      <ClusterTag key={cluster.id} cluster={cluster} />
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* 右栏：GitHub Trending */}
            <div className="lg:col-span-4">
              {(data.github_trending.length > 0 || data.github_new.length > 0) && (
                <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
                  <div className="px-4 py-2.5 border-b border-gray-50 flex items-center justify-between">
                    <h2 className="text-sm font-bold text-gray-800">GitHub Trending</h2>
                    <span className="text-[10px] text-gray-400">{data.github_trending.length + data.github_new.length} repos</span>
                  </div>
                  <div className="divide-y divide-gray-50">
                    {[...data.github_trending, ...data.github_new].map((repo, i) => (
                      <RepoRow key={repo.name} repo={repo} index={i} />
                    ))}
                  </div>
                </div>
              )}
            </div>

          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-100 mt-8 py-4 text-center text-[11px] text-gray-300">
        AI Daily &middot; {data?.generated_at ? new Date(data.generated_at).toLocaleString('zh-CN') : '—'}
      </footer>
    </div>
  )
}
