from __future__ import annotations
import base64, hashlib, secrets
from dataclasses import dataclass
from urllib.parse import urlencode, urlsplit

class SMARTValidationError(ValueError): pass

@dataclass(frozen=True)
class SMARTConfiguration:
    issuer:str
    authorization_endpoint:str
    token_endpoint:str
    jwks_uri:str|None
    scopes_supported:tuple[str,...]
    capabilities:tuple[str,...]

    @classmethod
    def from_document(cls, document:dict) -> "SMARTConfiguration":
        required=('issuer','authorization_endpoint','token_endpoint')
        missing=[k for k in required if not isinstance(document.get(k),str) or not document[k]]
        if missing: raise SMARTValidationError(f'missing SMART configuration fields: {", ".join(missing)}')
        for key in ('issuer','authorization_endpoint','token_endpoint','jwks_uri'):
            value=document.get(key)
            if value:
                parsed=urlsplit(value)
                if parsed.scheme!='https' or parsed.username or parsed.password: raise SMARTValidationError(f'{key} must be an HTTPS URL without embedded credentials')
        return cls(document['issuer'],document['authorization_endpoint'],document['token_endpoint'],document.get('jwks_uri'),tuple(document.get('scopes_supported',())),tuple(document.get('capabilities',())))

@dataclass(frozen=True)
class PKCEChallenge:
    verifier:str
    challenge:str
    method:str='S256'

def create_pkce() -> PKCEChallenge:
    verifier=base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode()
    challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    return PKCEChallenge(verifier,challenge)

def create_oauth_state()->str:
    return secrets.token_urlsafe(32)

def build_authorization_url(config:SMARTConfiguration,client_id:str,redirect_uri:str,scopes:list[str],state:str,pkce:PKCEChallenge,launch_context:dict|None=None,nonce:str|None=None) -> str:
    if not client_id or not state: raise SMARTValidationError('client_id and state are required')
    if urlsplit(redirect_uri).scheme!='https': raise SMARTValidationError('redirect URI must be HTTPS')
    allowed=set(config.scopes_supported)
    if allowed and any(scope not in allowed for scope in scopes): raise SMARTValidationError('requested scope is not supported by discovered SMART server')
    params={'response_type':'code','client_id':client_id,'redirect_uri':redirect_uri,'scope':' '.join(scopes),'state':state,'code_challenge':pkce.challenge,'code_challenge_method':pkce.method}
    if nonce: params['nonce']=nonce
    if launch_context:
        if launch_context.get('launch'): params['launch']=str(launch_context['launch'])
        if launch_context.get('patient'): params['launch/patient']=''
    return config.authorization_endpoint+'?'+urlencode(params)

def validate_token_response(response:dict)->dict:
    if not isinstance(response,dict) or not response.get('access_token'): raise SMARTValidationError('SMART token response must contain access_token')
    token_type=response.get('token_type','Bearer')
    if token_type.lower()!='bearer': raise SMARTValidationError('only Bearer token type is supported')
    scopes=tuple(str(response.get('scope','')).split()) if response.get('scope') else ()
    return {'token_type':'Bearer','scope':scopes,'expires_in':response.get('expires_in'),'refresh_token_present':bool(response.get('refresh_token'))}
