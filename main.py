import argparse
import sys
from pathlib import Path
import time
import re
import logging

from config import MAX_CODE_READ_CHARS
from project_scanner import (
    scan_project_directory,
    analyze_java_file,
    extract_imports_from_file,
)
from llm_interaction import call_gemini_with_tools
from dependency_verifier import parse_dependency_snippet, verify_maven_dependency
from prompts import (
    generate_initial_analysis_prompt,
    generate_dependencies_prompt,
    generate_config_prompt,
    generate_translation_prompt,
    generate_dependency_suggestions_prompt,
)

from logging_config import setup_logging, LOG_FILE_NAME

LLM_CALL_DELAY_SECONDS = 2
MODEL_ANNOTATIONS = {"Entity", "Embeddable", "MappedSuperclass", "Document"}
SERVICE_ANNOTATIONS = {
    "Stateless",
    "Stateful",
    "Service",
    "Component",
    "RequestScoped",
    "ApplicationScoped",
    "Controller",
    "RestController",
    "Model",
}
REST_ANNOTATIONS = {"Path"}

logger = logging.getLogger(__name__)


def categorize_file(analysis: dict | None) -> str:
    """Categorizes file based on annotations."""
    if not analysis or not analysis.get("types"):
        return "unknown"
    all_annotations = set()
    for type_info in analysis["types"]:
        all_annotations.update(type_info.get("annotations", []))
    if MODEL_ANNOTATIONS.intersection(all_annotations):
        return "model"
    if SERVICE_ANNOTATIONS.intersection(all_annotations):
        return "service"
    if REST_ANNOTATIONS.intersection(all_annotations):
        return "rest"
    return "other"


def main():
    parser = argparse.ArgumentParser(
        description="AI Assistant for migrating Java apps (V9 - Integrated Logging).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--source", required=True, help="Path to the source Java project directory."
    )
    parser.add_argument(
        "--target-framework",
        required=True,
        help="Target Java framework (e.g., 'Spring Boot').",
    )
    parser.add_argument(
        "--output", required=True, help="Output directory for generated files and logs."
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level.",
    )
    args = parser.parse_args()

    source_dir = Path(args.source).resolve()
    target_framework = args.target_framework
    output_dir = Path(args.output).resolve()
    log_level_str = args.log_level.upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    try:
        setup_logging(output_dir, level=log_level)
    except Exception as e:
        print(f"CRITICAL: Failed to set up logging: {e}", file=sys.stderr)
        sys.exit(1)

    logger.info("--- Starting Migration Assistance ---")
    logger.info(f"Source: {source_dir}")
    logger.info(f"Target Framework: {target_framework}")
    logger.info("Target Database: MongoDB")
    logger.info(f"Output Directory: {output_dir}")
    logger.info(f"Log Level: {log_level_str}")

    source_framework_guess = "Unknown"

    try:
        project_scan_results = scan_project_directory(source_dir)
    except FileNotFoundError as e:
        logger.error(e)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during project scanning: {e}", exc_info=True)
        sys.exit(1)

    prompt1 = generate_initial_analysis_prompt(project_scan_results, target_framework)
    logger.info("--- Task: Initial Analysis & Notes ---")
    response1 = call_gemini_with_tools(prompt1, output_dir)
    if response1:
        source_framework_guess = response1
        logger.info("[Info] LLM returned text for initial analysis (check log/file).")
    time.sleep(LLM_CALL_DELAY_SECONDS)

    prompt2 = generate_dependencies_prompt(target_framework)
    logger.info("--- Task: Generate Dependencies & pom.xml ---")
    _ = call_gemini_with_tools(prompt2, output_dir)
    time.sleep(LLM_CALL_DELAY_SECONDS)

    prompt3 = generate_config_prompt(target_framework)
    logger.info("--- Task: Generate Configuration File ---")
    _ = call_gemini_with_tools(prompt3, output_dir)
    time.sleep(LLM_CALL_DELAY_SECONDS)

    logger.info("--- Task: Analyzing, Categorizing & Translating Source Files ---")
    files_to_process = {}
    model_files, service_files, rest_files, other_files = [], [], [], []
    skipped_files_count, failed_analysis_count = 0, 0

    java_files_to_scan = project_scan_results.get("java_files", [])
    if not java_files_to_scan:
        logger.info("No Java files found in the source directory scan results.")
    else:
        logger.info(
            f"Found {len(java_files_to_scan)} Java files to potentially analyze."
        )
        for file_rel_path in java_files_to_scan:
            normalized_path = Path(file_rel_path).as_posix()
            if normalized_path.startswith("src/test/"):
                logger.info(f"Skipping test file: {file_rel_path}")
                skipped_files_count += 1
                continue

            logger.info(f"-- Analyzing: {file_rel_path} --")
            source_file_path = source_dir / file_rel_path
            if not source_file_path.is_file():
                logger.warning(f"Path invalid: {source_file_path}. Skipping.")
                skipped_files_count += 1
                continue

            analysis = analyze_java_file(source_file_path)
            files_to_process[file_rel_path] = analysis

            if not analysis:
                failed_analysis_count += 1
                continue

            category = categorize_file(analysis)
            logger.info(f"  Categorized as: {category}")

            if category == "model":
                model_files.append(file_rel_path)
            elif category == "service":
                service_files.append(file_rel_path)
            elif category == "rest":
                rest_files.append(file_rel_path)
            else:
                other_files.append(file_rel_path)

        all_batches = [
            ("Models", model_files, True),
            ("App Logic & Others", service_files + rest_files + other_files, False),
        ]
        total_translation_attempts = 0

        for batch_name, batch_files, is_model_batch in all_batches:
            logger.info(
                f"--- Processing Batch: {batch_name} ({len(batch_files)} files) ---"
            )
            for file_rel_path in batch_files:
                logger.info(f"-- Translating {batch_name[:-1]}: {file_rel_path} --")
                analysis = files_to_process[file_rel_path]
                source_file_path = source_dir / file_rel_path
                try:
                    source_code = source_file_path.read_text(encoding="utf-8")
                    if len(source_code) > MAX_CODE_READ_CHARS:
                        logger.warning(
                            f"Source file '{file_rel_path}' is long, truncating for prompt."
                        )
                        source_code = (
                            source_code[:MAX_CODE_READ_CHARS] + "\n... (code truncated)"
                        )

                    translate_prompt = generate_translation_prompt(
                        target_framework=target_framework,
                        source_file_rel_path=file_rel_path,
                        source_code=source_code,
                        source_analysis=analysis,
                        source_framework_guess=source_framework_guess,
                        is_model_file=is_model_batch,
                    )
                    call_gemini_with_tools(translate_prompt, output_dir)
                    total_translation_attempts += 1

                    time.sleep(LLM_CALL_DELAY_SECONDS)
                except Exception as e:
                    logger.error(
                        f"Error processing file '{file_rel_path}': {e}", exc_info=True
                    )

    logger.info("--- Task: Analyzing Imports in Generated Output Files ---")
    all_imports = set()
    generated_java_files = list(output_dir.rglob("*.java"))

    logger.info(
        f"Found {len(generated_java_files)} .java files in output directory to analyze for imports."
    )
    for gen_file_path in generated_java_files:
        imports_in_file = extract_imports_from_file(gen_file_path)
        all_imports.update(imports_in_file)

    if not all_imports:
        logger.info("No imports found in generated files to suggest dependencies for.")
    else:
        logger.info(
            f"--- Task: Suggesting Additional Dependencies Based on {len(all_imports)} Unique Imports ---"
        )
        dep_suggestion_prompt = generate_dependency_suggestions_prompt(all_imports)
        dependency_suggestions = call_gemini_with_tools(
            dep_suggestion_prompt, output_dir, available_tools=None
        )

        if not dependency_suggestions or dependency_suggestions.startswith("Error:"):
            logger.error("Could not get dependency suggestions from LLM.")
        else:
            logger.info("--- LLM Dependency Suggestions ---")
            logger.debug(f"Raw dependency suggestions:\n{dependency_suggestions}")

            logger.info("--- Verifying Suggested Dependencies via Maven Central ---")
            suggested_snippets = re.findall(
                r"<dependency>.*?</dependency>", dependency_suggestions, re.DOTALL
            )

            if not suggested_snippets:
                logger.info("No parsable <dependency> blocks found in the suggestions.")
            else:
                logger.info(
                    f"Found {len(suggested_snippets)} suggested dependency blocks to verify."
                )
                for snippet in suggested_snippets:
                    parsed_dep = parse_dependency_snippet(snippet)
                    if (
                        parsed_dep
                        and parsed_dep["group_id"]
                        and parsed_dep["artifact_id"]
                    ):
                        verification = verify_maven_dependency(parsed_dep)
                        details = verification["error"] or ""
                        if verification["exists"]:
                            details = f"Latest: {verification['latest_version']}"
                            if verification["requested_version"]:
                                details += (
                                    f" (Requested: {verification['requested_version']})"
                                )
                        elif not verification["error"]:
                            logger.info(
                                f"Dependency '{parsed_dep['group_id']}:{parsed_dep['artifact_id']}' not found."
                            )

                    else:
                        logger.warning(
                            f"Could not parse suggestion snippet: {snippet[:100]}..."
                        )
                    time.sleep(0.5)

    logger.info("--- Migration Assistance Script Finished ---")
    logger.info(
        f"Attempted translation for {total_translation_attempts} non-test source files."
    )
    logger.info(f"Skipped {skipped_files_count} files (test files or path errors).")
    logger.info(f"Failed analysis for {failed_analysis_count} files.")
    logger.info(
        f"Check the '{output_dir}' directory for generated files and '{LOG_FILE_NAME}'."
    )
    logger.info("  Files written via fallback may need extra review (check log file).")
    logger.info("IMPORTANT: Review the verified dependency suggestions above.")
    logger.info(
        "  Manually add any necessary and valid dependencies to your `pom.xml`."
    )
    logger.info("Remember to manually review ALL generated files.")


if __name__ == "__main__":
    main()
