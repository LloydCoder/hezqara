from app.infrastructure.http import client
class AthenaHealthClient:
    def __init__(self,base_url:str,token:str): self.base_url=base_url.rstrip('/'); self.token=token
    async def request(self,method:str,path:str,**kwargs):
        async with client() as http:
            headers={"Authorization":f"Bearer {self.token}"}; headers.update(kwargs.pop("headers",{})); return await http.request(method,self.base_url+path,headers=headers,**kwargs)
