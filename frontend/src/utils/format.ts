export function formatNumber(n: number): string {
  if (n >= 10000) return (n / 1000).toFixed(1) + 'k'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}

export function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return dateStr
  }
}

export function categoryIcon(category: string): string {
  switch (category) {
    case 'ai': return '\u{1F916}'
    case 'github': return '\u2B50'
    case 'web3': return '\u{1F310}'
    default: return '\u{1F4CC}'
  }
}

export function themeColor(theme: string): string {
  const colors: Record<string, string> = {
    'Coding Agents': 'bg-purple-100 text-purple-800',
    'IDE / Copilot Tools': 'bg-blue-100 text-blue-800',
    'Workflow Automation': 'bg-green-100 text-green-800',
    'Model Releases & Updates': 'bg-red-100 text-red-800',
    'Tooling / Infra': 'bg-yellow-100 text-yellow-800',
    'Evaluation / Evals': 'bg-orange-100 text-orange-800',
    'RAG / Retrieval': 'bg-teal-100 text-teal-800',
    'Demos / New Apps': 'bg-pink-100 text-pink-800',
  }
  return colors[theme] || 'bg-gray-100 text-gray-800'
}
