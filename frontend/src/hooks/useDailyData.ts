import { useState, useEffect } from 'react'
import type { DailyData } from '../types'

const DATA_BASE_URL = './data'

export function useDailyData(date?: string) {
  const [data, setData] = useState<DailyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const targetDate = date || new Date().toISOString().slice(0, 10)

    setLoading(true)
    setError(null)

    // 先尝试指定日期，再尝试 latest.json
    fetch(`${DATA_BASE_URL}/${targetDate}.json`)
      .then(res => {
        if (!res.ok) throw new Error(`No data for ${targetDate}`)
        return res.json()
      })
      .then((d: DailyData) => setData(d))
      .catch(() => {
        // 降级：尝试 latest.json
        return fetch(`${DATA_BASE_URL}/latest.json`)
          .then(res => {
            if (!res.ok) throw new Error('No data available')
            return res.json()
          })
          .then((fallback: DailyData) => {
            setData({
              ...fallback,
              meta: {
                ...fallback.meta,
                degraded: true,
                message: `${targetDate} 无数据，显示最近存档 (${fallback.date})`,
              },
            })
          })
          .catch(() => {
            setError('无法加载数据')
          })
      })
      .finally(() => setLoading(false))
  }, [date])

  return { data, loading, error }
}
