import { useState } from 'react'
import type { Quest, MarketSignal } from '../types'

function QuestCard({ quest }: { quest: Quest }) {
  return (
    <a
      href={quest.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block bg-white rounded-lg p-4 shadow-sm border border-gray-100 hover:border-green-200 transition-colors"
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-medium bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full">
          {quest.platform}
        </span>
        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
          {quest.task_type}
        </span>
      </div>
      <h4 className="font-semibold text-sm text-gray-900 mb-1">{quest.title}</h4>
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <span className={quest.cost_tag === '0成本' ? 'text-green-600' : 'text-amber-600'}>
          {quest.cost_tag}
        </span>
        <span>|</span>
        <span>风险: {quest.risk_tag}</span>
        {quest.deadline && <span>| 截止: {quest.deadline}</span>}
      </div>
      {quest.note && <p className="text-xs text-gray-400 mt-1">{quest.note}</p>}
    </a>
  )
}

function MarketCard({ market }: { market: MarketSignal }) {
  return (
    <a
      href={market.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block bg-white rounded-lg p-4 shadow-sm border border-gray-100 hover:border-purple-200 transition-colors"
    >
      <h4 className="font-semibold text-sm text-gray-900 mb-1">{market.title}</h4>
      <p className="text-xs text-gray-600 mb-2">{market.summary}</p>
      <div className="flex items-center gap-3 text-xs text-gray-500">
        {market.volume && <span>Volume: {market.volume}</span>}
        {market.odds_change && (
          <span className={market.odds_change.startsWith('+') ? 'text-green-600' : 'text-red-600'}>
            {market.odds_change}
          </span>
        )}
      </div>
    </a>
  )
}

interface Props {
  quests: Quest[]
  markets: MarketSignal[]
}

export function Web3Section({ quests, markets }: Props) {
  const [expanded, setExpanded] = useState(false)
  const hasData = quests.length > 0 || markets.length > 0

  if (!hasData) return null

  return (
    <section className="mt-8">
      <div
        className="flex items-center justify-between cursor-pointer select-none"
        onClick={() => setExpanded(!expanded)}
      >
        <h2 className="text-xl font-bold">Web3</h2>
        <span className="text-sm text-gray-500">{expanded ? '收起' : '展开'}</span>
      </div>

      {expanded && (
        <div className="mt-4 space-y-6">
          {quests.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-600 mb-3">Quests</h3>
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                {quests.map((q, i) => <QuestCard key={i} quest={q} />)}
              </div>
            </div>
          )}
          {markets.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-600 mb-3">Polymarket</h3>
              <div className="grid gap-3 md:grid-cols-2">
                {markets.map((m, i) => <MarketCard key={i} market={m} />)}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  )
}
