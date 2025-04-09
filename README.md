# AI-Assisted Java Migration Tool

This Python script leverages Large Language Models (specifically Google's Gemini API) and static analysis (`javalang`) to assist in migrating Java applications from one framework to another (e.g., Java EE/JBoss to Spring Boot), targeting MongoDB as the database.

**Disclaimer:** This is an *assistant* tool and a work-in-progress. It does not perform fully automatic migration. All generated code, configuration, and suggestions **require careful manual review, testing, and refinement** by a developer.

## Features

* **Source Project Scanning:** Analyzes the source project structure (`pom.xml`, common config files, source directories).
* **AI-Powered Analysis:** Uses the Gemini API to guess the source framework and identify potential migration challenges.
* **Initial Project Setup:** Generates suggestions for:
  * Basic `pom.xml` structure with core dependencies for the target framework (Spring Boot) and MongoDB.
  * Basic `application.yml` (or `.properties`) configuration for MongoDB connection.
* **Static Code Analysis:** Uses `javalang` to parse source Java files and extract structural context (package, imports, class structure, annotations). **(Work in progress)**
* **Iterative Code Translation:**
  * Categorizes source files (e.g., Models vs. Services/Other).
  * Translates non-test Java files in batches (Models first).
  * Sends source code and structural context to the Gemini API for translation to the target framework (e.g., JPA -> Spring Data MongoDB, EJB -> Spring Service).
  * Includes prompts for MongoDB schema recommendations (embedding vs. referencing, indexing) with comments in translated model files.
* **Function Calling:** Uses Gemini's function calling capability to write generated files (notes, pom.xml, config, translated source code) directly to the output directory.
* **Fallback Mechanism:** Attempts to save translated code even if the LLM fails to use the `write_file` function call correctly (marks these files for review).
* **Dependency Suggestion & Verification:** **(Work in progress)**
  * Analyzes imports in the *generated* translated code.
  * Asks the Gemini API to suggest additional Maven dependencies based on these imports.
  * Parses the suggestions and verifies them against the Maven Central Search API using `requests`.
  * Reports the verification status (OK, Not Found, Error) and latest version found.
* **Retry Logic:** Automatically retries calls to the Gemini API on specific transient errors (e.g., 500 Internal Server Error) with exponential backoff.
* **Logging:** Logs detailed information about the process to both the console and a file (`migration_run.log`) in the output directory. Configurable log level.

## Prerequisites

* **Python:** Version 3.12 or higher recommended.
* **`uv`:** This project uses `uv` for environment and package management. Install it if you haven't: [https://astral.sh/uv#installation](https://astral.sh/uv#installation)
* **Google Gemini API Key:** You need an API key for the Gemini API. Set it as an environment variable named `GEMINI_API_KEY`. Get one from Google AI Studio: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

## Installation & Setup

1. **Clone or Download:** Get the project files into a directory (e.g., `migration_tool`).

    ```bash
    # git clone <repository_url> # If using Git
    cd migration_tool
    ```

2. **Create Virtual Environment:** Use `uv` to create a virtual environment.

    ```bash
    uv venv
    ```

3. **Activate Environment:**
    * macOS/Linux: `source .venv/bin/activate`
    * Windows (Cmd): `.venv\Scripts\activate.bat`
    * Windows (PowerShell): `.venv\Scripts\Activate.ps1`
4. **Install Dependencies:**

    ```bash
    uv sync
    ```

5. **Set API Key:** Set the environment variable for your Gemini API Key.
    * macOS/Linux: `export GEMINI_API_KEY='YOUR_API_KEY'`
    * Windows (Cmd): `set GEMINI_API_KEY=YOUR_API_KEY`
    * Windows (PowerShell): `$env:GEMINI_API_KEY='YOUR_API_KEY'`

## Usage

Run the main script from the project directory, providing the required arguments:

```bash
uv run main.py \
  --source /path/to/your/source/java-project \
  --target-framework "Spring Boot" \
  --output ./migration_output \
  [--log-level DEBUG|INFO|WARNING|ERROR]
