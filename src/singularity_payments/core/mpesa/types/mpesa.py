from typing import TypedDict, Optional, Any, Protocol, Literal
from typing_extensions import NotRequired

class STKPushRequest(TypedDict):
    amount: int
    phoneNumber: str
    accountReference: str
    transactionDesc: str

    callbackUrl: NotRequired[str]

class STKPushResponse(TypedDict):
    MerchantRequestID: str
    CheckoutRequestID: str
    ResponseCode: str
    ResponseDescription: str
    CustomerMessage: str

class TransactionStatusRequest(TypedDict):
    CheckoutRequestID: str

class TransactionStatusResponse(TypedDict):
    ResponseCode: str
    ResponseDescription: str
    MerchantRequestID: str
    CheckoutRequestID: str
    ResultCode: str
    ResultDesc: str

class C2BRegisterRequest(TypedDict):
    shortCode: str
    responseType: Literal["Completed", "Cancelled"]
    confirmationURL: str
    validationURL: str

class CallbackItem(TypedDict):
    Name: str
    Value: str | int

class CallbackMetadata(TypedDict):
    Item: list[CallbackItem]

class STKObj(TypedDict):
    MerchantRequestID: str
    CheckoutRequestID: str
    ResultCode: int
    ResultDesc: str
    CallbackMetadata: NotRequired[CallbackMetadata]

class STKCallback(TypedDict):
    Body: STKObj

class C2BCallback(TypedDict):
    TransactionType: str
    TransID: str
    TransTime: str
    TransAmount: str
    BusinessShortCode: str
    BillRefNumber: str
    InvoiceNumber: NotRequired[str]
    OrgAccountBalance: NotRequired[str]
    ThirdPartyTransID: NotRequired[str]
    MSISDN: str
    FirstName: NotRequired[str]
    MiddleName: NotRequired[str]
    LastName: NotRequired[str]

class C2BRegisterResponse(TypedDict):
    OriginatorConversationID: str
    ResponseCode: str
    ResponseDescription: str 

B2CCommandID = Literal["BusinessPayment", "SalaryPayment", "PromotionPayment"]

class B2CRequest(TypedDict):
    amount: int
    phoneNumber: str
    commandID: B2CCommandID
    remarks: str
    occasion: NotRequired[str]
    resultUrl: NotRequired[str]
    timeoutUrl: NotRequired[str]

class B2CResponse(TypedDict):
    ConversationID: str
    OriginatorConversationID: str
    ResponseCode: str
    ResponseDescription: str

    
class ResultParameter(TypedDict):
    Key: str
    Value: str | int

class ReferenceItem(TypedDict):
    Key: str
    Value: str | int

class ResultObj(TypedDict):
    ResultType: int
    ResultCode: int
    ResultDesc: str
    OriginatorConversationID: str
    ConversationID: str
    TransactionID: str
    ResultParameters: NotRequired[list[ResultParameter]]
    ReferenceData: NotRequired[ReferenceItem]

class B2CCallback(TypedDict):
    Result: ResultObj

B2BCommandID = Literal[
    "BusinessPayBill",
    "BusinessBuyGoods",
    "DisburseFundsToBusiness",
    "BusinessToBusinessTransfer",
    "MerchantToMerchantTransfer"
]

class B2BRequest(TypedDict):
    amount: int
    partyB: str # Receiving business shortcode
    commandID: B2BCommandID
    senderIdentifierType: Literal[
        "1", # MSISDN
        "2", # Till
        "4"  # Paybill
    ]
    receiverIdentifierType: Literal[
        "1", 
        "2", 
        "4"  
    ]
    remarks: str
    accountReference: str
    resultUrl: NotRequired[str]
    timeoutUrl: NotRequired[str]

class B2BResponse(TypedDict):
    ConversatioinID: str
    OriginatorConversationID: str
    ResponseCode: str
    ResponseDescription: str

class B2BCallback(TypedDict):
    Result: ResultObj

BalanceIdentifierType = Literal["1", "2", "4"]

class AccountBalanceRequest(TypedDict):
    partyA: NotRequired[str]    # Optional, defaults to config.shortcode
    identifierType: NotRequired[BalanceIdentifierType] # Optional, defaults to '4'
    remarks: NotRequired[str]
    resultUrl: NotRequired[str]
    timeoutUrl: NotRequired[str]

class AccountBalanceResponse(TypedDict):
    ConversationID: str
    OriginatorConversationID: str
    ResponseCode: str
    ResponseDescription: str

class AccountBalanceCallback(TypedDict):
    Result: ResultObj


class GeneralTransactionStatusRequest(TypedDict):
    transactionID: str
    partyA: NotRequired[str]
    identifierType: NotRequired[Literal[
        "1",
        "2",
        "4"
    ]]
    remarks: NotRequired[str]
    occasion: NotRequired[str]
    resultUrl: NotRequired[str]
    timeoutUrl: NotRequired[str]

class GeneralTransactionStatusResponse(TypedDict):
    ConversationID: str
    OriginatorConversationID: str
    ResponseCode: str
    ResponseDescription: str

class TransactionStatusCallback(TypedDict):
    Result: ResultObj

class ReversalRequest(TypedDict):
    transactionID: str
    amount: int
    receiverParty: NotRequired[str]
    receiverIdentifierType: NotRequired[Literal[
        "1",
        "2",
        "4"
    ]]
    remarks: NotRequired[str]
    occasion: NotRequired[str]
    resultUrl: NotRequired[str]
    timeoutUrl: NotRequired[str]

class ReversalResponse(TypedDict):
    ConversationID: str
    OriginatorConversationID: str
    ResponseCode: str
    ResponseDescription: str

class ReversalCallback(TypedDict):
    Result: ResultObj

class DynamicQRRequest(TypedDict):
    merchantName: str
    refNo: str
    amount: int
    transactionType: Literal[
        "BG",
        "WA",
        "PB",
        "SM"
    ]
    creditPartyIdentifier: str
    size: NotRequired[Literal["300", "500"]] # QR Code size

class DynamicQRResponse(TypedDict):
    ResponseCode: str
    ResponseDescription: str
    QRCode: str # base64 encoded image