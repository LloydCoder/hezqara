import hashlib,hmac,pytest
from app.security.webhook import verify_hmac

def test_valid_hmac():
    body=b'{}'; secret='s'; signature=hmac.new(secret.encode(),body,hashlib.sha256).hexdigest(); verify_hmac(body,signature,secret)

def test_invalid_hmac():
    with pytest.raises(Exception): verify_hmac(b'{}','bad','s')


def test_stripe_signature_is_verified_with_timestamp():
    import time
    import stripe

    payload = b'{"id":"evt_test","type":"invoice.paid","data":{"object":{"id":"in_test"}}}'
    secret = "stripe-signing-secret"
    timestamp = int(time.time())
    signed = f"{timestamp}.".encode() + payload
    signature = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    header = f"t={timestamp},v1={signature}"
    event = stripe.Webhook.construct_event(payload, header, secret)
    assert event["id"] == "evt_test"


def test_stripe_signature_rejects_tampering():
    import time
    import stripe

    payload = b'{"id":"evt_test"}'
    secret = "stripe-signing-secret"
    timestamp = int(time.time())
    signature = hmac.new(secret.encode(), f"{timestamp}.".encode() + payload, hashlib.sha256).hexdigest()
    header = f"t={timestamp},v1={signature}"
    with pytest.raises(stripe.error.SignatureVerificationError):
        stripe.Webhook.construct_event(payload + b" ", header, secret)
