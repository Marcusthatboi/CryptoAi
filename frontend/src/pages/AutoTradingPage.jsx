import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/AutoTradingPage.css';

// Use localhost:8002 for local dev, otherwise use VITE_API_BASE_URL or default to localhost:8002
const isLocalDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
const API_BASE = isLocalDev ? 'http://localhost:8002' : (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002');

export default function AutoTradingPage() {
  const [warnings, setWarnings] = useState([]);
  const [showWarnings, setShowWarnings] = useState(true);
  const [allAcknowledged, setAllAcknowledged] = useState(false);
  const [riskAcknowledged, setRiskAcknowledged] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('warnings'); // warnings, trade, active
  const [activeTrades, setActiveTrades] = useState([]);
  const [loadingTrades, setLoadingTrades] = useState(false);
  const [tradeData, setTradeData] = useState({
    symbol: 'BTC/USD',
    action: 'BUY',
    quantity: 1,
    max_price: null,
    min_price: null,
    stop_loss: null,
    take_profit: null,
  });
  const [riskAssessment, setRiskAssessment] = useState(null);
  const [previewData, setPreviewData] = useState(null);

  useEffect(() => {
    checkSubscription();
    if (subscription?.tier === 'premium') {
      loadWarnings();
    }
  }, []);

  useEffect(() => {
    // Load active trades when switching to the active trades tab
    if (activeTab === 'active' && subscription?.tier === 'premium') {
      fetchActiveTrades();
    }
  }, [activeTab]);

  const checkSubscription = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE}/api/subscription/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSubscription(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error checking subscription:', error);
      setLoading(false);
    }
  };

  const loadWarnings = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/auto-trading/warnings`);
      setWarnings(response.data.warnings || []);
    } catch (error) {
      console.error('Error loading warnings:', error);
    }
  };

  const fetchActiveTrades = async () => {
    setLoadingTrades(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE}/api/auto-trading/user/active-trades`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setActiveTrades(response.data.active_trades || []);
    } catch (error) {
      console.error('Error fetching active trades:', error);
      setActiveTrades([]);
    } finally {
      setLoadingTrades(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setTradeData(prev => ({
      ...prev,
      [name]: isNaN(value) ? value : parseFloat(value)
    }));
  };

  const assessRisk = async () => {
    if (!tradeData.symbol || !tradeData.quantity) {
      alert('Please fill in symbol and quantity');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_BASE}/api/auto-trading/assess-risk`, {
        symbol: tradeData.symbol,
        action: tradeData.action,
        quantity: tradeData.quantity,
        current_price: 50000, // Would come from real market data
        portfolio_value: 100000, // Would come from user portfolio
        market_volatility: 0.05
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRiskAssessment(response.data.risk_assessment);
    } catch (error) {
      console.error('Error assessing risk:', error);
      alert('Error assessing risk');
    } finally {
      setLoading(false);
    }
  };

  const previewTrade = async () => {
    if (!riskAcknowledged || !termsAccepted) {
      alert('You must acknowledge all risks and accept terms');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_BASE}/api/auto-trading/preview`, {
        symbol: tradeData.symbol,
        action: tradeData.action,
        quantity: tradeData.quantity,
        stop_loss: tradeData.stop_loss,
        take_profit: tradeData.take_profit,
        acknowledgement_risks_understood: riskAcknowledged,
        acknowledgement_terms_accepted: termsAccepted
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPreviewData(response.data);
    } catch (error) {
      console.error('Error previewing trade:', error);
      alert(error.response?.data?.detail || 'Error previewing trade');
    } finally {
      setLoading(false);
    }
  };

  const executeTrade = async () => {
    if (!window.confirm(
      '⚠️ ARE YOU ABSOLUTELY SURE?\n\n' +
      'This will EXECUTE a real trade with REAL MONEY.\n\n' +
      'You could lose your entire investment in seconds.\n\n' +
      'Click OK only if you are 100% certain.'
    )) {
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_BASE}/api/auto-trading/execute`, {
        symbol: tradeData.symbol,
        action: tradeData.action,
        quantity: tradeData.quantity,
        stop_loss: tradeData.stop_loss,
        take_profit: tradeData.take_profit,
        acknowledgement_risks_understood: riskAcknowledged,
        acknowledgement_terms_accepted: termsAccepted
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      alert('✅ Trade executed! Monitor your position immediately.');
      console.log('Trade response:', response.data);
    } catch (error) {
      console.error('Error executing trade:', error);
      alert(error.response?.data?.detail || 'Error executing trade');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="auto-trading-container"><p>Loading...</p></div>;
  }

  if (subscription?.tier !== 'premium') {
    return (
      <div className="auto-trading-container">
        <header className="auto-trading-header">
          <h1>🤖 AI Auto Trading</h1>
          <p className="critical-warning">⚠️ PREMIUM FEATURE ⚠️</p>
        </header>

        <div className="premium-upgrade-prompt">
          <div className="upgrade-card">
            <h2>🔒 Premium Feature</h2>
            <p>Auto Trading is an exclusive Premium feature designed for our most advanced traders.</p>
            
            <div className="premium-benefits">
              <h3>Premium includes:</h3>
              <ul>
                <li>✅ AI-Powered Auto Trading</li>
                <li>✅ Unlimited Alerts</li>
                <li>✅ Advanced Portfolio Analytics</li>
                <li>✅ 1-Year Signal History</li>
                <li>✅ Early Access to New Features</li>
                <li>✅ Priority Support</li>
              </ul>
            </div>

            <div className="current-tier">
              <p>Your current tier: <strong>{subscription?.tier || 'free'}</strong></p>
            </div>

            <button 
              className="upgrade-button"
              onClick={() => window.location.href = '/pricing'}
            >
              💎 Upgrade to Premium
            </button>

            <p className="upgrade-note">
              Get unlimited access to all Premium features including Auto Trading.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auto-trading-container">
      <header className="auto-trading-header">
        <h1>🤖 AI Auto Trading</h1>
        <p className="critical-warning">⚠️ EXPERIMENTAL FEATURE - DANGEROUS ⚠️</p>
      </header>

      <div className="tabs">
        <button
          className={`tab-button ${activeTab === 'warnings' ? 'active' : ''}`}
          onClick={() => setActiveTab('warnings')}
        >
          📋 Warnings & Risks
        </button>
        <button
          className={`tab-button ${activeTab === 'trade' ? 'active' : ''}`}
          onClick={() => setActiveTab('trade')}
        >
          💱 Execute Trade
        </button>
        <button
          className={`tab-button ${activeTab === 'active' ? 'active' : ''}`}
          onClick={() => setActiveTab('active')}
        >
          📊 Active Trades
        </button>
      </div>

      {/* WARNINGS TAB */}
      {activeTab === 'warnings' && (
        <div className="tab-content warnings-tab">
          <div className="warning-header">
            <h2>🚨 Critical Warnings About Auto Trading</h2>
            <p>READ ALL WARNINGS BEFORE PROCEEDING</p>
          </div>

          <div className="warnings-grid">
            {warnings.map((warning, idx) => (
              <div
                key={idx}
                className={`warning-card severity-${warning.severity}`}
              >
                <h3>{warning.title}</h3>
                <p>{warning.description}</p>
                <span className="severity-badge">{warning.severity}</span>
              </div>
            ))}
          </div>

          <div className="important-section">
            <h3>⚠️ Key Points to Remember:</h3>
            <ul>
              <li>AI models FAIL in unprecedented market conditions</li>
              <li>Past performance does NOT guarantee future results</li>
              <li>Your losses can exceed your initial investment (with leverage)</li>
              <li>Flash crashes can execute trades at insane prices</li>
              <li>No amount of backtesting prevents real-world disasters</li>
              <li>High-frequency traders have structural advantages over you</li>
              <li>Technical glitches can cause unintended trades</li>
              <li>Market gaps can skip over your stop-losses</li>
            </ul>
          </div>

          <div className="acknowledgement-section">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={riskAcknowledged}
                onChange={(e) => setRiskAcknowledged(e.target.checked)}
              />
              I understand that AI auto trading is DANGEROUS and can result in
              TOTAL LOSS OF CAPITAL
            </label>
          </div>
        </div>
      )}

      {/* TRADE TAB */}
      {activeTab === 'trade' && (
        <div className="tab-content trade-tab">
          {!riskAcknowledged && (
            <div className="blocking-warning">
              <h3>⛔ You Must Acknowledge Risks First</h3>
              <p>Go to the "Warnings & Risks" tab and check the acknowledgement box</p>
            </div>
          )}

          {riskAcknowledged && (
            <>
              <div className="trade-form">
                <h2>Configure Auto Trade</h2>

                <div className="form-group">
                  <label>Trading Pair</label>
                  <input
                    type="text"
                    name="symbol"
                    value={tradeData.symbol}
                    onChange={handleInputChange}
                    placeholder="e.g., BTC/USD"
                  />
                </div>

                <div className="form-group">
                  <label>Action</label>
                  <select
                    name="action"
                    value={tradeData.action}
                    onChange={handleInputChange}
                  >
                    <option value="BUY">BUY</option>
                    <option value="SELL">SELL</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Quantity</label>
                  <input
                    type="number"
                    name="quantity"
                    value={tradeData.quantity}
                    onChange={handleInputChange}
                    placeholder="0.00"
                    step="0.01"
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Stop Loss Price ⚠️ REQUIRED</label>
                    <input
                      type="number"
                      name="stop_loss"
                      value={tradeData.stop_loss || ''}
                      onChange={handleInputChange}
                      placeholder="Protection price"
                      step="0.01"
                    />
                  </div>
                  <div className="form-group">
                    <label>Take Profit Price ⚠️ REQUIRED</label>
                    <input
                      type="number"
                      name="take_profit"
                      value={tradeData.take_profit || ''}
                      onChange={handleInputChange}
                      placeholder="Target price"
                      step="0.01"
                    />
                  </div>
                </div>

                <button
                  className="btn btn-secondary"
                  onClick={assessRisk}
                  disabled={loading}
                >
                  {loading ? 'Assessing...' : 'Assess Risk'}
                </button>

                {riskAssessment && (
                  <div
                    className={`risk-assessment risk-${riskAssessment.level}`}
                  >
                    <h3>Risk Assessment: {riskAssessment.level}</h3>
                    <p className="risk-score">Score: {riskAssessment.score}/100</p>
                    <div className="warnings">
                      {riskAssessment.warnings.map((warning, idx) => (
                        <p key={idx}>⚠️ {warning}</p>
                      ))}
                    </div>
                    <p className="recommendation">
                      <strong>Recommendation:</strong> {riskAssessment.recommendation}
                    </p>
                  </div>
                )}
              </div>

              <div className="terms-section">
                <h3>Auto Trading Terms & Conditions</h3>

                <div className="terms-box">
                  <p>
                    By using automated trading, you agree that:
                  </p>
                  <ul>
                    <li>You understand cryptocurrency trading is extremely risky</li>
                    <li>You accept ALL potential losses up to 100% of your investment</li>
                    <li>You have read and understood all provided warnings</li>
                    <li>You will NOT hold the platform liable for any losses</li>
                    <li>You will monitor your account and positions actively</li>
                    <li>You understand AI models can fail unpredictably</li>
                    <li>You will set and maintain stop-losses on all positions</li>
                  </ul>
                </div>

                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={termsAccepted}
                    onChange={(e) => setTermsAccepted(e.target.checked)}
                  />
                  I have read and accept all auto trading terms and conditions
                </label>
              </div>

              <div className="action-buttons">
                {!previewData ? (
                  <button
                    className="btn btn-primary"
                    onClick={previewTrade}
                    disabled={!riskAcknowledged || !termsAccepted || loading}
                  >
                    {loading ? 'Loading...' : 'Preview Trade'}
                  </button>
                ) : (
                  <>
                    <div className="preview-result">
                      <h3>📊 Trade Preview</h3>
                      <p>{previewData.message}</p>
                      <ul>
                        <li>Symbol: {previewData.symbol}</li>
                        <li>Action: {previewData.action}</li>
                        <li>Quantity: {previewData.quantity}</li>
                        <li>Stop Loss: ${previewData.stop_loss}</li>
                        <li>Take Profit: ${previewData.take_profit}</li>
                      </ul>
                      <div className="warnings">
                        {previewData.warnings.map((w, idx) => (
                          <p key={idx}>⚠️ {w}</p>
                        ))}
                      </div>
                    </div>

                    <div className="final-confirmation">
                      <h4>🚨 FINAL CONFIRMATION 🚨</h4>
                      <p>
                        This trade will commit REAL MONEY immediately upon clicking
                        "Execute".
                      </p>
                      <p style={{ color: '#ff0000', fontWeight: 'bold' }}>
                        You could lose your entire investment.
                      </p>
                    </div>

                    <button
                      className="btn btn-danger"
                      onClick={executeTrade}
                      disabled={loading}
                    >
                      {loading ? 'Executing...' : '⚠️ EXECUTE TRADE ⚠️'}
                    </button>

                    <button
                      className="btn btn-secondary"
                      onClick={() => setPreviewData(null)}
                    >
                      Cancel & Edit
                    </button>
                  </>
                )}
              </div>
            </>
          )}
        </div>
      )}

      {/* ACTIVE TRADES TAB */}
      {activeTab === 'active' && (
        <div className="tab-content active-trades-tab">
          <h2>Your Active Auto Trades</h2>
          <p>Monitor your positions and stop-losses carefully.</p>
          <p style={{ color: '#ff6600' }}>
            ⚠️ Active trades will execute automatically. Be prepared to intervene.
          </p>
          
          {loadingTrades ? (
            <p>Loading active trades...</p>
          ) : activeTrades.length === 0 ? (
            <div className="no-trades-message">
              <p>No active trades at this time.</p>
              <p style={{ fontSize: '0.9em', color: '#888' }}>
                Your executed trades will appear here with real-time status.
              </p>
            </div>
          ) : (
            <div className="active-trades-list">
              {activeTrades.map((trade, idx) => (
                <div key={idx} className="trade-card">
                  <div className="trade-header">
                    <div>
                      <strong>{trade.symbol}</strong>
                      <span className={`action-badge ${trade.action.toLowerCase()}`}>
                        {trade.action}
                      </span>
                    </div>
                    <div className="trade-status" style={{ 
                      color: trade.status === 'open' ? '#4ade80' : '#fbbf24'
                    }}>
                      {trade.status.toUpperCase()}
                    </div>
                  </div>
                  
                  <div className="trade-details">
                    <div className="detail-row">
                      <span>Order ID:</span>
                      <code>{trade.order_id}</code>
                    </div>
                    <div className="detail-row">
                      <span>Quantity:</span>
                      <strong>{trade.quantity}</strong>
                    </div>
                    <div className="detail-row">
                      <span>Stop Loss:</span>
                      <span style={{ color: '#f87171' }}>${trade.stop_loss.toFixed(2)}</span>
                    </div>
                    <div className="detail-row">
                      <span>Take Profit:</span>
                      <span style={{ color: '#4ade80' }}>${trade.take_profit.toFixed(2)}</span>
                    </div>
                    <div className="detail-row">
                      <span>Entry Price:</span>
                      <span>${trade.entry_price ? trade.entry_price.toFixed(2) : 'N/A'}</span>
                    </div>
                    <div className="detail-row">
                      <span>Created:</span>
                      <small>{new Date(trade.created_at).toLocaleString()}</small>
                    </div>
                    <div className="detail-row">
                      <span>Exchange:</span>
                      <small>{trade.exchange}</small>
                    </div>
                  </div>
                  
                  <div className="trade-actions">
                    <button className="close-button" onClick={() => alert('Close trade feature coming soon')}>
                      Close Position
                    </button>
                    <button className="adjust-button" onClick={() => alert('Adjust stops feature coming soon')}>
                      Adjust Stops
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
