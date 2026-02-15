import { useState } from 'react'
import type { BriefItem } from '../types'
import { categoryIcon } from '../utils/format'

export function DailyBrief({ items }: { items: BriefItem[] }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <section className="mb-8">
      <div
        className="flex items-center justify-between cursor-pointer select-none"
        onClick={() => setCollapsed(!collapsed)}
      >
        <h2 className="text-xl font-bold">Daily Brief</h2>
        <span className="text-sm text-gray-500">{collapsed ? '展开' : '收起'}</span>
      </div>

      {!collapsed && (
        <ol className="mt-4 space-y-3">
          {items.map((item, i) => (
            <li key={i} className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <div className="flex items-start gap-3">
                <span className="text-lg mt-0.5 shrink-0">{categoryIcon(item.category)}</span>
                <div className="min-w-0">
                  <p className="font-medium text-gray-900 leading-snug">{item.conclusion}</p>
                  <p className="text-sm text-gray-500 mt-1">{item.why_hot}</p>
                  {item.evidence_urls.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {item.evidence_urls.map((url, j) => (
                        <a
                          key={j}
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-600 hover:underline truncate max-w-[240px]"
                        >
                          {new URL(url).hostname}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
