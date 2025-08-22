#!/usr/bin/env python3
"""
Reduct Server - HTTP API for text reduction using LLMs
"""

import os
import sys
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our reduct functions
from reduct import transform_content

app = FastAPI(title="Reduct Server", version="1.0.0")

# Configure CORS to allow requests from Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, be more specific
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReductionRequest(BaseModel):
    text: str
    reduction_level: int = 50
    prompt: Optional[str] = None


class ReductionResponse(BaseModel):
    reduced_text: str
    original_length: int
    reduced_length: int
    reduction_percentage: float


@app.get("/health")
async def health_check():
    """Check if the server is running and LLM is configured."""
    llm_model = os.getenv("LLM_MODEL")
    llm_key = os.getenv("LLM_KEY")

    if not llm_model:
        return {
            "status": "unhealthy",
            "error": "LLM_MODEL environment variable not set",
        }

    if not llm_key:
        # Check for provider-specific keys
        if llm_model.startswith("anthropic/") and not os.getenv("ANTHROPIC_API_KEY"):
            return {
                "status": "unhealthy",
                "error": "LLM_KEY or ANTHROPIC_API_KEY not set",
            }
        elif llm_model.startswith("openai/") and not os.getenv("OPENAI_API_KEY"):
            return {"status": "unhealthy", "error": "LLM_KEY or OPENAI_API_KEY not set"}

    return {"status": "healthy", "model": llm_model}


@app.post("/reduce", response_model=ReductionResponse)
async def reduce_text(request: ReductionRequest):
    """Reduce text content using LLM."""
    try:
        # Use custom prompt if provided, otherwise use default
        if request.prompt:
            # Replace any remaining {REDUCT_FACTOR} placeholders in custom prompts
            prompt = request.prompt.replace(
                "{REDUCT_FACTOR}", str(request.reduction_level)
            )
        else:
            prompt = (
                f"Reduce this text to approximately {request.reduction_level}% "
                f"of its original length. Remove filler, redundancy, and verbose "
                f"explanations while retaining all meaningful semantic content, "
                f"key points, and factual information. Maintain the original tone "
                f"and style. Output as clean HTML using these tags: <p>, <ul>, <ol>, "
                f"<li>, <strong>, <em>, <h3>, <blockquote>, <details>, <summary>. "
                f"Use <details><summary>Title</summary>content</details> for less "
                f"important information. IMPORTANT: Output ONLY the HTML without any "
                f"introduction, wrapper tags, or commentary."
            )

        # Log the prompt being sent
        print("\n[REDUCT SERVER] Sending prompt to LLM:", file=sys.stderr)
        print(f"{'=' * 60}", file=sys.stderr)
        print(prompt, file=sys.stderr)
        print(f"{'=' * 60}\n", file=sys.stderr)

        # Call the transform_content function from reduct
        reduced_text = transform_content(request.text, prompt)

        # Calculate statistics
        original_length = len(request.text.split())
        reduced_length = len(reduced_text.split())
        actual_reduction = (
            round((1 - reduced_length / original_length) * 100, 1)
            if original_length > 0
            else 0
        )

        return ReductionResponse(
            reduced_text=reduced_text,
            original_length=original_length,
            reduced_length=reduced_length,
            reduction_percentage=actual_reduction,
        )

    except Exception as e:
        print(f"Error in reduce_text: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Run the server."""
    # Check for required environment variables
    if not os.getenv("LLM_MODEL"):
        print("Error: LLM_MODEL environment variable not set", file=sys.stderr)
        print(
            "Example: export LLM_MODEL=anthropic/claude-3-haiku-20240307",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Starting Reduct server on http://localhost:8000", file=sys.stderr)
    print(f"Using model: {os.getenv('LLM_MODEL')}", file=sys.stderr)

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
