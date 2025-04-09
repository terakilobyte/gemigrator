def generate_initial_analysis_prompt(scan_results: dict, target_framework: str) -> str:
    """Generates the prompt for initial project analysis and challenges."""
    context = f"""
Analyze the structure of a Java project. Key findings during scan:
- Potential build files found: {scan_results['potential_build_files']}
- Potential config files found: {scan_results['potential_config_files']}
- Java source structure exists: {scan_results['src_main_java_exists']}
- Java files count: {len(scan_results['java_files'])}
"""
    if scan_results.get("pom_xml_content"):
        context += f"\n- Start of pom.xml content:\n```xml\n{scan_results['pom_xml_content']}\n```\n"

    prompt = f"""{context}
TASK:
1. Based on these findings, what is the most likely original Java framework or primary technology stack? Briefly explain your reasoning in text.
2. Identify 2-3 key challenges or areas to focus on when migrating this type of project to '{target_framework}' with MongoDB.

CRITICAL INSTRUCTION: You MUST use the 'write_file' function to save your complete analysis (points 1 and 2 combined) into a markdown file named 'migration_analysis_notes.md'. Use the analysis summary as the 'reason'. Do NOT output the analysis as plain text in your response.
"""
    return prompt


def generate_dependencies_prompt(target_framework: str) -> str:
    """Generates the prompt for suggesting dependencies and writing pom.xml."""
    prompt = f"""
TASK: Generate the necessary Maven dependencies (as XML snippets) for a new project using '{target_framework}'.
The project needs to:
1. Build a web application (RESTful APIs).
2. Connect to and interact with a MongoDB database (e.g., using Spring Data MongoDB if target is Spring Boot, or equivalent idiomatic choices).
3. Include standard {target_framework} core functionalities.

CRITICAL INSTRUCTION: You MUST use the 'write_file' function to create a basic 'pom.xml' file in the output directory. This pom.xml should include a standard parent/structure (if applicable for {target_framework}) and incorporate the generated dependencies. If unsure about the full structure, provide the dependencies wrapped in `<dependencies>...</dependencies>` tags within the file content. Reason should be 'Generated initial pom.xml'. Do NOT output the pom.xml content as plain text in your response.
"""
    return prompt


def generate_config_prompt(target_framework: str) -> str:
    """Generates the prompt for suggesting MongoDB configuration."""
    config_file_name = "application.properties"
    config_format = "properties"
    if "spring boot" in target_framework.lower():
        config_file_name = "application.yml"
        config_format = "YAML"
    elif "quarkus" in target_framework.lower():
        config_file_name = "application.properties"
        config_format = "properties"

    prompt = f"""
TASK: Generate a basic configuration snippet for a '{target_framework}' application to connect to a MongoDB database.
Assume:
- MongoDB is running on localhost:27017.
- The database name is 'migrated_db'.
- Include standard properties for connection, including placeholders or comments for username/password.

Format the configuration correctly for '{config_file_name}' (use {config_format} format).

CRITICAL INSTRUCTION: You MUST use the 'write_file' function to save this configuration into a file named 'src/main/resources/{config_file_name}' within the output directory. Ensure the path includes 'src/main/resources/'. Reason should be 'Generated MongoDB configuration'. Do NOT output the configuration as plain text in your response.
"""
    return prompt


def generate_translation_prompt(
    target_framework: str,
    source_file_rel_path: str,
    source_code: str,
    source_analysis: dict | None,
    source_framework_guess: str = "Java EE / Unknown",
    is_model_file: bool = False,
) -> str:
    """Generates the prompt for translating a specific Java file.
    Includes schema recommendations for model files and fallback instruction.
    """

    analysis_context = "No structural analysis available for source file."
    if source_analysis:
        type_summaries = []
        for t in source_analysis.get("types", []):
            summary = f"  - {t.get('kind', 'N/A')} {t.get('name', 'N/A')}"
            extends_info = t.get("extends")
            if extends_info:
                extends_str = (
                    ", ".join(extends_info)
                    if isinstance(extends_info, list)
                    else extends_info
                )
                summary += f" extends {extends_str}"
            implements_info = t.get("implements")
            if implements_info:
                summary += f" implements {', '.join(implements_info)}"
            type_summaries.append(summary)
        analysis_context = f"""
Source File Structural Analysis ({source_analysis.get('file_path', source_file_rel_path)}):
- Package: {source_analysis.get('package', 'N/A')}
- Imports Count: {len(source_analysis.get('imports', []))}
- Detected Types:
{chr(10).join(type_summaries) if type_summaries else '    None'}"""

    schema_instructions = ""
    if is_model_file:
        schema_instructions = """
   - SCHEMA RECOMMENDATIONS (Add as JavaDoc comments in the translated code):
     - Based on typical usage patterns for such an entity, explicitly recommend whether related data (if any were implied by relationships like @OneToMany, @ManyToMany in the source) should generally be EMBEDDED within this document or REFERENCED (linking via IDs). Briefly explain the trade-offs (e.g., query performance vs. data duplication).
     - Suggest appropriate @Indexed annotations on fields commonly used for filtering or sorting to optimize query performance, beyond the primary @Id. Explain why these indexes are suggested.
"""

    prompt = f"""
CONTEXT:
- Source Project Framework (estimated): {source_framework_guess}
- Target Project Framework: {target_framework}
- Target Database: MongoDB
- Source File Relative Path: {source_file_rel_path}
{analysis_context}

SOURCE CODE to translate:
```java
{source_code}
TASK:

Analyze the source code. What is its likely role (e.g., JPA Entity, EJB Service Bean, Servlet, Utility class)? Use this analysis as the 'reason' argument later.
Translate this Java code to be idiomatic for the '{target_framework}' framework using MongoDB.
If it's a JPA Entity (or similar data object), convert it to a Spring Data MongoDB Document (@Document class if target is Spring Boot), mapping annotations (like @Id, @Column, @Transient, relationship annotations - explain how you handle relationships) and types appropriately. Add necessary MongoDB/Spring Data annotations. {schema_instructions}
If it's an EJB or similar service/component, convert it to a Spring Bean (@Service, @Component, etc.) using constructor injection or @Autowired for dependencies. Replace Java EE specific APIs with {target_framework} equivalents.
Adjust imports and package declarations as needed. Assume a base target package like 'com.migratedapp' + subpackages (e.g., .model, .service, .controller). Preserve the original class name unless translation implies a change (e.g., Customer -> CustomerDocument).
Add JavaDoc comments explaining significant changes, assumptions made, or areas needing manual review (especially for complex logic or unsupported annotations).
Determine a suitable relative path and filename for the translated file within a standard '{target_framework}' project structure (e.g., 'src/main/java/com/migratedapp/model/TranslatedEntity.java').
CRITICAL INSTRUCTION: You MUST use the 'write_file' function to save the complete translated Java code (including package declaration and imports) to the path determined in step 3. Provide the role analysis from step 1 as the 'reason' argument. Do NOT output the translated code as plain text in your response.

FALLBACK INSTRUCTION: If, for some reason, you absolutely cannot use the 'write_file' function call, then start your response immediately with a single line exactly like this:
FallbackFilePath: [intended relative output path, e.g., src/main/java/com/migratedapp/model/MyModel.java]
Followed by a newline, and then the complete translated code block.
"""

    return prompt


def generate_dependency_suggestions_prompt(imports: set[str]) -> str:
    """
    Generates a prompt asking LLM to suggest Maven dependencies based on imports.
    """
    import_list = "\n".join(sorted(list(imports)))

    prompt = f"""
CONTEXT:
The following Java import statements were found in the automatically translated source code of a project being migrated to Spring Boot and MongoDB:

{import_list}


TASK:
Based *only* on these import statements, suggest potential additional Maven dependencies that might be required, beyond the standard Spring Boot starters like 'spring-boot-starter-web' and 'spring-boot-starter-data-mongodb' (which are assumed to be present already).

Provide your suggestions as XML `<dependency>...</dependency>` blocks.
- For common libraries (e.g., Apache Commons, Guava, Jackson, testing libraries like JUnit 5, Mockito), provide standard coordinates.
- For dependencies typically managed by the Spring Boot BOM (Bill of Materials), OMIT the `<version>` tag (e.g., for Spring Cloud, Spring Security, etc.).
- If you are unsure about a specific dependency for a less common import, you can state that.
- Do NOT include dependencies that are already covered by `spring-boot-starter-web` or `spring-boot-starter-data-mongodb`.

Format your response clearly, listing each suggested dependency block. If no *additional* dependencies seem necessary based *only* on these imports, state that clearly.
"""
    return prompt
