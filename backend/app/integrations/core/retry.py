from app.integrations.core.contracts import IntegrationError

RETRYABLE=frozenset({'timeout','network_error','rate_limited','provider_unavailable'})
PERMANENT=frozenset({'configuration_error','authentication_error','authorization_error','validation_error','provider_rejected','malformed_response','unsupported_capability'})

def normalize_error(code:str,message:str,status:int|None=None)->IntegrationError:
    if status==429: code='rate_limited'
    elif status==401: code='authentication_error'
    elif status==403: code='authorization_error'
    elif status in {400,422}: code='validation_error'
    elif status==409: code='provider_rejected'
    elif status is not None and status>=500: code='provider_unavailable'
    if code not in RETRYABLE and code not in PERMANENT: code='unknown_error'
    return IntegrationError(code,message[:500],code in RETRYABLE,status)

def retry_delay(attempt:int,base:float=1.0,cap:float=60.0)->float:
    if attempt<0: raise ValueError('attempt must be non-negative')
    return min(cap,base*(2**min(attempt,8)))
