import type { DailyData } from '../types'

export function DegradeBanner({ meta }: { meta: DailyData['meta'] }) {
  if (!meta?.degraded) return null

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-6 text-sm text-amber-800">
      {meta.message || '部分数据源受限，已启用降级模式'}
      {meta.degraded_modules && meta.degraded_modules.length > 0 && (
        <span className="ml-2 text-amber-600">
          (受影响: {meta.degraded_modules.join(', ')})
        </span>
      )}
    </div>
  )
}
