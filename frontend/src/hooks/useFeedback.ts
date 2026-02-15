interface FeedbackRecord {
  tweet_id: string
  type: 'up' | 'down' | 'spam'
  timestamp: number
  author_handle: string
}

const STORAGE_KEY = 'ai-dashboard-feedback'

function getFeedbacks(): FeedbackRecord[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export function useFeedback() {
  const addFeedback = (tweetId: string, type: FeedbackRecord['type'], authorHandle: string) => {
    const feedbacks = getFeedbacks()
    const filtered = feedbacks.filter(f => f.tweet_id !== tweetId)
    filtered.push({
      tweet_id: tweetId,
      type,
      timestamp: Date.now(),
      author_handle: authorHandle,
    })
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered))
  }

  const getFeedback = (tweetId: string): FeedbackRecord['type'] | null => {
    const feedbacks = getFeedbacks()
    const found = feedbacks.find(f => f.tweet_id === tweetId)
    return found?.type ?? null
  }

  return { addFeedback, getFeedback }
}
