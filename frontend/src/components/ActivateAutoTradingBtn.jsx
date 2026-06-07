import React, { useState } from 'react';
import './ActivateAutoTradingBtn.css';
import AutoTradingCoin from './AutoTradingCoin';

const ActivateAutoTradingBtn = ({ symbol, currentPrice, onAutoTradingChange }) => {
  const [showModal, setShowModal] = useState(false);
  const [isActive, setIsActive] = useState(false);

  const handleOpenModal = (e) => {
    e.stopPropagation();
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
  };

  const handleAutoTradingChange = (status) => {
    setIsActive(status);
    if (onAutoTradingChange) {
      onAutoTradingChange(status);
    }
  };

  return (
    <>
      <button
        className={`activate-auto-trading-btn ${isActive ? 'active' : ''}`}
        onClick={handleOpenModal}
        title="Configure auto trading for this cryptocurrency"
      >
        <span className="btn-icon">
          {isActive ? '🤖' : '⚙️'}
        </span>
        <span className="btn-text">
          {isActive ? 'Auto Trading Active' : 'Activate Auto Trading'}
        </span>
        {isActive && <span className="active-indicator"></span>}
      </button>

      {showModal && (
        <AutoTradingCoin
          symbol={symbol}
          currentPrice={currentPrice}
          onClose={handleCloseModal}
          onStatusChange={handleAutoTradingChange}
        />
      )}
    </>
  );
};

export default ActivateAutoTradingBtn;
