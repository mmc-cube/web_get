import { useState } from 'react'
import { useFeedback } from '../hooks/useFeedback'

interface Props {
  tweetId: string
  authorHandle: string
}

export function FeedbackButtons({ tweetId, authorHandle }: Props) {
  const { addFeedback, getFeedback } = useFeedback()
  const [current, setCurrent] = useState<string | null>(() => getFeedback(tweetId))

  const handle = (type: 'up' | 'down' | 'spam') => {
    addFeedback(tweetId, type, authorHandle)
    setCurrent(type)
  }

  const btnClass = (type: string) =>
    `px-2 py-1 rounded text-xs transition-colors ${
      current === type
        ? 'bg-blue-100 text-blue-700 font-medium'
        : 'hover:bg-gray-100 text-gray-400'
    }`

  return (
    <div className="flex items-center gap-1">
      <button onClick={() => handle('up')} className={btnClass('up')} title="有价值">
        {'\uD83D\uDC4D'}
      </button>
      <button onClick={() => handle('down')} className={btnClass('down')} title="没价值">
        {'\uD83D\uDC4E'}
      </button>
      <button onClick={() => handle('spam')} className={btnClass('spam')} title="喊单/广告">
        {'\uD83D\uDEAB'}
      </button>
    </div>
  )
}
