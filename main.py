from auth import Auth
from tracker import Tracker
from schema import CredRequest
from fastapi.responses import RedirectResponse
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()
tracker = Tracker()
authy = Auth(tracker.econ)
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    ver = authy.validate(token)
    
    if not ver[0]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return ver[1]

@app.get("/{tag}")
async def get_url(tag: str, request: Request):
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "-1.-1.-1.-1"

    url = tracker.get_url(tag, client_ip)

    return RedirectResponse(url)

@app.post("/register")
async def register(request: CredRequest):
    if request.organization and request.secret:
        reg_res = authy.register(
            request.organization,
            request.secret
        )
        return reg_res
    return (False, "Invalid request parameters.")

@app.post("/auth")
async def auth(request: CredRequest):
    if request.organization and request.secret:
        auth_res = authy.authenticate(
            request.organization,
            request.secret
        )
        return auth_res
    return (False, "Invalid request parameters.")

@app.get("/track/{url:path}", dependencies=[Depends(security)])
async def track(url: str, request: Request, org: str = Depends(verify_token)):
    query_string = request.url.query
    full_url = f"{url}?{query_string}" if query_string else url

    return {"tag": tracker.track(full_url, authy.find_org(org).id)}

@app.get("/stats/{tag}", dependencies=[Depends(security)])
async def get_stats(tag: str, org: str = Depends(verify_token)):
    return tracker.get_stats(tag, authy.find_org(org).id)

@app.get("/delete/{tag}")
async def delete(tag: str):
    tracker.delete(tag)
