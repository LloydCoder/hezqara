import ipaddress
import socket
from urllib.parse import urlsplit
import httpx

class SSRFError(ValueError): pass

def _public_ip(host: str) -> bool:
    try: infos=socket.getaddrinfo(host,None,type=socket.SOCK_STREAM)
    except OSError as exc: raise SSRFError('host resolution failed') from exc
    return all(not any((lambda a: a.is_private or a.is_loopback or a.is_link_local or a.is_reserved or a.is_multicast or a.is_unspecified)(ipaddress.ip_address(info[4][0])) for info in infos) for _ in [0])

def validate_provider_url(url: str, allowed_hosts: set[str]) -> str:
    parsed=urlsplit(url); host=(parsed.hostname or '').lower().rstrip('.')
    if parsed.scheme!='https' or not host or parsed.username or parsed.password: raise SSRFError('provider URL must be an HTTPS URL without embedded credentials')
    if host not in {h.lower().rstrip('.') for h in allowed_hosts}: raise SSRFError('provider host is not allowlisted')
    if not _public_ip(host): raise SSRFError('provider host resolves to a non-public address')
    return parsed.geturl()

class TrustedHttpClient:
    def __init__(self, allowed_hosts:set[str], timeout:float=15.0): self.allowed_hosts=allowed_hosts; self.timeout=timeout
    async def get(self,url:str,**kwargs):
        safe_url=validate_provider_url(url,self.allowed_hosts)
        async with httpx.AsyncClient(timeout=self.timeout,follow_redirects=False) as client: return await client.get(safe_url,**kwargs)
