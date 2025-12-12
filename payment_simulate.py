"""
Payment Gateway Simulator
=========================
Simulates realistic payment processing for demo purposes.
Includes card validation (Luhn algorithm), UPI validation,
and realistic success/failure rates.

No actual payment gateway is used - this is for demonstration only.
"""

import random
import time
import uuid
import re
from datetime import datetime


class PaymentSimulator:
    """
    Simulates a payment gateway for card and UPI transactions.
    Provides realistic validation and random success/failure simulation.
    """
    
    # Success rate for payments (90% succeed, 10% fail)
    SUCCESS_RATE = 0.90
    
    # Simulated processing delay in seconds
    PROCESSING_DELAY = 1.5
    
    # Common failure reasons (randomly selected on payment failure)
    FAILURE_REASONS = [
        "Transaction declined by bank",
        "Insufficient funds",
        "Card expired",
        "Payment gateway timeout",
        "Transaction limit exceeded",
        "Suspected fraud - please contact your bank",
        "Network error - please try again",
        "Card issuer unavailable",
        "Invalid transaction",
        "Payment declined - contact your bank",
        "Daily transaction limit reached",
        "Bank server is temporarily unavailable",
    ]

    def __init__(self, success_rate=None, simulate_delay=True):
        """
        Initialize the payment simulator.
        
        Args:
            success_rate: Override default success rate (0.0 to 1.0)
            simulate_delay: Whether to add realistic processing delay
        """
        self.success_rate = success_rate if success_rate is not None else self.SUCCESS_RATE
        self.simulate_delay = simulate_delay

    def luhn_check(self, card_number: str) -> bool:
        """
        Validate card number using Luhn algorithm.
        
        Args:
            card_number: Card number as string (digits only)
            
        Returns:
            True if valid, False otherwise
        """
        # Remove any spaces or dashes
        card_number = re.sub(r'[\s-]', '', card_number)
        
        if not card_number.isdigit() or len(card_number) < 13:
            return False
            
        total = 0
        reverse_digits = card_number[::-1]
        
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
            
        return total % 10 == 0

    def validate_card_details(self, card_number: str, expiry: str, cvv: str) -> dict:
        """
        Validate card details before processing.
        
        Returns:
            dict with 'valid' boolean and 'errors' list
        """
        errors = []
        card_number = re.sub(r'[\s-]', '', card_number)
        
        # Validate card number
        if not card_number:
            errors.append("Card number is required")
        elif not card_number.isdigit():
            errors.append("Card number must contain only digits")
        elif len(card_number) < 13 or len(card_number) > 19:
            errors.append("Invalid card number length")
        elif not self.luhn_check(card_number):
            errors.append("Invalid card number (failed checksum)")
        
        # Validate expiry (MM/YY format)
        if not expiry:
            errors.append("Expiry date is required")
        else:
            expiry_match = re.match(r'^(\d{2})/(\d{2})$', expiry)
            if not expiry_match:
                errors.append("Expiry must be in MM/YY format")
            else:
                month, year = int(expiry_match.group(1)), int(expiry_match.group(2))
                if month < 1 or month > 12:
                    errors.append("Invalid expiry month")
                else:
                    # Check if card is expired
                    current_year = datetime.now().year % 100
                    current_month = datetime.now().month
                    if year < current_year or (year == current_year and month < current_month):
                        errors.append("Card has expired")
        
        # Validate CVV
        if not cvv:
            errors.append("CVV is required")
        elif not cvv.isdigit() or len(cvv) not in [3, 4]:
            errors.append("CVV must be 3 or 4 digits")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def validate_upi(self, upi_id: str) -> dict:
        """
        Validate UPI ID format.
        
        Returns:
            dict with 'valid' boolean and 'errors' list
        """
        errors = []
        
        if not upi_id:
            errors.append("UPI ID is required")
        elif not re.match(r'^[\w.-]+@[\w]+$', upi_id):
            errors.append("Invalid UPI ID format (should be like name@bank)")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def _simulate_processing(self):
        """Add realistic processing delay"""
        if self.simulate_delay:
            time.sleep(self.PROCESSING_DELAY)

    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        return f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

    def process_card_payment(self, card_number: str, expiry: str, cvv: str, amount: float) -> dict:
        """
        Process a card payment.
        
        Args:
            card_number: Card number
            expiry: Expiry date (MM/YY)
            cvv: CVV code
            amount: Payment amount
            
        Returns:
            dict with transaction result
        """
        card_number = re.sub(r'[\s-]', '', card_number)
        
        # Validate card details first
        validation = self.validate_card_details(card_number, expiry, cvv)
        if not validation['valid']:
            return {
                "success": False,
                "status": "validation_failed",
                "errors": validation['errors'],
                "transaction_id": None
            }
        
        # Simulate processing
        self._simulate_processing()
        
        # Random success/failure based on success rate (75% success, 25% fail)
        if random.random() <= self.success_rate:
            return {
                "success": True,
                "status": "completed",
                "transaction_id": self._generate_transaction_id(),
                "amount": amount,
                "payment_method": "card",
                "card_last_four": card_number[-4:],
                "message": "Payment successful"
            }
        else:
            return {
                "success": False,
                "status": "failed",
                "errors": [random.choice(self.FAILURE_REASONS)],
                "transaction_id": self._generate_transaction_id()
            }

    def process_upi_payment(self, upi_id: str, amount: float) -> dict:
        """
        Process a UPI payment.
        
        Args:
            upi_id: UPI ID (e.g., name@upi)
            amount: Payment amount
            
        Returns:
            dict with transaction result
        """
        # Validate UPI ID
        validation = self.validate_upi(upi_id)
        if not validation['valid']:
            return {
                "success": False,
                "status": "validation_failed",
                "errors": validation['errors'],
                "transaction_id": None
            }
        
        # Simulate processing
        self._simulate_processing()
        
        # Random success/failure
        if random.random() <= self.success_rate:
            return {
                "success": True,
                "status": "completed",
                "transaction_id": self._generate_transaction_id(),
                "amount": amount,
                "payment_method": "upi",
                "upi_id": upi_id,
                "message": "Payment successful"
            }
        else:
            return {
                "success": False,
                "status": "failed", 
                "errors": [random.choice(["UPI server timeout", "Transaction declined", "UPI ID not found"])],
                "transaction_id": self._generate_transaction_id()
            }


# Singleton instance for easy import
payment_gateway = PaymentSimulator()


def process_payment(payment_method: str, amount: float, **kwargs) -> dict:
    """
    Convenience function to process payment.
    
    Args:
        payment_method: 'card' or 'upi'
        amount: Payment amount
        **kwargs: Payment details (card_number, expiry, cvv for card; upi_id for UPI)
        
    Returns:
        dict with transaction result
    """
    if payment_method == 'card':
        return payment_gateway.process_card_payment(
            card_number=kwargs.get('card_number', ''),
            expiry=kwargs.get('expiry', ''),
            cvv=kwargs.get('cvv', ''),
            amount=amount
        )
    elif payment_method == 'upi':
        return payment_gateway.process_upi_payment(
            upi_id=kwargs.get('upi_id', ''),
            amount=amount
        )
    else:
        return {
            "success": False,
            "status": "error",
            "errors": [f"Unknown payment method: {payment_method}"],
            "transaction_id": None
        }