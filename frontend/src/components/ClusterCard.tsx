import type { EventCluster } from '../types'
import { themeColor } from '../utils/format'

export function ClusterCard({ cluster }: { cluster: EventCluster }) {
  return (
    <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
      <div className="flex items-start justify-between mb-2">
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${themeColor(cluster.theme)}`}>
          {cluster.theme}
        </span>
        <span className="text-sm font-bold text-orange-500" title="Heat Score">
          {cluster.heat_score.toFixed(1)}
        </span>
      </div>

      <h4 className="font-semibold text-sm text-gray-900 leading-snug mb-2">{cluster.title}</h4>

      {/* Keywords */}
      <div className="flex flex-wrap gap-1 mb-2">
        {cluster.keywords.map(kw => (
          <span key={kw} className="text-xs bg-gray-50 text-gray-500 px-1.5 py-0.5 rounded">
            {kw}
          </span>
        ))}
      </div>

      {/* Related repos */}
      {cluster.repo_names.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {cluster.repo_names.map(repo => (
            <a
              key={repo}
              href={`https://github.com/${repo}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-600 hover:underline"
            >
              {repo}
            </a>
          ))}
        </div>
      )}

      <div className="text-xs text-gray-400 mt-2">
        {cluster.tweet_ids.length} related tweets
      </div>
    </div>
  )
}
