import React, { useState, useEffect } from 'react'
import { cryptoAPI } from '../utils/api'
import { useWebSocket } from '../hooks/useWebSocket'
import './TrendChart.css'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'

export default function TrendChart({ cryptoId }) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const { priceUpdates } = useWebSocket()

  useEffect(() => {
    fetchHistory()
    // Auto-refresh every 60 seconds for fresh data
    const interval = setInterval(() => fetchHistory(), 60000)
    return () => clearInterval(interval)
  }, [cryptoId])

  // Update chart with live WebSocket prices
  useEffect(() => {
    if (priceUpdates && priceUpdates.length > 0) {
      setData((prevData) => {
        if (prevData.length === 0) return prevData
        
        const updated = [...prevData]
        const lastIndex = updated.length - 1
        
        // Update latest price point with live data
        if (updated[lastIndex]) {
          updated[lastIndex] = {
            ...updated[lastIndex],
            price: priceUpdates[0]?.price || updated[lastIndex].price,
            timestamp: new Date().toLocaleTimeString(),
            isLive: true
          }
        }
        
        return updated
      })
    }
  }, [priceUpdates])

  const fetchHistory = async () => {
    try {
      setLoading(true)
      const response = await cryptoAPI.getHistory(cryptoId, 100)
      const chartData = response.data.records.map((record, idx) => ({
        timestamp: new Date(record.timestamp).toLocaleTimeString(),
        price: record.price,
        time: new Date(record.timestamp),
        index: idx,
        isLive: idx === response.data.records.length - 1
      }))
      setData(chartData)
      setError(null)
    } catch (err) {
      setError('Failed to fetch history')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="trend-chart loading">Loading chart...</div>
  if (error) return <div className="trend-chart error">{error}</div>
  if (data.length === 0) return <div className="trend-chart">No data available</div>

  return (
    <div className="trend-chart">
      <h3>{cryptoId.toUpperCase()} Price History</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="timestamp" 
            tick={{ fontSize: 12 }}
          />
          <YAxis 
            tickFormatter={(value) => `$${value.toLocaleString()}`}
            tick={{ fontSize: 12 }}
          />
          <Tooltip 
            formatter={(value) => `$${value.toLocaleString('en-US', { 
              minimumFractionDigits: 2, 
              maximumFractionDigits: 2 
            })}`}
          />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="price" 
            stroke="#667eea" 
            dot={false}
            strokeWidth={2}
            isAnimationActive={true}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
