"""
Generic Gemini LLM caller.

Usage
-----
    from apps.core.llm import call_llm

    result = call_llm("Write a short bio for a 25-year-old who loves hiking.")

Configuration
-------------
Set GEMINI_API_KEY in .env.
Model defaults to gemini-2.0-flash but can be overridden via GEMINI_MODEL in .env.
"""

import os

import google.generativeai as genai
from django.conf import settings


def _get_model():
    api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
    return genai.GenerativeModel(model_name)


def call_llm(prompt: str) -> str:
    """
    Send a prompt to Gemini and return the text response.

    Parameters
    ----------
    prompt : str — the full prompt to send

    Returns
    -------
    str — the model's text response, stripped of leading/trailing whitespace

    Raises
    ------
    RuntimeError — if GEMINI_API_KEY is not set
    Exception    — propagates any API errors to the caller
    """
    model = _get_model()
    response = model.generate_content(prompt)
    return response.text.strip()
