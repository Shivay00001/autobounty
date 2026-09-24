"""FastAPI service: honest scoped web security scanning. POST /scan."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from scanner import scan

app = FastAPI(title="autobounty", version="2.0.0")


class ScanRequest(BaseModel):
    target: str  # hostname only, e.g. "example.com"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/scan")
def run_scan(req: ScanRequest):
    if not req.target or any(c in req.target for c in " /:@"):
        raise HTTPException(
            status_code=400, detail="target must be a bare hostname, e.g. example.com"
        )
    try:
        return scan(req.target)
    except Exception as e:  # never leak tracebacks as fake findings
        raise HTTPException(status_code=502, detail=f"scan failed: {type(e).__name__}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8005)
