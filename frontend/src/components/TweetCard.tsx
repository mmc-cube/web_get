import { useState } from 'react'
import type { Tweet } from '../types'
import { formatNumber, formatDate } from '../utils/format'
import { FeedbackButtons } from './FeedbackButtons'

export function TweetCard({ tweet }: { tweet: Tweet }) {
  const [expanded, setExpanded] = useState(false)
  const isLong = tweet.text.length > 200

  return (
    <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-semibold text-sm truncate">{tweet.author_name}</span>
          <span className="text-xs text-gray-400 shrink-0">{tweet.author_handle}</span>
          <span className={`text-xs px-1.5 py-0.5 rounded font-mono ${tweet.lang === 'zh' ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-600'}`}>
            {tweet.lang.toUpperCase()}
          </span>
        </div>
        <span className="text-xs text-gray-400 shrink-0">{formatDate(tweet.created_at)}</span>
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-1 mb-2">
        {tweet.tags.map(tag => (
          <span key={tag} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{tag}</span>
        ))}
        {tweet.is_ad_suspect && (
          <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">Ad?</span>
        )}
      </div>

      {/* Text */}
      <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
        {isLong && !expanded ? tweet.text.slice(0, 200) + '...' : tweet.text}
      </p>
      {isLong && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-blue-500 mt-1 hover:underline"
        >
          {expanded ? '收起' : '展开全文'}
        </button>
      )}

      {/* URLs */}
      {tweet.urls.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {tweet.urls.map((url, i) => (
            <a
              key={i}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-600 hover:underline truncate max-w-[200px]"
            >
              {(() => { try { return new URL(url).hostname } catch { return url.slice(0, 30) } })()}
            </a>
          ))}
        </div>
      )}

      {/* Metrics + Feedback */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-50">
        <div className="flex items-center gap-4 text-xs text-gray-400">
          <span title="Likes">{'\u2764\uFE0F'} {formatNumber(tweet.likes)}</span>
          <span title="Reposts">{'\uD83D\uDD01'} {formatNumber(tweet.reposts)}</span>
          <span title="Replies">{'\uD83D\uDCAC'} {formatNumber(tweet.replies)}</span>
          <span title="Bookmarks">{'\uD83D\uDD16'} {formatNumber(tweet.bookmarks)}</span>
          <span className="text-orange-500 font-medium" title="Heat Score">
            {tweet.heat_score.toFixed(1)}
          </span>
        </div>
        <FeedbackButtons tweetId={tweet.id} authorHandle={tweet.author_handle} />
      </div>
    </div>
  )
}
