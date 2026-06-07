import React, { useState, useEffect } from 'react';
import './AutoTradingCoin.css';
import { cryptoAPI } from '../utils/api';

const AutoTradingCoin = ({ symbol, currentPrice, onClose }) => {
  const [settings, setSettings] = useState({
    enabled: false,
    buy_percentage: 5.0,
    sell_percentage: 10.0,
    reference_price: currentPrice,
  });
  
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [activeTab, setActiveTab] = useState('config');
  const [recommendations, setRecommendations] = useState(null);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);

  useEffect(() => {
    loadSettings();
  }, [symbol]);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await cryptoAPI.getAutoTradingCoinSettings(symbol);
      setSettings(response.data);
      
      // Load stats if enabled
      if (response.data.enabled) {
        const statsResponse = await cryptoAPI.getAutoTradingCoinStats(symbol);
        setStats(statsResponse.data);
      }
    } catch (err) {
      console.error('Error loading settings:', err);
      setError('Failed to load auto trading settings');
    } finally {
      setLoading(false);
    }
  };

  const handleEnable = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await cryptoAPI.enableAutoTradingCoin(
        symbol,
        settings.buy_percentage,
        settings.sell_percentage,
        settings.reference_price || currentPrice
      );
      
      setSuccessMessage(response.data?.message || 'Auto trading enabled');
      setSettings(prev => ({
        ...prev,
        enabled: true,
        reference_price: settings.reference_price || currentPrice
      }));
      
      // Reload stats
      const statsResponse = await cryptoAPI.getAutoTradingCoinStats(symbol);
      setStats(statsResponse.data);
      
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to enable auto trading');
    } finally {
      setLoading(false);
    }
  };

  const handleDisable = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await cryptoAPI.disableAutoTradingCoin(symbol);
      
      setSuccessMessage(response.data?.message || 'Auto trading disabled');
      setSettings(prev => ({
        ...prev,
        enabled: false
      }));
      setStats(null);
      
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to disable auto trading');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await cryptoAPI.updateAutoTradingCoinSettings(
        symbol,
        settings.buy_percentage,
        settings.sell_percentage,
        settings.reference_price
      );
      
      setSuccessMessage('Settings updated successfully');
      setSettings(response.data?.settings || settings);
      
      // Reload stats
      if (settings.enabled) {
        const statsResponse = await cryptoAPI.getAutoTradingCoinStats(symbol);
        setStats(statsResponse.data);
      }
      
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update settings');
    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendations = async () => {
    try {
      setLoadingRecommendations(true);
      setError('');
      const response = await cryptoAPI.getAutoTradingAIRecommendations(symbol);
      setRecommendations(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch AI recommendations');
    } finally {
      setLoadingRecommendations(false);
    }
  };

  const applyRecommendations = () => {
    if (recommendations?.recommendations) {
      const rec = recommendations.recommendations;
      setSettings({
        ...settings,
        buy_percentage: rec.buy_percentage,
        sell_percentage: rec.sell_percentage
      });
      setSuccessMessage('✨ AI recommendations applied!');
      setTimeout(() => setSuccessMessage(''), 3000);
    }
  };

  const calculateBuyTrigger = () => {
    const reference = settings.reference_price || currentPrice;
    const drop = reference * (settings.buy_percentage / 100);
    return (reference - drop).toFixed(2);
  };

  const calculateSellTrigger = () => {
    if (stats?.average_cost) {
      const gain = stats.average_cost * (settings.sell_percentage / 100);
      return (stats.average_cost + gain).toFixed(2);
    }
    return 'N/A';
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  return (
    <div className="auto-trading-coin-modal">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Auto Trading - {symbol}</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        {successMessage && (
          <div className="success-message">{successMessage}</div>
        )}
        {error && (
          <div className="error-message">{error}</div>
        )}

        <div className="modal-tabs">
          <button
            className={`tab-btn ${activeTab === 'config' ? 'active' : ''}`}
            onClick={() => setActiveTab('config')}
          >
            ⚙️ Configuration
          </button>
          {settings.enabled && (
            <button
              className={`tab-btn ${activeTab === 'stats' ? 'active' : ''}`}
              onClick={() => setActiveTab('stats')}
            >
              📊 Statistics
            </button>
          )}
          {settings.enabled && (
            <button
              className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => setActiveTab('history')}
            >
              📜 History
            </button>
          )}
        </div>

        {activeTab === 'config' && (
          <div className="tab-content config-content">
            <div className="status-display">
              <div className="status-item">
                <span className="status-label">Status:</span>
                <span className={`status-value ${settings.enabled ? 'enabled' : 'disabled'}`}>
                  {settings.enabled ? '🟢 ACTIVE' : '⚫ INACTIVE'}
                </span>
              </div>
              <div className="status-item">
                <span className="status-label">Current Price:</span>
                <span className="status-value">{formatCurrency(currentPrice)}</span>
              </div>
            </div>

            {!settings.enabled ? (
              <div className="config-section">
                <h3>Enable Auto Trading</h3>
                
                <div className="form-group">
                  <label>Reference Price (starting point)</label>
                  <input
                    type="number"
                    value={settings.reference_price || currentPrice}
                    onChange={(e) => setSettings({
                      ...settings,
                      reference_price: parseFloat(e.target.value)
                    })}
                    step="0.01"
                    disabled={loading}
                  />
                  <small>The price at which buy/sell calculations will be based</small>
                </div>

                <div className="ai-recommendations-section">
                  <button
                    className="ai-recommendations-btn"
                    onClick={fetchRecommendations}
                    disabled={loadingRecommendations || loading}
                  >
                    {loadingRecommendations ? '🤖 Analyzing...' : '✨ Get AI Recommendations'}
                  </button>
                  
                  {recommendations && (
                    <div className="recommendations-panel">
                      <div className="recommendations-header">
                        <h4>🤖 AI Recommendations</h4>
                        <p className="volatility-tier">{recommendations.recommendations.volatility_tier} Volatility</p>
                      </div>
                      <p className="recommendation-reason">{recommendations.recommendations.reason}</p>
                      <div className="recommendation-values">
                        <div className="rec-value">
                          <label>Buy %:</label>
                          <span className="rec-highlight">{recommendations.recommendations.buy_percentage}%</span>
                          <span className="current-value">(Current: {settings.buy_percentage}%)</span>
                        </div>
                        <div className="rec-value">
                          <label>Sell %:</label>
                          <span className="rec-highlight">{recommendations.recommendations.sell_percentage}%</span>
                          <span className="current-value">(Current: {settings.sell_percentage}%)</span>
                        </div>
                      </div>
                      <button
                        className="apply-recommendations-btn"
                        onClick={applyRecommendations}
                        disabled={loading}
                      >
                        ✓ Apply Recommendations
                      </button>
                    </div>
                  )}
                </div>

                <div className="form-group">
                  <label>
                    Buy Percentage: <strong>{settings.buy_percentage}%</strong>
                  </label>
                  <input
                    type="range"
                    min="0.1"
                    max="50"
                    step="0.5"
                    value={settings.buy_percentage}
                    onChange={(e) => setSettings({
                      ...settings,
                      buy_percentage: parseFloat(e.target.value)
                    })}
                    disabled={loading}
                  />
                  <p className="trigger-info">
                    🔴 BUY when price drops to {formatCurrency(calculateBuyTrigger())}
                  </p>
                </div>

                <div className="form-group">
                  <label>
                    Sell Percentage: <strong>{settings.sell_percentage}%</strong>
                  </label>
                  <input
                    type="range"
                    min="0.1"
                    max="50"
                    step="0.5"
                    value={settings.sell_percentage}
                    onChange={(e) => setSettings({
                      ...settings,
                      sell_percentage: parseFloat(e.target.value)
                    })}
                    disabled={loading}
                  />
                  <p className="trigger-info">
                    🟢 SELL when price rises to {calculateSellTrigger()}
                  </p>
                </div>

                <button
                  className="action-btn enable-btn"
                  onClick={handleEnable}
                  disabled={loading}
                >
                  {loading ? 'Enabling...' : '▶️ Enable Auto Trading'}
                </button>
              </div>
            ) : (
              <div className="config-section">
                <h3>Active Auto Trading Configuration</h3>
                
                <div className="form-group">
                  <label>Reference Price</label>
                  <input
                    type="number"
                    value={settings.reference_price || currentPrice}
                    onChange={(e) => setSettings({
                      ...settings,
                      reference_price: parseFloat(e.target.value)
                    })}
                    step="0.01"
                    disabled={loading}
                  />
                </div>

                <div className="form-group">
                  <label>
                    Buy Percentage: <strong>{settings.buy_percentage}%</strong>
                  </label>
                  <input
                    type="range"
                    min="0.1"
                    max="50"
                    step="0.5"
                    value={settings.buy_percentage}
                    onChange={(e) => setSettings({
                      ...settings,
                      buy_percentage: parseFloat(e.target.value)
                    })}
                    disabled={loading}
                  />
                  <p className="trigger-info">
                    🔴 BUY when price drops to {formatCurrency(calculateBuyTrigger())}
                  </p>
                </div>

                <div className="form-group">
                  <label>
                    Sell Percentage: <strong>{settings.sell_percentage}%</strong>
                  </label>
                  <input
                    type="range"
                    min="0.1"
                    max="50"
                    step="0.5"
                    value={settings.sell_percentage}
                    onChange={(e) => setSettings({
                      ...settings,
                      sell_percentage: parseFloat(e.target.value)
                    })}
                    disabled={loading}
                  />
                  <p className="trigger-info">
                    🟢 SELL when price rises to {calculateSellTrigger()}
                  </p>
                </div>

                <div className="button-group">
                  <button
                    className="action-btn update-btn"
                    onClick={handleUpdate}
                    disabled={loading}
                  >
                    {loading ? 'Updating...' : '💾 Save Changes'}
                  </button>
                  <button
                    className="action-btn disable-btn"
                    onClick={handleDisable}
                    disabled={loading}
                  >
                    {loading ? 'Disabling...' : '⏹️ Stop Auto Trading'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'stats' && stats && (
          <div className="tab-content stats-content">
            <div className="stats-grid">
              <div className="stat-card">
                <span className="stat-label">Total Profit/Loss</span>
                <span className={`stat-value ${stats.total_profit_loss >= 0 ? 'positive' : 'negative'}`}>
                  {formatCurrency(stats.total_profit_loss)}
                </span>
              </div>

              <div className="stat-card">
                <span className="stat-label">Total Buys</span>
                <span className="stat-value">{stats.total_buys}</span>
              </div>

              <div className="stat-card">
                <span className="stat-label">Total Sells</span>
                <span className="stat-value">{stats.total_sells}</span>
              </div>

              <div className="stat-card">
                <span className="stat-label">Winning Sells</span>
                <span className="stat-value">{stats.winning_sells}</span>
              </div>

              <div className="stat-card">
                <span className="stat-label">Win Rate</span>
                <span className="stat-value">{stats.win_rate}</span>
              </div>

              <div className="stat-card">
                <span className="stat-label">Quantity Held</span>
                <span className="stat-value">{stats.quantity_held.toFixed(4)}</span>
              </div>

              <div className="stat-card">
                <span className="stat-label">Average Cost</span>
                <span className="stat-value">
                  {stats.average_cost ? formatCurrency(stats.average_cost) : 'N/A'}
                </span>
              </div>

              <div className="stat-card">
                <span className="stat-label">Last Action</span>
                <span className="stat-value">
                  {stats.last_action?.timestamp 
                    ? new Date(stats.last_action.timestamp).toLocaleTimeString()
                    : 'None'
                  }
                </span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="tab-content history-content">
            <div className="history-info">
              <button 
                className="refresh-btn"
                onClick={loadSettings}
                disabled={loading}
              >
                🔄 Refresh
              </button>
            </div>
            {stats?.actions_history && stats.actions_history.length > 0 ? (
              <div className="history-list">
                {stats.actions_history.map((action, idx) => (
                  <div key={idx} className="history-item">
                    <div className="history-header">
                      <span className={`action-badge ${action.action_type.toLowerCase()}`}>
                        {action.action_type}
                      </span>
                      <span className="history-time">
                        {new Date(action.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div className="history-details">
                      <p>{action.reason || action.action_type}</p>
                      {action.profit_loss && (
                        <p className={action.profit_loss > 0 ? 'positive' : 'negative'}>
                          P/L: {formatCurrency(action.profit_loss)}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-history">No trading actions yet</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AutoTradingCoin;
