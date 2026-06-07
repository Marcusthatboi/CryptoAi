"""
Ollama AI Integration Module
============================

Integrates local Ollama models (Mistral, Neural Chat, etc.)
with the CryptoAI FastAPI backend for intelligent chat responses.
"""

import requests
import logging
from typing import Optional, Dict
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Ollama Configuration
OLLAMA_API_URL = "http://localhost:11434"
OLLAMA_MODEL = "mistral"  # or "neural-chat", "llama2"
OLLAMA_TIMEOUT = 60  # seconds

# Load system prompt from file
def load_system_prompt() -> str:
    """Load the Robinhood API specialization prompt."""
    prompt_file = Path(__file__).parent.parent / "Promt.txt"
    
    if prompt_file.exists():
        try:
            with open(prompt_file, 'r') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Could not load system prompt: {e}")
    
    # Fallback prompt if file not found
    return """You are an expert CryptoAI assistant specializing in cryptocurrency analysis and trading.
    
Your expertise includes:
1. Real-time price analysis and market trends
2. Portfolio management advice
3. Risk assessment for cryptocurrency investments
4. Robinhood API integration and trading automation
5. Technical analysis using moving averages and trend indicators

Always:
- Provide accurate, data-driven responses
- Prioritize security and risk management
- Explain complex concepts clearly
- Ask clarifying questions when needed
- Never provide guaranteed investment predictions"""


def check_ollama_health() -> bool:
    """
    Check if Ollama server is running and accessible.
    
    Returns:
        True if Ollama is available, False otherwise
    """
    try:
        response = requests.get(f"{OLLAMA_API_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except requests.RequestException as e:
        logger.warning(f"Ollama health check failed: {e}")
        return False


def get_ollama_response(
    user_message: str,
    system_prompt: Optional[str] = None,
    crypto_context: Optional[Dict] = None
) -> Optional[str]:
    """
    Get response from Ollama model.
    
    Args:
        user_message: User's input message
        system_prompt: System prompt for model behavior (optional)
        crypto_context: Additional cryptocurrency context (optional)
        
    Returns:
        Response from Ollama model, or None if request fails
    """
    if not check_ollama_health():
        logger.error("Ollama server is not running")
        return None
    
    # Build system prompt
    if system_prompt is None:
        system_prompt = load_system_prompt()
    
    # Add crypto context to message if provided
    context_text = ""
    if crypto_context:
        context_text = _build_context_string(crypto_context)
        user_message = f"{context_text}\n\nUser Question: {user_message}"
    
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": user_message,
            "system": system_prompt,
            "stream": False,
            "temperature": 0.7
        }
        
        response = requests.post(
            f"{OLLAMA_API_URL}/api/generate",
            json=payload,
            timeout=OLLAMA_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "").strip()
        else:
            logger.error(f"Ollama API error: {response.status_code}")
            return None
    
    except requests.Timeout:
        logger.error("Ollama request timed out")
        return None
    except requests.RequestException as e:
        logger.error(f"Ollama request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Error processing Ollama response: {e}")
        return None


def _build_context_string(crypto_context: Dict) -> str:
    """Build cryptocurrency context string for the prompt."""
    lines = ["CRYPTOCURRENCY CONTEXT:"]

    if crypto_context.get('username'):
        lines.append(f"- User: {crypto_context['username']}")

    if crypto_context.get('email'):
        lines.append(f"- Email: {crypto_context['email']}")

    if crypto_context.get('role'):
        lines.append(f"- Role: {crypto_context['role']}")

    if crypto_context.get('subscription_tier'):
        lines.append(f"- Subscription Tier: {str(crypto_context['subscription_tier']).upper()}")

    if crypto_context.get('portfolio_total_value') is not None:
        lines.append(f"- Portfolio Total Value: ${crypto_context['portfolio_total_value']:,.2f}")

    if crypto_context.get('portfolio_cash') is not None:
        lines.append(f"- Portfolio Cash: ${crypto_context['portfolio_cash']:,.2f}")

    if crypto_context.get('personal_buying_power') is not None:
        lines.append(f"- Personal Buying Power: ${crypto_context['personal_buying_power']:,.2f}")

    if crypto_context.get('holdings_count') is not None:
        lines.append(f"- Holdings Count: {crypto_context['holdings_count']}")

    if crypto_context.get('holdings_summary'):
        lines.append(f"- Holdings Summary: {'; '.join(crypto_context['holdings_summary'])}")
    
    if crypto_context.get('current_price'):
        lines.append(f"- Current Price: ${crypto_context['current_price']:,.2f}")
    
    if crypto_context.get('price_change_24h'):
        change = crypto_context['price_change_24h']
        lines.append(f"- 24h Change: {change:+.2f}%")
    
    if crypto_context.get('market_cap'):
        lines.append(f"- Market Cap: ${crypto_context['market_cap']:,.0f}")
    
    if crypto_context.get('trend'):
        lines.append(f"- Trend: {crypto_context['trend']}")
    
    if crypto_context.get('sma'):
        lines.append(f"- 5-Day SMA: ${crypto_context['sma']:.2f}")
    
    if crypto_context.get('volume_24h'):
        lines.append(f"- 24h Volume: ${crypto_context['volume_24h']:,.0f}")
    
    return "\n".join(lines)


def list_available_models() -> list:
    """
    Get list of available Ollama models.
    
    Returns:
        List of available model names
    """
    try:
        response = requests.get(
            f"{OLLAMA_API_URL}/api/tags",
            timeout=5
        )
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [model["name"] for model in models]
    except Exception as e:
        logger.warning(f"Could not fetch available models: {e}")
    
    return []


def switch_model(model_name: str) -> bool:
    """
    Switch to a different Ollama model.
    
    Args:
        model_name: Name of the model to switch to (e.g., 'mistral', 'neural-chat', 'llama2')
        
    Returns:
        True if switch successful, False otherwise
    """
    global OLLAMA_MODEL
    
    available_models = list_available_models()
    
    if not available_models:
        logger.error("Could not fetch available models from Ollama")
        return False
    
    # Check if model is available
    if model_name not in available_models:
        logger.error(f"Model '{model_name}' not found. Available: {available_models}")
        return False
    
    OLLAMA_MODEL = model_name
    logger.info(f"Switched to model: {model_name}")
    return True
