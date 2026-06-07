# Ollama AI Integration Setup Guide

## Overview
Your CryptoAI backend is now integrated with **Ollama**, a free local AI platform. This means your AI assistant runs entirely on your machine with no API costs!

## Prerequisites
- ✅ Ollama installed (you already installed it!)
- ✅ Backend updated with Ollama integration
- ✅ Robinhood API specialization prompt ready

## Quick Start

### Step 1: Start Ollama Server
Open a PowerShell terminal and run:
```powershell
ollama serve
```

Keep this terminal open - Ollama will run in the background on `http://localhost:11434`

You should see:
```
listening on 127.0.0.1:11434
```

### Step 2: Pull a Model (In a New Terminal)
Choose a model based on your needs:

**Recommended for CryptoAI (Balanced Speed/Quality):**
```powershell
ollama pull mistral
```

**Alternative Models:**
```powershell
# Smaller, faster (4.1GB) - Good for CPU
ollama pull neural-chat

# Larger, smarter (7GB) - Need decent GPU
ollama pull llama2

# Very fast, lightweight (3.8GB)
ollama pull orca-mini
```

### Step 3: Update Backend Dependencies
In your project root directory:
```powershell
pip install -r requirements.txt
```

### Step 4: Start Your Backend
```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

You should see:
```
Uvicorn running on http://127.0.0.1:8000
```

### Step 5: Test the Integration
Open your browser and go to:
```
http://localhost:8000/docs
```

Click on **POST /api/chat** and try these test messages:
- "What's the current price of Bitcoin?"
- "Analyze the Ethereum trend"
- "How do I use the Robinhood API for trading?"

## Available Endpoints

### Chat with Ollama
```
POST /api/chat
Body: {"message": "Your question here"}
```

### Check Ollama Status
```
GET /api/ollama/status
```

Response:
```json
{
  "status": "running",
  "available": true,
  "model": "mistral",
  "available_models": ["mistral", "neural-chat"]
}
```

### Switch Models
```
POST /api/ollama/switch-model/neural-chat
```

## Troubleshooting

### "Ollama not available" Error
**Solution:** Make sure `ollama serve` is running in a separate terminal

### Model Takes Too Long to Respond
**Solution:** 
- Switch to a smaller model: `ollama pull neural-chat`
- Or get a GPU (Ollama supports NVIDIA/AMD/Apple Silicon)

### "Prompt.txt not found" Warning
**Solution:** The Robinhood prompt file loads automatically if it exists, otherwise uses a default

### How to Uninstall a Model
```powershell
ollama rm mistral
```

## Model Sizes & Performance

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| orca-mini | 3.8GB | ⚡⚡⚡ Fast | ⭐⭐ | CPU-only systems |
| neural-chat | 4.1GB | ⚡⚡ Fast | ⭐⭐⭐ | Good balance |
| mistral | 4.3GB | ⚡⚡ Fast | ⭐⭐⭐⭐ | **Recommended** |
| llama2 | 7.4GB | ⚡ Medium | ⭐⭐⭐⭐⭐ | GPU recommended |

## Advanced: Custom System Prompt

The AI uses your `Promt.txt` file as a system prompt. To customize:

1. Edit `Promt.txt` in your project root
2. Add your custom instructions
3. Restart the backend

Example customization:
```
You are a CryptoAI trading assistant specialized in:
1. Robinhood API integration
2. Risk management strategies
3. Technical analysis
4. Portfolio optimization
```

## Performance Tips

1. **First Request is Slower** - Model loads into memory on first use
2. **Run on GPU** - Much faster if you have NVIDIA/AMD/Apple Silicon
3. **Warm Up** - Send a test message before getting important responses
4. **Monitor RAM** - Models use 2-8GB RAM depending on size

## Next Steps

1. ✅ Start `ollama serve`
2. ✅ Pull a model (`ollama pull mistral`)
3. ✅ Start backend (`python -m uvicorn backend.main:app --reload`)
4. ✅ Test at `http://localhost:8000/docs`
5. 🎉 Chat with your AI-powered CryptoAI backend!

## Security Notes

- ✅ All data stays on your machine (no API calls to OpenAI/Claude)
- ✅ No API keys needed
- ✅ Models downloaded to local disk
- ✅ All responses generated locally

Enjoy your private, cost-free AI assistant! 🚀
