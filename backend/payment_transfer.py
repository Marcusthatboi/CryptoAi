"""
Payment Transfer Module for CryptoAI
Handles Stripe payment processing with encrypted crypto wallet transfers
"""
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import stripe
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# Supported cryptocurrencies for transfer
SUPPORTED_CRYPTOS = {
    "BTC": {"name": "Bitcoin", "network": "bitcoin", "min_transfer": 0.0001},
    "ETH": {"name": "Ethereum", "network": "ethereum", "min_transfer": 0.001},
    "USDT": {"name": "Tether", "network": "ethereum", "min_transfer": 10},
    "USD": {"name": "US Dollar", "network": "bank", "min_transfer": 1},
}

class PaymentTransferError(Exception):
    """Custom exception for payment transfer errors"""
    pass

class PaymentTransferManager:
    """Manages payment to encrypted wallet transfers"""
    
    def __init__(self, db=None, wallet_manager=None):
        self.db = db
        self.wallet_manager = wallet_manager
        self.collection_name = "payment_transfers"
    
    def create_payment_intent_for_crypto(
        self,
        amount: float,
        currency: str = "usd",
        crypto_symbol: str = "BTC",
        user_id: str = None,
        wallet_label: str = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe payment intent for purchasing crypto
        
        Args:
            amount: USD amount to pay
            currency: Payment currency (usd, eur, etc.)
            crypto_symbol: Target cryptocurrency
            user_id: User making the payment
            wallet_label: Optional label for the wallet
            
        Returns:
            Payment intent details including client_secret
        """
        if crypto_symbol not in SUPPORTED_CRYPTOS:
            raise PaymentTransferError(f"Unsupported crypto: {crypto_symbol}")
        
        try:
            # Create Stripe payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency.lower(),
                automatic_payment_methods={"enabled": True},
                metadata={
                    "crypto_symbol": crypto_symbol,
                    "user_id": user_id or "anonymous",
                    "wallet_label": wallet_label or "default",
                    "type": "crypto_purchase"
                }
            )
            
            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "amount": amount,
                "crypto_symbol": crypto_symbol,
                "status": intent.status,
                "amount_crypto_estimated": self._estimate_crypto_amount(amount, crypto_symbol)
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {e}")
            raise PaymentTransferError(f"Failed to create payment: {str(e)}")
    
    def _estimate_crypto_amount(self, usd_amount: float, crypto_symbol: str) -> float:
        """Estimate crypto amount based on approximate prices"""
        # These should be fetched from real-time prices in production
        approximate_prices = {
            "BTC": 67500.0,
            "ETH": 3450.0,
            "USDT": 1.0,
            "USD": 1.0
        }
        
        price = approximate_prices.get(crypto_symbol, 1.0)
        return round(usd_amount / price, 8)
    
    async def record_transfer(
        self,
        user_id: str,
        payment_intent_id: str,
        crypto_symbol: str,
        encrypted_wallet: Dict[str, Any],
        amount_usd: float,
        amount_crypto: float,
        status: str = "pending"
    ) -> bool:
        """Record a payment transfer in database"""
        if not self.db:
            logger.warning("No database, transfer not recorded")
            return False
        
        try:
            collection = self.db[self.collection_name]
            
            transfer_doc = {
                "user_id": user_id,
                "payment_intent_id": payment_intent_id,
                "crypto_symbol": crypto_symbol,
                "encrypted_wallet": encrypted_wallet,
                "amount_usd": amount_usd,
                "amount_crypto": amount_crypto,
                "status": status,  # pending, processing, completed, failed
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await collection.update_one(
                {"payment_intent_id": payment_intent_id},
                {"$set": transfer_doc},
                upsert=True
            )
            
            logger.info(f"Recorded transfer {payment_intent_id} for user {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error recording transfer: {e}")
            return False
    
    async def update_transfer_status(
        self,
        payment_intent_id: str,
        status: str,
        transaction_hash: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update transfer status after processing"""
        if not self.db:
            return False
        
        try:
            collection = self.db[self.collection_name]
            
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if transaction_hash:
                update_data["transaction_hash"] = transaction_hash
            
            if error_message:
                update_data["error_message"] = error_message
            
            if status == "completed":
                update_data["completed_at"] = datetime.utcnow().isoformat()
            
            await collection.update_one(
                {"payment_intent_id": payment_intent_id},
                {"$set": update_data}
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating transfer status: {e}")
            return False
    
    async def get_transfer(self, payment_intent_id: str) -> Optional[Dict]:
        """Get transfer details by payment intent ID"""
        if not self.db:
            return None
        
        try:
            collection = self.db[self.collection_name]
            return await collection.find_one({"payment_intent_id": payment_intent_id})
        except Exception as e:
            logger.error(f"Error fetching transfer: {e}")
            return None
    
    async def get_user_transfers(self, user_id: str, limit: int = 10) -> list:
        """Get recent transfers for a user"""
        if not self.db:
            return []
        
        try:
            collection = self.db[self.collection_name]
            cursor = collection.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(limit)
            
            return await cursor.to_list(length=limit)
        
        except Exception as e:
            logger.error(f"Error fetching user transfers: {e}")
            return []
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> Dict:
        """Verify Stripe webhook signature"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            raise PaymentTransferError("Invalid webhook payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise PaymentTransferError("Invalid webhook signature")

    async def process_successful_payment(
        self,
        payment_intent_id: str,
        decrypted_wallet_address: str,
        crypto_symbol: str,
        amount_crypto: float
    ) -> Dict[str, Any]:
        """
        Process a successful payment and initiate crypto transfer
        
        This is where you would integrate with your exchange/custodian
        to actually transfer crypto to the user's wallet.
        """
        try:
            # Update status to processing
            await self.update_transfer_status(payment_intent_id, "processing")
            
            # In production, you would:
            # 1. Call your exchange API to initiate transfer
            # 2. Or submit to your custodian service
            # 3. Or send to a blockchain network directly
            
            # For now, we simulate the transfer
            # Replace this with actual crypto transfer logic
            
            logger.info(
                f"Initiating transfer of {amount_crypto} {crypto_symbol} "
                f"to wallet {decrypted_wallet_address[:10]}..."
            )
            
            # Simulate transfer delay
            # In production: await exchange_api.transfer(wallet_address, amount_crypto)
            
            # Mark as completed (in production, this would be done by webhook)
            await self.update_transfer_status(
                payment_intent_id,
                "completed",
                transaction_hash=f"tx_{payment_intent_id[:16]}"
            )
            
            return {
                "status": "completed",
                "transaction_hash": f"tx_{payment_intent_id[:16]}",
                "wallet_address": self._mask_wallet(decrypted_wallet_address),
                "crypto_amount": amount_crypto,
                "crypto_symbol": crypto_symbol
            }
        
        except Exception as e:
            logger.error(f"Error processing payment: {e}")
            await self.update_transfer_status(
                payment_intent_id,
                "failed",
                error_message=str(e)
            )
            raise PaymentTransferError(f"Failed to process transfer: {str(e)}")
    
    def _mask_wallet(self, address: str) -> str:
        """Mask wallet address for display"""
        if len(address) <= 10:
            return address
        return address[:6] + "..." + address[-4:]


# Standalone functions
def get_supported_cryptos() -> Dict[str, Dict]:
    """Get list of supported cryptocurrencies"""
    return SUPPORTED_CRYPTOS

def validate_transfer_amount(amount: float, crypto_symbol: str) -> bool:
    """Validate transfer amount meets minimum requirements"""
    if crypto_symbol not in SUPPORTED_CRYPTOS:
        return False
    
    min_amount = SUPPORTED_CRYPTOS[crypto_symbol]["min_transfer"]
    return amount >= min_amount
