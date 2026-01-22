from typing import Dict, List, Optional, Callable, Any, Awaitable, Union, TypedDict
from dataclasses import dataclass, field
from datetime import datetime
import logging


@dataclass
class ParsedCallbackData:
    """Parsed STK Push callback data"""
    merchant_request_id: str
    checkout_request_id: str
    result_code: int
    result_description: str
    amount: Optional[float] = None
    mpesa_receipt_number: Optional[str] = None
    transaction_date: Optional[str] = None
    phone_number: Optional[str] = None
    is_success: bool = False
    error_message: Optional[str] = None


@dataclass
class ParsedC2BCallback:
    """Parsed C2B callback data"""
    transaction_type: str
    transaction_id: str
    transaction_time: str
    amount: float
    business_short_code: str
    bill_ref_number: str
    msisdn: str
    invoice_number: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None


@dataclass
class B2CResult:
    """B2C transaction result"""
    is_success: bool
    transaction_id: Optional[str] = None
    amount: Optional[float] = None
    recipient_phone: Optional[str] = None
    charges: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class B2BResult:
    """B2B transaction result"""
    is_success: bool
    transaction_id: Optional[str] = None
    amount: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class AccountBalanceResult:
    """Account balance result"""
    is_success: bool
    working_balance: Optional[float] = None
    available_balance: Optional[float] = None
    booked_balance: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class TransactionStatusResult:
    """Transaction status result"""
    is_success: bool
    receipt_no: Optional[str] = None
    amount: Optional[float] = None
    completed_time: Optional[str] = None
    originator_conversation_id: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ReversalResult:
    """Reversal result"""
    is_success: bool
    transaction_id: Optional[str] = None
    error_message: Optional[str] = None

class CallbackLogger(TypedDict, total=False):
    info: Callable[[str, Any], None]
    error: Callable[[str, Any], None]
    warn: Callable[[str, Any], None]


class CallbackHandlerOptions(TypedDict, total=False):
    # STK Push
    onSuccess: Optional[Callable[[ParsedCallbackData], Union[None, Awaitable[None]]]]
    onFailure: Optional[Callable[[ParsedCallbackData], Union[None, Awaitable[None]]]]
    onCallback: Optional[Callable[[ParsedCallbackData], Union[None, Awaitable[None]]]]

    # C2B
    onC2BConfirmation: Optional[Callable[[ParsedC2BCallback], Union[None, Awaitable[None]]]]
    onC2BValidation: Optional[Callable[[ParsedC2BCallback], Awaitable[bool]]]

    # B2C
    onB2CResult: Optional[
        Callable[[Dict[str, Optional[Union[bool, str, float]]]], Union[None, Awaitable[None]]]
    ]

    # B2B
    onB2BResult: Optional[
        Callable[[Dict[str, Optional[Union[bool, str, float]]]], Union[None, Awaitable[None]]]
    ]

    # Account Balance
    onAccountBalance: Optional[
        Callable[[Dict[str, Optional[Union[bool, str, float]]]], Union[None, Awaitable[None]]]
    ]

    # Transaction Status
    onTransactionStatus: Optional[
        Callable[[Dict[str, Optional[Union[bool, str, float]]]], Union[None, Awaitable[None]]]
    ]

    # Reversal
    onReversal: Optional[
        Callable[[Dict[str, Optional[Union[bool, str, float]]]], Union[None, Awaitable[None]]]
    ]

    # Misc
    validateIp: Optional[bool]
    allowedIps: Optional[List[str]]
    isDuplicate: Optional[Callable[[str], Union[bool, Awaitable[bool]]]]
    logger: Optional[CallbackLogger]

class MpesaCallbackHandler:
    SAFARICOM_IPS = [
        "196.201.214.200",
        "196.201.214.206",
        "196.201.213.114",
        "196.201.214.207",
        "196.201.214.208",
        "196.201.213.44",
        "196.201.212.127",
        "196.201.212.138",
        "196.201.212.129",
        "196.201.212.136",
        "196.201.212.74",
        "196.201.212.69",
    ]

    ERROR_MESSAGES = {
        0: "Success",
        1: "Insufficient funds in M-Pesa account",
        17: "User cancelled the transaction",
        26: "System internal error",
        1001: "Unable to lock subscriber, a transaction is already in process",
        1019: "Transaction expired. No response from user",
        1032: "Request cancelled by user",
        1037: "Timeout in sending PIN request",
        2001: "Wrong PIN entered",
        9999: "Request cancelled by user",
    }

    def __init__(
        self,
        on_success: Optional[Callable[[ParsedCallbackData], Union[None, Awaitable[None]]]] = None,
        on_failure: Optional[Callable[[ParsedCallbackData], Union[None, Awaitable[None]]]] = None,
        on_callback: Optional[Callable[[ParsedCallbackData], Union[None, Awaitable[None]]]] = None,
        on_c2b_confirmation: Optional[Callable[[ParsedC2BCallback], Union[None, Awaitable[None]]]] = None,
        on_c2b_validation: Optional[Callable[[ParsedC2BCallback], Awaitable[bool]]] = None,
        on_b2c_result: Optional[Callable[[B2CResult], Union[None, Awaitable[None]]]] = None,
        on_b2b_result: Optional[Callable[[B2BResult], Union[None, Awaitable[None]]]] = None,
        on_account_balance: Optional[Callable[[AccountBalanceResult], Union[None, Awaitable[None]]]] = None,
        on_transaction_status: Optional[Callable[[TransactionStatusResult], Union[None, Awaitable[None]]]] = None,
        on_reversal: Optional[Callable[[ReversalResult], Union[None, Awaitable[None]]]] = None,
        validate_ip: bool = True,
        allowed_ips: Optional[List[str]] = None,
        is_duplicate: Optional[Callable[[str], Union[bool, Awaitable[bool]]]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.on_success = on_success
        self.on_failure = on_failure
        self.on_callback = on_callback
        self.on_c2b_confirmation = on_c2b_confirmation
        self.on_c2b_validation = on_c2b_validation
        self.on_b2c_result = on_b2c_result
        self.on_b2b_result = on_b2b_result
        self.on_account_balance = on_account_balance
        self.on_transaction_status = on_transaction_status
        self.on_reversal = on_reversal
        self.validate_ip = validate_ip
        self.allowed_ips = allowed_ips or self.SAFARICOM_IPS
        self.is_duplicate = is_duplicate
        self.logger = logger or logging.getLogger(__name__)

    def validate_callback_ip(self, ip_address: str) -> bool:
       
        if not self.validate_ip:
            return True
        
        return ip_address in self.allowed_ips

    def get_error_message(self, result_code: int) -> str:
      
        return self.ERROR_MESSAGES.get(
            result_code,
            f"Transaction failed with code: {result_code}"
        )

    def format_transaction_date(self, date_str: str) -> str:
        
        year = date_str[0:4]
        month = date_str[4:6]
        day = date_str[6:8]
        hours = date_str[8:10]
        minutes = date_str[10:12]
        seconds = date_str[12:14]
        
        return f"{year}-{month}-{day}T{hours}:{minutes}:{seconds}"

    def parse_callback(self, callback: Dict[str, Any]) -> ParsedCallbackData:
       
        stk_callback = callback["Body"]["stkCallback"]
        
        result_code = stk_callback["ResultCode"]
        parsed = ParsedCallbackData(
            merchant_request_id=stk_callback["MerchantRequestID"],
            checkout_request_id=stk_callback["CheckoutRequestID"],
            result_code=result_code,
            result_description=stk_callback["ResultDesc"],
            is_success=(result_code == 0),
            error_message=self.get_error_message(result_code) if result_code != 0 else None
        )
        
        # If transaction was successful, parse metadata
        if result_code == 0 and "CallbackMetadata" in stk_callback:
            metadata = stk_callback["CallbackMetadata"]
            self._extract_metadata(metadata, parsed)
        
        return parsed

    def _extract_metadata(self, metadata: Dict[str, Any], parsed: ParsedCallbackData) -> None:
        
        for item in metadata.get("Item", []):
            name = item.get("Name")
            value = item.get("Value")
            
            if name == "Amount":
                parsed.amount = float(value)
            elif name == "MpesaReceiptNumber":
                parsed.mpesa_receipt_number = str(value)
            elif name == "TransactionDate":
                parsed.transaction_date = self.format_transaction_date(str(value))
            elif name == "PhoneNumber":
                parsed.phone_number = str(value)

    def parse_c2b_callback(self, callback: Dict[str, Any]) -> ParsedC2BCallback:
        return ParsedC2BCallback(
            transaction_type=callback["TransactionType"],
            transaction_id=callback["TransID"],
            transaction_time=callback["TransTime"],
            amount=float(callback["TransAmount"]),
            business_short_code=callback["BusinessShortCode"],
            bill_ref_number=callback["BillRefNumber"],
            msisdn=callback["MSISDN"],
            invoice_number=callback.get("InvoiceNumber"),
            first_name=callback.get("FirstName"),
            middle_name=callback.get("MiddleName"),
            last_name=callback.get("LastName"),
        )

    def parse_b2c_callback(self, callback: Dict[str, Any]) -> B2CResult:
        result = callback["Result"]
        result_code = result["ResultCode"]
        
        parsed = B2CResult(
            is_success=(result_code == 0),
            error_message=self.get_error_message(result_code) if result_code != 0 else None
        )
        
        if result_code == 0 and "ResultParameters" in result:
            for param in result["ResultParameters"].get("ResultParameter", []):
                key = param.get("Key")
                value = param.get("Value")
                
                if key == "TransactionReceipt":
                    parsed.transaction_id = str(value)
                elif key == "TransactionAmount":
                    parsed.amount = float(value)
                elif key == "ReceiverPartyPublicName":
                    parsed.recipient_phone = str(value)
                elif key == "B2CChargesPaidAccountAvailableFunds":
                    parsed.charges = float(value)
        
        return parsed

    def parse_b2b_callback(self, callback: Dict[str, Any]) -> B2BResult:
        result = callback["Result"]
        result_code = result["ResultCode"]
        
        parsed = B2BResult(
            is_success=(result_code == 0),
            error_message=self.get_error_message(result_code) if result_code != 0 else None
        )
        
        if result_code == 0 and "ResultParameters" in result:
            for param in result["ResultParameters"].get("ResultParameter", []):
                key = param.get("Key")
                value = param.get("Value")
                
                if key == "TransactionReceipt":
                    parsed.transaction_id = str(value)
                elif key == "TransactionAmount":
                    parsed.amount = float(value)
        
        return parsed

    def parse_account_balance_callback(self, callback: Dict[str, Any]) -> AccountBalanceResult:
        result = callback["Result"]
        result_code = result["ResultCode"]
        
        parsed = AccountBalanceResult(
            is_success=(result_code == 0),
            error_message=self.get_error_message(result_code) if result_code != 0 else None
        )
        
        if result_code == 0 and "ResultParameters" in result:
            for param in result["ResultParameters"].get("ResultParameter", []):
                key = param.get("Key")
                value = param.get("Value")
                
                if key == "WorkingAccountAvailableFunds":
                    parsed.working_balance = float(value)
                elif key == "AvailableBalance":
                    parsed.available_balance = float(value)
                elif key == "BookedBalance":
                    parsed.booked_balance = float(value)
        
        return parsed

    def parse_transaction_status_callback(self, callback: Dict[str, Any]) -> TransactionStatusResult:
        result = callback["Result"]
        result_code = result["ResultCode"]
        
        parsed = TransactionStatusResult(
            is_success=(result_code == 0),
            originator_conversation_id=result.get("OriginatorConversationID"),
            error_message=self.get_error_message(result_code) if result_code != 0 else None
        )
        
        if result_code == 0 and "ResultParameters" in result:
            for param in result["ResultParameters"].get("ResultParameter", []):
                key = param.get("Key")
                value = param.get("Value")
                
                if key == "ReceiptNo":
                    parsed.receipt_no = str(value)
                elif key == "TransactionAmount":
                    parsed.amount = float(value)
                elif key == "TransCompletedTime":
                    parsed.completed_time = str(value)
        
        return parsed

    def parse_reversal_callback(self, callback: Dict[str, Any]) -> ReversalResult:
        result = callback["Result"]
        result_code = result["ResultCode"]
        
        return ReversalResult(
            is_success=(result_code == 0),
            transaction_id=result.get("TransactionID"),
            error_message=self.get_error_message(result_code) if result_code != 0 else None
        )

    async def handle_callback(
        self,
        callback: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> None:
        # Validate IP if provided
        if ip_address and not self.validate_callback_ip(ip_address):
            self.logger.warning(f"Invalid callback IP: {ip_address}")
            raise ValueError(f"Invalid callback IP: {ip_address}")
        
        
        parsed = self.parse_callback(callback)
        
        self.logger.info(
            f"Processing STK callback - CheckoutRequestID: {parsed.checkout_request_id}, "
            f"ResultCode: {parsed.result_code}"
        )
        
        
        if self.is_duplicate:
            is_dupe = self.is_duplicate(parsed.checkout_request_id)
            if hasattr(is_dupe, '__await__'):
                is_dupe = await is_dupe
            
            if is_dupe:
                self.logger.warning(
                    f"Duplicate callback detected - CheckoutRequestID: {parsed.checkout_request_id}"
                )
                return  
        
        
        if self.on_callback:
            result = self.on_callback(parsed)
            if hasattr(result, '__await__'):
                await result
        
        
        if parsed.is_success and self.on_success:
            result = self.on_success(parsed)
            if hasattr(result, '__await__'):
                await result
        elif not parsed.is_success and self.on_failure:
            result = self.on_failure(parsed)
            if hasattr(result, '__await__'):
                await result

    async def handle_c2b_validation(self, callback: Dict[str, Any]) -> bool:
        parsed = self.parse_c2b_callback(callback)
        
        self.logger.info(f"Processing C2B validation - TransactionID: {parsed.transaction_id}")
        
        if self.on_c2b_validation:
            return await self.on_c2b_validation(parsed)
        
        
        return True

    async def handle_c2b_confirmation(self, callback: Dict[str, Any]) -> None:
        parsed = self.parse_c2b_callback(callback)
        
        self.logger.info(f"Processing C2B confirmation - TransactionID: {parsed.transaction_id}")
        
        if self.on_c2b_confirmation:
            result = self.on_c2b_confirmation(parsed)
            if hasattr(result, '__await__'):
                await result

    @staticmethod
    def create_callback_response(success: bool = True, message: Optional[str] = None) -> Dict[str, Any]:
        return {
            "ResultCode": 0 if success else 1,
            "ResultDesc": message or ("Accepted" if success else "Rejected")
        }