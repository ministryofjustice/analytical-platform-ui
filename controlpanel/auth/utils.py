import base64
import hashlib


def pkce_transform(code_verifier):
    """Transforms the code verifier to a code challenge."""
    digest = hashlib.sha256(code_verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
