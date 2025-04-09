import requests
import re
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)

MAVEN_SEARCH_URL = "https://search.maven.org/solrsearch/select"


def parse_dependency_snippet(snippet: str) -> dict | None:
    """Parses a Maven <dependency> XML snippet."""
    try:
        root = ET.fromstring(f"<root>{snippet}</root>")
        dep = root.find("dependency")
        if dep is None:
            return None
        group_id_elem = dep.find("groupId")
        artifact_id_elem = dep.find("artifactId")
        version_elem = dep.find("version")
        if group_id_elem is None or artifact_id_elem is None:
            return None
        return {
            "group_id": group_id_elem.text.strip() if group_id_elem.text else None,
            "artifact_id": (
                artifact_id_elem.text.strip() if artifact_id_elem.text else None
            ),
            "version": (
                version_elem.text.strip()
                if version_elem is not None and version_elem.text
                else None
            ),
            "snippet": snippet,
        }
    except ET.ParseError:
        logger.warning(
            f"XML parse failed for snippet, falling back to regex: {snippet[:50]}..."
        )
        dep_match = re.search(
            r"<groupId>(.*?)</groupId>\s*<artifactId>(.*?)</artifactId>\s*(?:<version>(.*?)</version>)?",
            snippet,
            re.DOTALL | re.IGNORECASE,
        )
        if dep_match:
            group_id, artifact_id, version = dep_match.groups()
            return {
                "group_id": group_id.strip() if group_id else None,
                "artifact_id": artifact_id.strip() if artifact_id else None,
                "version": version.strip() if version else None,
                "snippet": snippet,
            }
        return None
    except Exception as e:
        logger.error(f"Error parsing dependency snippet: {e}")
        return None


def verify_maven_dependency(dep_info: dict) -> dict:
    """Verifies a parsed dependency against Maven Central Search API."""
    verification_result = {
        "suggestion": dep_info["snippet"],
        "group_id": dep_info["group_id"],
        "artifact_id": dep_info["artifact_id"],
        "requested_version": dep_info["version"],
        "exists": False,
        "latest_version": None,
        "error": None,
    }

    if not dep_info["group_id"] or not dep_info["artifact_id"]:
        verification_result["error"] = "Missing groupId or artifactId"
        logger.warning(
            f"Skipping verification, missing groupId/artifactId in: {dep_info['snippet'][:50]}..."
        )
        return verification_result

    query = f'g:"{dep_info["group_id"]}" AND a:"{dep_info["artifact_id"]}"'
    params = {"q": query, "core": "gav", "rows": "1", "wt": "json"}
    logger.debug(f"Querying Maven Central: {params}")

    try:
        response = requests.get(MAVEN_SEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data["response"]["numFound"] > 0:
            verification_result["exists"] = True
            latest_version = data["response"]["docs"][0].get("v")
            verification_result["latest_version"] = latest_version
        else:
            verification_result["exists"] = False

    except requests.exceptions.Timeout:
        verification_result["error"] = "Timeout connecting to Maven Central"
        logger.warning(
            f"Timeout verifying {dep_info['group_id']}:{dep_info['artifact_id']}"
        )
    except requests.exceptions.RequestException as e:
        verification_result["error"] = "Maven Central API request failed"
        logger.warning(
            f"API Error verifying {dep_info['group_id']}:{dep_info['artifact_id']}: {e}"
        )
    except Exception as e:
        verification_result["error"] = "Failed to process Maven Central response"
        logger.error(
            f"Error parsing Maven response for {dep_info['group_id']}:{dep_info['artifact_id']}: {e}",
            exc_info=True,
        )

    return verification_result
