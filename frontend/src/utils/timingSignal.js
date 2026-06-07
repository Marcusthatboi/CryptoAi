export const buildHistoryStats = (history, fallbackCurrentPrice = 0) => {
  if (!Array.isArray(history) || !history.length) {
    return {
      highPrice: Number(fallbackCurrentPrice || 0),
      lowPrice: Number(fallbackCurrentPrice || 0),
      avgPrice: Number(fallbackCurrentPrice || 0),
      priceChange: 0,
      changePercent: 0
    }
  }

  const prices = history
    .map((point) => Number(point?.price || 0))
    .filter((price) => Number.isFinite(price) && price > 0)

  if (!prices.length) {
    return {
      highPrice: Number(fallbackCurrentPrice || 0),
      lowPrice: Number(fallbackCurrentPrice || 0),
      avgPrice: Number(fallbackCurrentPrice || 0),
      priceChange: 0,
      changePercent: 0
    }
  }

  const firstPrice = prices[0]
  const latestPrice = prices[prices.length - 1]

  return {
    highPrice: Math.max(...prices),
    lowPrice: Math.min(...prices),
    avgPrice: prices.reduce((sum, price) => sum + price, 0) / prices.length,
    priceChange: latestPrice - firstPrice,
    changePercent: firstPrice > 0 ? ((latestPrice - firstPrice) / firstPrice) * 100 : 0
  }
}

export const evaluateTimingSignal = (history, stats, t) => {
  if (!Array.isArray(history) || history.length < 10) {
    return {
      action: 'HOLD',
      confidence: 'LOW',
      rationale: t('detail_timing_not_enough', 'Not enough data points yet for a reliable timing signal.')
    }
  }

  const prices = history
    .map((point) => Number(point?.price || 0))
    .filter((price) => Number.isFinite(price) && price > 0)

  if (prices.length < 10) {
    return {
      action: 'HOLD',
      confidence: 'LOW',
      rationale: t('detail_timing_incomplete_history', 'Price history is incomplete, so recommendation defaults to HOLD.')
    }
  }

  const shortWindow = prices.slice(-7)
  const longWindow = prices.slice(-Math.min(30, prices.length))
  const shortAvg = shortWindow.reduce((sum, price) => sum + price, 0) / shortWindow.length
  const longAvg = longWindow.reduce((sum, price) => sum + price, 0) / longWindow.length
  const trendDelta = ((shortAvg - longAvg) / longAvg) * 100
  const changePercent = Number(stats?.changePercent || 0)

  if (trendDelta >= 1.25 && changePercent >= 0) {
    return {
      action: 'BUY',
      confidence: trendDelta >= 3 ? 'HIGH' : 'MEDIUM',
      rationale: `${t('detail_timing_buy_prefix', 'Short-term momentum is above long-term trend')} (+${trendDelta.toFixed(2)}%), ${t('detail_timing_buy_suffix', 'which supports adding exposure.')}`
    }
  }

  if (trendDelta <= -1.25 && changePercent < 0) {
    return {
      action: 'SELL',
      confidence: trendDelta <= -3 ? 'HIGH' : 'MEDIUM',
      rationale: `${t('detail_timing_sell_prefix', 'Short-term momentum is below long-term trend')} (${trendDelta.toFixed(2)}%), ${t('detail_timing_sell_suffix', 'suggesting downside pressure.')}`
    }
  }

  return {
    action: 'HOLD',
    confidence: 'MEDIUM',
    rationale: `${t('detail_timing_hold_prefix', 'Trend is mixed')} (${trendDelta.toFixed(2)}% ${t('detail_timing_vs_long_term', 'vs long-term average')}), ${t('detail_timing_hold_suffix', 'so waiting for confirmation is safer.')}`
  }
}
