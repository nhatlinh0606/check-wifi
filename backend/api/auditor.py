"""
API: Security Auditor Endpoints
Provides offline password strength evaluation, WPA2/WPA3 password generation,
wordlist quality analysis, and mathematical search-space simulation.
Strictly offline and non-intrusive.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel, Field

from backend.services.auditor_service import AuditorService

router = APIRouter(prefix="/api/auditor", tags=["Security Auditor"])


class AnalyzePasswordRequest(BaseModel):
    password: str = Field(..., max_length=256)


class GeneratePasswordRequest(BaseModel):
    length: int = Field(default=16, ge=8, le=63)
    include_upper: bool = True
    include_lower: bool = True
    include_digits: bool = True
    include_symbols: bool = True
    exclude_ambiguous: bool = True


class SimulateSpaceRequest(BaseModel):
    charset_type: str = "alphanumeric"  # numeric, alpha_lower, alpha_mixed, alphanumeric, ascii_printable
    length: int = Field(default=8, ge=1, le=63)
    custom_pool_size: Optional[int] = None
    attempts_per_sec: float = Field(default=1000.0, gt=0)


class WordlistTextRequest(BaseModel):
    text: str = Field(..., max_length=10_000_000)


@router.post("/analyze-password")
def analyze_password(req: AnalyzePasswordRequest) -> Dict[str, Any]:
    """Analyzes a password for entropy, weak patterns, and theoretical crack times."""
    return AuditorService.evaluate_password(req.password)


@router.post("/generate-password")
def generate_password(req: GeneratePasswordRequest) -> Dict[str, Any]:
    """Generates a cryptographically strong random WPA2/WPA3 password."""
    pwd = AuditorService.generate_password(
        length=req.length,
        include_upper=req.include_upper,
        include_lower=req.include_lower,
        include_digits=req.include_digits,
        include_symbols=req.include_symbols,
        exclude_ambiguous=req.exclude_ambiguous,
    )
    analysis = AuditorService.evaluate_password(pwd)
    return {"password": pwd, "analysis": analysis}


@router.post("/analyze-wordlist")
async def analyze_wordlist_upload(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Uploads a TXT wordlist file to audit duplicate rates, weak patterns, and length distributions."""
    if not file.filename.endswith((".txt", ".lst", ".wordlist", ".dic")):
        raise HTTPException(status_code=400, detail="Only plain text wordlist files (.txt) are supported.")

    try:
        content_bytes = await file.read()
        text = content_bytes.decode("utf-8", errors="ignore")
        return AuditorService.analyze_wordlist_text(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process wordlist: {e}")


@router.post("/analyze-wordlist-text")
def analyze_wordlist_raw_text(req: WordlistTextRequest) -> Dict[str, Any]:
    """Analyzes raw wordlist text directly."""
    return AuditorService.analyze_wordlist_text(req.text)


@router.post("/simulate-search-space")
def simulate_search_space(req: SimulateSpaceRequest) -> Dict[str, Any]:
    """Simulates mathematical theoretical search space and duration."""
    return AuditorService.simulate_search_space(
        charset_type=req.charset_type,
        length=req.length,
        custom_pool_size=req.custom_pool_size,
        attempts_per_sec=req.attempts_per_sec,
    )
