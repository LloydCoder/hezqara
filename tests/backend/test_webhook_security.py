import hashlib,hmac,pytest
from app.security.webhook import verify_hmac

def test_valid_hmac():
    body=b'{}'; secret='s'; sig=hmac.new(secret.encode(),body,hashlib.sha256).hexdigest(); verify_hmac(body,sig,secret)

def test_invalid_hmac():
    with pytest.raises(Exception): verify_hmac(b'{}','bad','s')
