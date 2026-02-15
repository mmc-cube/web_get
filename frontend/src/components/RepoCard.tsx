import type { Repo } from '../types'
import { formatNumber } from '../utils/format'

export function RepoCard({ repo }: { repo: Repo }) {
  return (
    <a
      href={`https://github.com/${repo.name}`}
      target="_blank"
      rel="noopener noreferrer"
      className="block bg-white rounded-lg p-4 shadow-sm border border-gray-100 hover:border-blue-200 transition-colors"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="min-w-0">
          <h4 className="font-semibold text-sm text-blue-700 truncate">{repo.name}</h4>
          <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{repo.description}</p>
        </div>
        {repo.is_new && (
          <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full shrink-0 ml-2">NEW</span>
        )}
      </div>

      {/* Metrics */}
      <div className="flex items-center gap-3 text-xs text-gray-500 mt-2">
        <span>{'\u2B50'} {formatNumber(repo.stars)}</span>
        <span className="text-green-600 font-medium">+{formatNumber(repo.stars_24h)}/24h</span>
        <span>{'\uD83C\uDF74'} {formatNumber(repo.forks)}</span>
        {repo.language && (
          <span className="bg-gray-100 px-1.5 py-0.5 rounded">{repo.language}</span>
        )}
      </div>

      {/* Topics */}
      {repo.topics.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {repo.topics.slice(0, 5).map(topic => (
            <span key={topic} className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">
              {topic}
            </span>
          ))}
        </div>
      )}

      {/* README summary */}
      {repo.readme_summary && (
        <p className="text-xs text-gray-400 mt-2 line-clamp-1">{repo.readme_summary}</p>
      )}
    </a>
  )
}
