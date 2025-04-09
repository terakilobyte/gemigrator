import random
import time
import google.generativeai as genai
from google.generativeai.types import Tool, FunctionDeclaration
from google.api_core import exceptions as google_api_exceptions
from pathlib import Path
import sys
import re
import logging

from config import load_api_key, MODEL_NAME

logger = logging.getLogger(__name__)


try:
    GOOGLE_API_KEY = load_api_key()
    genai.configure(api_key=GOOGLE_API_KEY)
    logger.info("Gemini API configured successfully.")
except ValueError as e:
    logger.critical(f"Configuration Error: {e}")
    sys.exit(1)
except Exception as e:
    logger.critical(f"Unexpected Error configuring Gemini API: {e}")
    sys.exit(1)

write_file_func = FunctionDeclaration(
    name="write_file",
    description="Writes or overwrites a file with the given content...",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "..."},
            "content": {"type": "string", "description": "..."},
            "reason": {"type": "string", "description": "..."},
        },
        "required": ["file_path", "content"],
    },
)
default_tools = Tool(function_declarations=[write_file_func])


def safe_write_file(
    output_dir: Path, relative_path: str, content: str, reason: str | None = None
):
    """Safely writes content to a file within the output directory."""

    if not relative_path or ".." in Path(relative_path).parts:
        logger.info(
            f"Error: Invalid or potentially unsafe file path requested: '{relative_path}'. Skipping write."
        )
        return False
    try:
        output_dir = output_dir.resolve(strict=True)
        target_file = output_dir.joinpath(relative_path).resolve()
        if not str(target_file).startswith(str(output_dir)):
            logger.info(
                f"Error: Attempted write outside designated output directory: '{relative_path}'. Skipping."
            )
            return False
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Successfully wrote file: {target_file}")
        if reason:
            logger.info(f"  Reason: {reason}")
        return True
    except FileNotFoundError:
        logger.info(
            f"Error: Output directory {output_dir} not found during file write."
        )
        return False
    except Exception as e:
        logger.info(f"Error writing file '{relative_path}': {e}")
        return False


def call_gemini_with_tools(
    prompt: str,
    output_dir: Path,
    model_name: str = MODEL_NAME,
    available_tools: Tool | None = default_tools,
    max_retries: int = 3,
    initial_delay: float = 1.0,
) -> str | None:
    """
    Sends prompt, handles function calls, includes fallback, uses logging,
    and implements retry logic for specific API errors.
    """
    logger.info(f"Asking Gemini ({model_name})...")
    logger.debug(f"Full Prompt:\n{prompt}")

    model = genai.GenerativeModel(model_name)
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            response = model.generate_content(
                prompt,
                tools=available_tools,
            )

            if not response.candidates:
                logger.error("No response candidates generated (potentially blocked).")
                logger.debug(f"Prompt Feedback: {response.prompt_feedback}")

                return "Error: No response generated."

            if response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                if part.function_call:

                    fc = part.function_call
                    logger.info(f"Gemini requested function call: {fc.name}")
                    args = {k: v for k, v in fc.args.items()}
                    logger.debug(f"Function call args: {args}")
                    if fc.name == "write_file":
                        if "file_path" in args and "content" in args:
                            safe_write_file(
                                output_dir,
                                args["file_path"],
                                args["content"],
                                args.get("reason"),
                            )
                            return None
                        else:
                            logger.error("Missing required args for 'write_file'.")
                            return (
                                "Error: Function call 'write_file' missing arguments."
                            )
                    else:
                        logger.warning(f"Received unhandled function call '{fc.name}'.")
                        return f"Received unhandled function call: {fc.name}"

                elif part.text:

                    raw_text = part.text
                    fallback_match = re.match(r"FallbackFilePath:\s*(.+)\n", raw_text)
                    if fallback_match:
                        fallback_path = fallback_match.group(1).strip()
                        fallback_content = (
                            raw_text.split("\n", 1)[1] if "\n" in raw_text else ""
                        )
                        logger.warning(
                            f"Fallback Detected: LLM provided text with path: {fallback_path}"
                        )
                        logger.info("Attempting fallback write...")
                        safe_write_file(
                            output_dir,
                            fallback_path,
                            fallback_content,
                            "[Fallback - Review Needed] LLM failed function call",
                        )
                        return None
                    else:
                        logger.info(
                            "Gemini Text Response received (No Function Call / Fallback)."
                        )
                        logger.info(
                            raw_text[:200] + ("..." if len(raw_text) > 200 else "")
                        )
                        logger.debug(f"Full Text Response:\n{raw_text}")
                        return raw_text

                else:
                    logger.error("Received an empty or unexpected response part.")
                    return "Error: Received an empty or unexpected response part."

            logger.error("Unexpected response structure (no parts?).")
            return "Error: Unexpected response structure."

        except (
            google_api_exceptions.InternalServerError,
            google_api_exceptions.ServiceUnavailable,
            google_api_exceptions.DeadlineExceeded,
            google_api_exceptions.ResourceExhausted,
        ) as e:
            last_exception = e
            if attempt < max_retries:
                delay = initial_delay * (2**attempt) + random.uniform(0, 0.5)
                logger.warning(
                    f"API Error: {e}. Retrying in {delay:.2f} seconds... (Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
            else:
                logger.error(f"API Error: {e}. Max retries exceeded.")
                break
        except Exception as e:

            last_exception = e
            logger.error(
                f"Unexpected Error interacting with Gemini API: {e}", exc_info=True
            )
            break

    logger.error(
        f"Failed to get successful response from Gemini after {max_retries + 1} attempts."
    )
    return f"Error: Failed after retries. Last error: {last_exception}"
