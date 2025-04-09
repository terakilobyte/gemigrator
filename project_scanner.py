import os
from pathlib import Path
import javalang
from config import MAX_POM_READ_BYTES, MAX_CODE_READ_CHARS
import logging

logger = logging.getLogger(__name__)


def scan_project_directory(source_dir: Path) -> dict:
    """Scans the source directory. (Code unchanged from previous version)"""
    logger.info(f"\nScanning project directory: {source_dir}...")
    findings = {
        "files_found": [],
        "java_files": [],
        "directories_found": [],
        "potential_build_files": [],
        "potential_config_files": [],
        "src_main_java_exists": False,
        "pom_xml_content": None,
    }
    max_pom_read_bytes = MAX_POM_READ_BYTES

    if not source_dir.is_dir():
        logger.info(
            f"Error: Source directory '{source_dir}' not found or is not a directory."
        )
        raise FileNotFoundError(f"Source directory '{source_dir}' not found.")

    for item in source_dir.rglob("*"):
        if item.is_file():
            relative_path_str = str(item.relative_to(source_dir))
            findings["files_found"].append(relative_path_str)
            if item.name.endswith(".java"):
                findings["java_files"].append(relative_path_str)
            if item.name == "pom.xml":
                findings["potential_build_files"].append(relative_path_str)
                try:
                    with open(item, "r", encoding="utf-8", errors="ignore") as f:
                        findings["pom_xml_content"] = f.read(max_pom_read_bytes)
                        if len(findings["pom_xml_content"]) == max_pom_read_bytes:
                            findings["pom_xml_content"] += "\n... (file truncated)"
                except Exception as e:
                    logger.info(f"Warning: Could not read {item.name}: {e}")
            elif item.name == "build.gradle" or item.name == "build.gradle.kts":
                findings["potential_build_files"].append(relative_path_str)
            elif item.name in [
                "web.xml",
                "persistence.xml",
                "ejb-jar.xml",
                "beans.xml",
                "application.xml",
                "standalone.xml",
                "domain.xml",
            ]:
                findings["potential_config_files"].append(relative_path_str)
        elif item.is_dir():
            relative_dir = str(item.relative_to(source_dir))
            findings["directories_found"].append(relative_dir)
            src_java_path = os.path.join("src", "main", "java")
            src_kotlin_path = os.path.join("src", "main", "kotlin")
            if relative_dir.startswith(src_java_path) or relative_dir.startswith(
                src_kotlin_path
            ):
                findings["src_main_java_exists"] = True

    logger.info(
        f"Found {len(findings['files_found'])} files ({len(findings['java_files'])} Java files) and {len(findings['directories_found'])} directories."
    )
    if findings["potential_build_files"]:
        logger.info(f"Potential build files: {findings['potential_build_files']}")
    if findings["potential_config_files"]:
        logger.info(f"Potential config files: {findings['potential_config_files']}")
    if findings["src_main_java_exists"]:
        logger.info("Found src/main/java or src/main/kotlin structure.")
    return findings


def analyze_java_file(file_path: Path) -> dict | None:
    """
    Parses a single Java file using javalang and extracts basic structural info,
    including top-level type annotations.
    Returns a dictionary with info, or None if parsing fails.
    """
    logger.info(f"Analyzing Java file structure: {file_path.name}...")
    if not file_path.is_file():
        logger.info(f"Error: Java file not found: {file_path}")
        return None

    analysis_results = {
        "file_path": str(file_path),
        "package": None,
        "imports": [],
        "types": [],
    }

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        if len(content) > MAX_CODE_READ_CHARS * 2:
            logger.info(
                f"Warning: File {file_path.name} is very large, parsing might be slow."
            )

        tree = javalang.parse.parse(content)

        if tree.package:
            analysis_results["package"] = tree.package.name
        analysis_results["imports"] = [imp.path for imp in tree.imports]

        if tree.types:
            for type_decl in tree.types:
                annotations = []
                if type_decl.annotations:
                    annotations = [a.name for a in type_decl.annotations]

                type_info = {
                    "kind": type(type_decl).__name__,
                    "name": type_decl.name,
                    "annotations": annotations,
                    "extends": None,
                    "implements": [],
                }

                if hasattr(type_decl, "extends") and type_decl.extends:
                    if isinstance(type_decl.extends, list):
                        type_info["extends"] = [ext.name for ext in type_decl.extends]
                    elif type_decl.extends:

                        if hasattr(type_decl.extends, "name"):
                            type_info["extends"] = type_decl.extends.name
                        else:
                            type_info["extends"] = str(type_decl.extends)

                if hasattr(type_decl, "implements") and type_decl.implements:
                    type_info["implements"] = [
                        impl.name
                        for impl in type_decl.implements
                        if hasattr(impl, "name")
                    ]

                analysis_results["types"].append(type_info)

        type_names = [t["name"] for t in analysis_results["types"]]
        logger.info(f"  Found types: {', '.join(type_names) if type_names else 'None'}")
        for t in analysis_results["types"]:
            if t["annotations"]:
                logger.info(f"    Annotations on {t['name']}: {t['annotations']}")

        return analysis_results

    except FileNotFoundError:
        logger.info(f"Error: File not found during analysis: {file_path}")
        return None
    except javalang.tokenizer.LexerError as e:
        logger.info(
            f"Error: Lexer error parsing {file_path.name}: {e}. Skipping analysis."
        )
        return None
    except Exception as e:
        logger.info(
            f"Error: Failed to parse or analyze {file_path.name}: {e}. Skipping analysis."
        )
        return None


def extract_imports_from_file(file_path: Path) -> set[str]:
    """
    Parses a Java file and extracts the set of unique import statements.
    """
    imports = set()
    if not file_path.is_file():
        logger.info(f"Warning: Cannot extract imports, file not found: {file_path}")
        return imports

    logger.info(f"Extracting imports from: {file_path.name}...")
    try:

        content = file_path.read_text(encoding="utf-8", errors="ignore")

        if not content.strip():
            logger.info(
                f"Warning: File is empty, skipping import extraction: {file_path.name}"
            )
            return imports

        tree = javalang.parse.parse(content)
        if tree.imports:
            imports.update(imp.path for imp in tree.imports)
        logger.info(f"  Found {len(imports)} unique imports in this file.")
        return imports

    except FileNotFoundError:

        logger.info(f"Warning: File not found during import extraction: {file_path}")
        return imports
    except javalang.tokenizer.LexerError as e:
        logger.info(
            f"Warning: Lexer error parsing {file_path.name} for imports: {e}. Imports might be incomplete."
        )

        return set()
    except Exception as e:

        logger.info(
            f"Warning: Failed to parse {file_path.name} for imports: {e}. Imports might be incomplete."
        )
        return set()
