from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import padding
import base64

def encryptInitiatorPassword(
    initiatorPassword: str,
    certificatePath: str
) -> str:
    with open(certificatePath, "rb") as f:
        cert_bytes = f.read()

        if b"BEGIN CERTIFICATE" in cert_bytes:
            cert = x509.load_pem_x509_certificate(cert_bytes)
        else:
            cert = x509.load_der_x509_certificate(cert_bytes)

    public_key = cert.public_key()

    encrypted = public_key.encrypt(
        initiatorPassword.encode(),
        padding.PKCS1v15()
    )

    securityCredential = base64.b64encode(encrypted).decode("utf-8")
    return securityCredential

