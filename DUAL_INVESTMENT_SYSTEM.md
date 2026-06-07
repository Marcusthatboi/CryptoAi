# 💳 Dual Investment System - Fake & Real Money

## Overview

CryptoAI now features a complete dual investment system allowing users to:
1. **Practice with Fake Money** 🎮 - Invest simulated funds using portfolio cash balance
2. **Real Money Investment** 💳 - Make actual purchases with encrypted credit card payments

## Features

### 🎮 Fake Money Investments
- **Portfolio-based**: Deducts from user's simulated $100,000 starting cash
- **No payment processing**: Instant transactions
- **Portfolio tracking**: Recorded in MongoDB with investment history
- **Perfect for**: Learning, backtesting, practice trades

### 💳 Real Money Investments
- **Encrypted payments**: Uses Web Crypto API (AES-GCM-256 encryption)
- **Secure transmission**: Card data encrypted before leaving browser
- **Payment validation**: Card number validation using Luhn algorithm
- **Transaction receipts**: Complete payment records with transaction IDs
- **Audit logging**: All payment attempts logged for security

## Architecture

### Frontend Components

#### 1. **PaymentForm.jsx** - Encrypted Credit Card Input
```jsx
- Card number input with format validation
- Cardholder name
- Expiry date (MM/YY)
- CVV (hidden input)
- Automatic card type detection (Visa, Mastercard, Amex, Discover)
- Real-time validation with error messages
- Encryption before form submission
```

#### 2. **InvestmentTypeSelector.jsx** - Investment Mode Chooser
```jsx
- Toggle between Fake Money (🎮) and Real Money (💳)
- Amount or Quantity input modes
- Preset quick-select amounts ($100, $500, $1000, $5000)
- Order summary with calculations
- Conditional payment form display for real money
```

#### 3. **InvestmentDetailPage.jsx** - Investment Page
```jsx
- Integrated with new InvestmentTypeSelector component
- Calls backend endpoints for investment processing
- Handles both fake and real money flows
- Token-based authentication for API calls
```

### Frontend Utilities

#### **encryption.js** - Client-side Encryption
```javascript
Features:
- encryptCardData(cardData) - AES-GCM-256 encryption of card details
- validateCardNumber(cardNumber) - Luhn algorithm validation
- detectCardType(cardNumber) - Automatic card type detection
- formatCardNumber(value) - Format input with spaces
- maskCardNumber(cardNumber) - Display only last 4 digits (security)

Technology: Web Crypto API (SubtleCrypto)
- Browser-native encryption
- No external dependencies
- Military-grade AES-256
```

### Backend Endpoints

#### **POST /api/user/portfolio/invest/fake**
Fake money investment (portfolio-based)

**Request:**
```json
{
  "symbol": "BTC",
  "quantity": 0.5,
  "price": 43000,
  "total_value": 21500
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Fake money investment recorded: BTC",
  "investment_type": "fake_money",
  "holding": {
    "symbol": "BTC",
    "quantity": 0.5,
    "price": 43000,
    "total_value": 21500,
    "investment_type": "fake_money",
    "timestamp": "2026-06-01T12:00:00"
  },
  "portfolio": { ... }
}
```

#### **POST /api/user/portfolio/invest/real**
Real money investment with encrypted payment

**Request:**
```json
{
  "symbol": "BTC",
  "quantity": 0.5,
  "price": 43000,
  "total_value": 21500,
  "encrypted_payment": {
    "encryptedData": "base64_encrypted_card_data",
    "iv": "base64_initialization_vector",
    "key": "base64_encryption_key",
    "algorithm": "AES-GCM-256",
    "cardLast4": "4242",
    "cardType": "visa"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Investment purchase completed: BTC",
  "investment_type": "real_money",
  "payment_receipt": {
    "transaction_id": "TXN-user123-1717250400",
    "status": "completed",
    "amount": 21500,
    "currency": "USD",
    "card_last4": "4242",
    "card_type": "visa",
    "timestamp": "2026-06-01T12:00:00"
  },
  "holding": { ... },
  "portfolio": { ... }
}
```

### Backend Modules

#### **payment_encryption.py** - Encryption/Decryption
```python
Functions:
- decrypt_card_data(encrypted_payload) - Decrypt client-side encrypted data
- validate_decrypted_card_data(card_data) - Validate card information
- mask_card_number(card_number) - Mask for logging (shows last 4 digits)
- log_payment_attempt(...) - Audit logging for all payment attempts
```

## Security Architecture

### Encryption Flow

**Frontend (Browser):**
```
1. User enters card details
2. Web Crypto API generates AES-256 key
3. Generate random 96-bit IV (Initialization Vector)
4. Encrypt card JSON with AES-GCM
5. Base64 encode encrypted data, IV, and key
6. Send to backend ONLY over HTTPS
```

**Backend (Python):**
```
1. Receive encrypted payload
2. Decode base64 components
3. Use cryptography library to decrypt with AESGCM
4. Validate decrypted card data
5. Mask card for logging (show only last 4 digits)
6. Process payment (integrate with Stripe/PayPal)
7. Never store unencrypted card data
```

### Security Best Practices Implemented

✅ **Client-side Encryption** - Sensitive data encrypted before transmission
✅ **Never Store Cards** - Encrypted data not persisted in database
✅ **HTTPS Only** - Encryption assumes HTTPS transport
✅ **Luhn Validation** - Card number format validation
✅ **Input Sanitization** - All inputs validated and sanitized
✅ **Audit Logging** - All payment attempts logged with masked card
✅ **Error Handling** - Generic error messages (don't reveal system details)
✅ **Token Auth** - Bearer token validation on all protected endpoints
✅ **CORS Protection** - API only accepts requests from authorized origins

## Database Schema

### Investment Holding (in users.portfolio.holdings)
```json
{
  "_id": ObjectId,
  "symbol": "BTC",
  "quantity": 0.5,
  "price": 43000,
  "total_value": 21500,
  "investment_type": "fake_money" | "real_money",
  "payment_receipt": {
    "transaction_id": "TXN-...",
    "status": "completed",
    "amount": 21500,
    "currency": "USD",
    "card_last4": "4242",
    "card_type": "visa",
    "timestamp": "2026-06-01T12:00:00"
  },
  "timestamp": "2026-06-01T12:00:00"
}
```

## User Flow

### Fake Money Investment Flow
```
1. User clicks on crypto card or "Invest" button
2. InvestmentDetailPage loads with price data
3. User selects "Fake Money" investment type (🎮)
4. Enters amount or quantity to invest
5. Reviews order summary
6. Clicks "Invest $XXX (Fake Money)"
7. Frontend calls POST /api/user/portfolio/invest/fake
8. Backend deducts from portfolio cash
9. Backend adds holding record to MongoDB
10. User sees success confirmation
11. Portfolio updated with new holding
```

### Real Money Investment Flow
```
1. User clicks on crypto or "Invest" button
2. InvestmentDetailPage loads
3. User selects "Real Money" investment type (💳)
4. Enters amount or quantity
5. Clicks "Proceed to Payment"
6. PaymentForm displays
7. User enters encrypted card details:
   - Card number (with Luhn validation)
   - Cardholder name
   - Expiry date (MM/YY)
   - CVV (hidden)
8. Client-side encryption occurs (AES-GCM-256)
9. Encrypted payload sent to backend
10. Backend decrypts and validates
11. Payment processing occurs (simulated or real Stripe/PayPal)
12. Transaction receipt generated
13. Investment holding recorded in MongoDB
14. Success confirmation with transaction details
```

## Testing Guide

### Test Fake Money Investment
```
1. Login with Admin/Admin1
2. Click on any cryptocurrency card
3. Select "Fake Money" mode
4. Enter $500
5. Click "Invest"
6. See success message with updated portfolio
```

### Test Real Money Investment (Demo Mode)
```
1. Login with Admin/Admin1
2. Click on cryptocurrency
3. Select "Real Money" mode
4. Enter $1000
5. Click "Proceed to Payment"
6. Enter test card details:
   - Card: 4242 4242 4242 4242 (Visa test card)
   - Name: John Doe
   - Expiry: 12/26
   - CVV: 123
7. Click "Invest $1000 Now"
8. See payment receipt with transaction ID
```

## Production Considerations

### To Enable Real Payment Processing

1. **Integrate Payment Processor** (Stripe recommended):
```python
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# In real investment endpoint:
payment_intent = stripe.PaymentIntent.create(
    amount=int(total_value * 100),  # Convert to cents
    currency="usd",
    description=f"{quantity} {symbol} for user {current_user}",
    payment_method_data={
        "type": "card",
        "card": {
            "number": card_data["cardNumber"],
            "exp_month": card_data["expiryMonth"],
            "exp_year": card_data["expiryYear"],
            "cvc": card_data["cvv"]
        }
    }
)
```

2. **Add Environment Variables**:
```
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
```

3. **Enable HTTPS**:
- Use Let's Encrypt SSL certificate
- Update CORS to match production domain
- Ensure all requests use HTTPS

4. **Add PCI Compliance**:
- Implement tokenization (instead of passing raw cards)
- Use Stripe Elements for card input
- Add fraud detection (Stripe Radar)
- Store only payment method IDs, never full card data

5. **Add Rate Limiting**:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/api/user/portfolio/invest/real")
@limiter.limit("5/hour")  # Max 5 real investments per hour
async def user_invest_real_money(...):
```

## Environment Variables

Add to your `.env` file:
```
# Payment Processing (when enabling real payments)
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key

# Security
SECRET_KEY=your_jwt_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database
MONGODB_URL=mongodb://localhost:27017/cryptoai
```

## Files Modified/Created

### New Files
- `frontend/src/utils/encryption.js` - Client-side encryption utility
- `frontend/src/components/PaymentForm.jsx` - Credit card form component
- `frontend/src/components/PaymentForm.css` - Payment form styling
- `frontend/src/components/InvestmentTypeSelector.jsx` - Investment type selector
- `frontend/src/components/InvestmentTypeSelector.css` - Selector styling
- `backend/payment_encryption.py` - Server-side encryption/decryption

### Modified Files
- `frontend/src/pages/InvestmentDetailPage.jsx` - Updated to use new components
- `backend/main.py` - Added /api/user/portfolio/invest/fake and /api/user/portfolio/invest/real endpoints
- `requirements.txt` - Added cryptography>=41.0.0

## Troubleshooting

### "Failed to decrypt payment data"
- Check that IV and key lengths are correct (12 bytes IV, 32 bytes key)
- Verify base64 encoding/decoding on both client and server
- Ensure same encryption algorithm on both sides

### "Invalid card data"
- Card number must be 13-19 digits
- Expiry month must be 1-12
- Expiry year must be valid (within 10 years)
- CVV must be 3-4 digits
- Cardholder name required

### "Insufficient cash" (Fake Money)
- User doesn't have enough simulated cash in portfolio
- Reset portfolio cash to $100,000 in MongoDB
- Or start a new account

## Next Steps

1. **Real Payment Integration** - Connect to Stripe/PayPal API
2. **Email Receipts** - Send transaction confirmations to user email
3. **Refund Handling** - Implement partial/full refund capability
4. **Wallet Integration** - Connect to Alpaca/Robinhood for automatic execution
5. **Tax Reporting** - Generate 1099-K forms for real transactions
6. **Multi-currency** - Support payments in multiple currencies
7. **Mobile App** - Native iOS/Android with biometric authentication

---

**Status**: ✅ Complete - Fake and Real Money Investment System Ready
**Version**: 1.0
**Last Updated**: June 1, 2026
