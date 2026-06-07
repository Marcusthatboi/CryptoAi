import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
  ReferenceLine,
  Dot,
  ScatterChart,
  Scatter
} from 'recharts'

export default function PriceChart({ data }) {
  if (!data || data.length === 0) {
    return <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>No data available</div>
  }

  // Format data for the chart
  const chartData = data.map((item, idx) => ({
    time: new Date(item.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
    date: new Date(item.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    price: Number(item.price),
    index: idx
  }))

  // Calculate technical indicators
  const calculateMovingAverage = (data, period) => {
    return data.map((item, idx) => {
      if (idx < period - 1) return null
      const sum = data.slice(idx - period + 1, idx + 1).reduce((acc, d) => acc + d.price, 0)
      return sum / period
    })
  }

  const calculateRSI = (data, period = 14) => {
    const rsi = []
    let gains = 0
    let losses = 0

    for (let i = 1; i < data.length; i++) {
      const change = data[i].price - data[i - 1].price
      if (i < period) {
        if (change > 0) gains += change
        else losses += Math.abs(change)
        rsi.push(null)
      } else {
        if (i === period) {
          const avgGain = gains / period
          const avgLoss = losses / period
          const rs = avgGain / avgLoss
          rsi.push(100 - 100 / (1 + rs))
        } else {
          const lastRSI = rsi[i - 1]
          const change = data[i].price - data[i - 1].price
          gains = change > 0 ? change : 0
          losses = change < 0 ? Math.abs(change) : 0
          const rs = gains / losses || 0
          rsi.push(100 - 100 / (1 + rs))
        }
      }
    }
    return rsi
  }

  // Generate buy/sell signals using support/resistance levels
  const generateSignals = () => {
    const avgPrice = chartData.reduce((sum, d) => sum + d.price, 0) / chartData.length
    const stdDev = Math.sqrt(chartData.reduce((sum, d) => sum + Math.pow(d.price - avgPrice, 2), 0) / chartData.length)
    
    // Calculate support and resistance using Bollinger Bands concept
    // Support (Buy Level) = Average Price - 1.5 * Standard Deviation
    // Resistance (Sell Level) = Average Price + 1.5 * Standard Deviation
    const buyLevel = avgPrice - (stdDev * 1.5)
    const sellLevel = avgPrice + (stdDev * 1.5)
    
    // Find actual buy and sell signal points based on these levels
    const buySignals = []
    const sellSignals = []
    
    for (let i = 1; i < chartData.length; i++) {
      const currentPrice = chartData[i].price
      const prevPrice = chartData[i - 1].price
      
      // Buy signal when price crosses below support level (good buying opportunity)
      if (prevPrice > buyLevel && currentPrice <= buyLevel) {
        buySignals.push({
          index: i,
          price: buyLevel,
          date: chartData[i].date,
          type: 'BUY'
        })
      }
      
      // Sell signal when price crosses above resistance level (good selling opportunity)
      if (prevPrice < sellLevel && currentPrice >= sellLevel) {
        sellSignals.push({
          index: i,
          price: sellLevel,
          date: chartData[i].date,
          type: 'SELL'
        })
      }
    }
    
    return { 
      buySignals, 
      sellSignals,
      buyLevel,
      sellLevel,
      avgPrice
    }
  }

  const { buySignals, sellSignals, buyLevel, sellLevel, avgPrice: calculatedAvgPrice } = generateSignals()

  // Show every nth point to avoid crowding (for large datasets)
  const displayInterval = Math.ceil(chartData.length / 20)
  const displayData = chartData.filter((_, idx) => idx % displayInterval === 0 || idx === chartData.length - 1)

  const minPrice = Math.min(...chartData.map(d => d.price))
  const maxPrice = Math.max(...chartData.map(d => d.price))
  const priceRange = maxPrice - minPrice
  const avgPrice = calculatedAvgPrice

  return (
    <div className="price-chart-container">
      <div className="chart-header-info">
        <div className="signal-legend">
          <div className="legend-item buy">
            <span className="legend-color" style={{backgroundColor: '#4CAF50'}}></span>
            <span className="legend-text">BUY Signal (Green Line)</span>
          </div>
          <div className="legend-item sell">
            <span className="legend-color" style={{backgroundColor: '#f44336'}}></span>
            <span className="legend-text">SELL Signal (Red Line)</span>
          </div>
          <div className="legend-item average">
            <span className="legend-color" style={{backgroundColor: '#FF9800'}}></span>
            <span className="legend-text">20-Day Moving Average</span>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={450}>
        <AreaChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
        >
          <defs>
            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#667eea" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#667eea" stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 0, 0, 0.1)" />
          <XAxis
            dataKey="date"
            stroke="#666"
            tick={{ fontSize: 12 }}
            interval={Math.floor(chartData.length / 8)}
          />
          <YAxis
            stroke="#666"
            tick={{ fontSize: 12 }}
            domain={['dataMin - 50', 'dataMax + 50']}
            label={{ value: 'Price ($)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle' } }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(0, 0, 0, 0.9)',
              border: '2px solid #667eea',
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
              padding: '12px'
            }}
            formatter={(value, name) => {
              if (name === 'Price') return [`$${value.toFixed(2)}`, 'Current Price']
              if (name === 'sma20') return [`$${value.toFixed(2)}`, '20-Day MA']
              return [`$${value.toFixed(2)}`, name]
            }}
            labelStyle={{ color: '#fff' }}
            contentClassName="custom-tooltip"
          />
          <Legend wrapperStyle={{ paddingTop: '20px', fontSize: '14px' }} />
          
          {/* Price Area */}
          <Area
            type="monotone"
            dataKey="price"
            stroke="#667eea"
            strokeWidth={2.5}
            fillOpacity={1}
            fill="url(#colorPrice)"
            dot={false}
            activeDot={{ r: 8 }}
            name="Price"
          />

          {/* Buy Signal Line - Green */}
          <ReferenceLine
            y={buyLevel}
            stroke="#4CAF50"
            strokeWidth={2}
            strokeDasharray="5 5"
            label={{
              value: `BUY: $${buyLevel.toFixed(2)}`,
              position: 'right',
              fill: '#4CAF50',
              fontSize: 12,
              fontWeight: 'bold'
            }}
          />

          {/* Sell Signal Line - Red */}
          <ReferenceLine
            y={sellLevel}
            stroke="#f44336"
            strokeWidth={2}
            strokeDasharray="5 5"
            label={{
              value: `SELL: $${sellLevel.toFixed(2)}`,
              position: 'right',
              fill: '#f44336',
              fontSize: 12,
              fontWeight: 'bold'
            }}
          />

          {/* Average Price Line - Orange */}
          <ReferenceLine
            y={avgPrice}
            stroke="#FF9800"
            strokeWidth={1.5}
            strokeDasharray="3 3"
            label={{
              value: `AVG: $${avgPrice.toFixed(2)}`,
              position: 'left',
              fill: '#FF9800',
              fontSize: 11,
              fontWeight: 'bold'
            }}
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Buy and Sell Signal Indicators */}
      {(buySignals.length > 0 || sellSignals.length > 0) && (
        <div className="signals-container">
          {buySignals.length > 0 && (
            <div className="signals-box buy-signals">
              <div className="signals-title">🟢 BUY Signals ({buySignals.length})</div>
              <div className="signals-list">
                {buySignals.slice(-3).map((signal, idx) => (
                  <div key={idx} className="signal-item">
                    <span className="signal-price">${signal.price.toFixed(2)}</span>
                    <span className="signal-date">{signal.date}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {sellSignals.length > 0 && (
            <div className="signals-box sell-signals">
              <div className="signals-title">🔴 SELL Signals ({sellSignals.length})</div>
              <div className="signals-list">
                {sellSignals.slice(-3).map((signal, idx) => (
                  <div key={idx} className="signal-item">
                    <span className="signal-price">${signal.price.toFixed(2)}</span>
                    <span className="signal-date">{signal.date}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="chart-statistics">
        <div className="stat-box">
          <span className="stat-name">Min Price</span>
          <span className="stat-value">${minPrice.toFixed(2)}</span>
        </div>
        <div className="stat-box">
          <span className="stat-name">Max Price</span>
          <span className="stat-value">${maxPrice.toFixed(2)}</span>
        </div>
        <div className="stat-box">
          <span className="stat-name">Avg Price</span>
          <span className="stat-value">${avgPrice.toFixed(2)}</span>
        </div>
        <div className="stat-box">
          <span className="stat-name">Range</span>
          <span className="stat-value">${priceRange.toFixed(2)}</span>
        </div>
        <div className="stat-box">
          <span className="stat-name">Buy Level</span>
          <span className="stat-value buy-level">${buyLevel.toFixed(2)}</span>
        </div>
        <div className="stat-box">
          <span className="stat-name">Sell Level</span>
          <span className="stat-value sell-level">${sellLevel.toFixed(2)}</span>
        </div>
      </div>

      <style>{`
        .price-chart-container {
          width: 100%;
        }

        .chart-header-info {
          padding: 16px;
          background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(244, 67, 54, 0.05) 100%);
          border-radius: 8px;
          margin-bottom: 20px;
          border: 1px solid rgba(102, 126, 234, 0.1);
        }

        .signal-legend {
          display: flex;
          gap: 20px;
          flex-wrap: wrap;
          font-size: 13px;
          font-weight: 500;
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .legend-color {
          width: 16px;
          height: 16px;
          border-radius: 3px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .legend-text {
          color: #333;
        }

        .signals-container {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
          margin: 24px 0;
        }

        .signals-box {
          padding: 16px;
          border-radius: 8px;
          border-left: 4px solid;
        }

        .buy-signals {
          background: rgba(76, 175, 80, 0.08);
          border-left-color: #4CAF50;
        }

        .sell-signals {
          background: rgba(244, 67, 54, 0.08);
          border-left-color: #f44336;
        }

        .signals-title {
          font-weight: 700;
          font-size: 13px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 12px;
        }

        .buy-signals .signals-title {
          color: #2e7d32;
        }

        .sell-signals .signals-title {
          color: #c62828;
        }

        .signals-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .signal-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px;
          background: rgba(255, 255, 255, 0.6);
          border-radius: 4px;
          font-size: 12px;
        }

        .signal-price {
          font-weight: 700;
          font-family: 'Monaco', 'Courier New', monospace;
        }

        .signal-date {
          color: #999;
          font-size: 11px;
        }

        .chart-statistics {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
          gap: 16px;
          margin-top: 24px;
          padding-top: 20px;
          border-top: 1px solid rgba(0, 0, 0, 0.1);
        }

        .stat-box {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 16px;
          background: rgba(102, 126, 234, 0.08);
          border-radius: 8px;
          border-left: 3px solid #667eea;
          transition: all 0.3s ease;
        }

        .stat-box:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
        }

        .stat-box.buy-level {
          border-left-color: #4CAF50;
          background: rgba(76, 175, 80, 0.08);
        }

        .stat-box.sell-level {
          border-left-color: #f44336;
          background: rgba(244, 67, 54, 0.08);
        }

        .stat-name {
          font-size: 11px;
          color: #999;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 8px;
        }

        .stat-value {
          font-size: 18px;
          font-weight: 700;
          color: #333;
          font-family: 'Monaco', 'Courier New', monospace;
        }

        .stat-value.buy-level {
          color: #2e7d32;
        }

        .stat-value.sell-level {
          color: #c62828;
        }

        .custom-tooltip {
          background: rgba(0, 0, 0, 0.9) !important;
        }

        @media (max-width: 768px) {
          .chart-statistics {
            grid-template-columns: repeat(2, 1fr);
          }

          .signals-container {
            grid-template-columns: 1fr;
          }

          .signal-legend {
            flex-direction: column;
            gap: 12px;
          }
        }
      `}</style>
    </div>
  )
}
