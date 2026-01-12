from typing import Literal
from typing import TypedDict, Optional, Any, Protocol
from typing_extensions import NotRequired

Environment = Literal["sandbox", "production"]

class MpesaConfig(TypedDict):
    consumerKey: str
    consumerSecret: str
    passkey: str
    shortcode: str
    environment: Environment

    callbackUrl: NotRequired[str]
    timeoutUrl: NotRequired[str]
    resultUrl: NotRequired[str]
    initiatorName: NotRequired[str]
    securityCredential: NotRequired[str]

class MpesaPlugin(Protocol):
    name: str

    def init(self, client: Any) -> None:
        ...
