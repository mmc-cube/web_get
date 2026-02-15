interface Props {
  currentDate: string
  onChange: (date: string) => void
}

export function DatePicker({ currentDate, onChange }: Props) {
  // 生成最近 30 天的日期列表
  const dates: string[] = []
  for (let i = 0; i < 30; i++) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    dates.push(d.toISOString().slice(0, 10))
  }

  return (
    <select
      value={currentDate}
      onChange={e => onChange(e.target.value)}
      className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
    >
      {dates.map(d => (
        <option key={d} value={d}>{d}</option>
      ))}
    </select>
  )
}
