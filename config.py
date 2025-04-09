import os

MODEL_NAME = "gemini-2.5-pro-preview-03-25"
MAX_POM_READ_BYTES = 1024 * 5
MAX_CODE_READ_CHARS = 25000


def load_api_key():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    return api_key
