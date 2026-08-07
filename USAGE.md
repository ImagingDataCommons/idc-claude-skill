# Usage Instructions

This document provides technical instructions for integrating the Imaging Data Commons skill into your AI assistant environment. The skill is not specific to any single vendor: it follows the open [Agent Skills](https://agentskills.io/) format, so it works with any agent that supports that format, and its content can be loaded as plain Markdown into any other assistant.

## Quick Install for Coding Agents (Recommended)

The simplest way to install this skill is with the [Skills.sh](https://skills.sh/) framework:

```bash
npx skills add ImagingDataCommons/imaging-data-commons-skill
```

This command automatically detects the AI agents installed on your system (Claude Code, Codex, Cursor, Gemini CLI, and others) and offers to install the skill across all of them, making it available system-wide. Once installed, invoke with `/imaging-data-commons` or let your AI assistant auto-detect based on questions about IDC.

## Claude.ai Web Interface

### Install the skill

1. Download the latest release ZIP from the [Releases page](https://github.com/ImagingDataCommons/imaging-data-commons-skill/releases/latest)
2. Open Claude Customize settings https://claude.ai/customize, select "Skills" and upload the `imaging-data-commons` skill ZIP file.
   - <img width="871" height="292" alt="2026-05-18_12-37-57" src="https://github.com/user-attachments/assets/e12a94dc-6d7f-402f-a7e6-b1c6b9cf869d" />

This gives Claude the complete skill with all the reference guides in one upload.

### Configure settings

1. Go to **Settings > Capabilities** in Claude.ai
2. Under **Code execution and file creation**:
   - Enable "Allow network egress" so that Claude can install `idc-index` package and its components
   - Under "Domain whitelist" select "Package managers only" so that `idc-index` package can be pulled from PyPI
3. Under **Additional allowed domains** add the following:
     * `*.github.com` and `*.githubusercontent.com`: used to access source code and release artifacts
     * `*.googleapis.com`: used to fetch IDC data from Google Storage buckets
     * `*.s3.amazonaws.com`: used to fetch IDC data from Amazon S3 buckets
     * `api.imaging.datacommons.cancer.gov`: used for the IDC REST API and MCP server (optional — only if you want the skill to query IDC over HTTP)

<img width="899" height="648" alt="image" src="https://github.com/user-attachments/assets/5bcb2d6f-9b9b-4c9e-955f-839cb4a98ca3" />


## Claude Desktop Setup

Claude Desktop works the same as the Claude.ai web interface. Follow the [Claude.ai Web Interface](#claudeai-web-interface) instructions above to upload the ZIP and configure Settings > Capabilities.

For persistent access across conversations, create a **Project** in Claude Desktop, upload the ZIP to the project's knowledge base, and configure the allowed domains in the project's Capabilities settings.

### Verifying the Skill is Loaded

Ask Claude: "What do you know about the Imaging Data Commons?"

Claude should respond with specific information about IDC, the `idc-index` package, and how to query and download cancer imaging data.

## Claude Code Setup

If you're using [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (the CLI tool), the `npx skills add` command above is the easiest option. Alternatively, install manually as described below. Other agents that support the Agent Skills format work the same way — just substitute their skills directory (e.g. `~/.claude/skills/` becomes the equivalent location for your agent).

### Option 1: Install as Personal Skill

Link or copy the skill to your personal skills directory. This makes it available across all projects:

```bash
# Create a symlink (keeps skill updated with repo)
ln -s /path/to/imaging-data-commons-skill ~/.claude/skills/imaging-data-commons

# Or copy the entire directory
cp -r /path/to/imaging-data-commons-skill ~/.claude/skills/imaging-data-commons
```

Once installed, invoke with `/imaging-data-commons` or let Claude auto-detect based on your questions about IDC.

### Option 2: Install as Project Skill

For project-specific use, link to your project's `.claude/skills/` directory:

```bash
mkdir -p /path/to/your-project/.claude/skills
ln -s /path/to/imaging-data-commons-skill /path/to/your-project/.claude/skills/imaging-data-commons
```

This makes the skill available only when working in that project.

### Option 3: Import During Session

For one-time use without permanent installation, ask your assistant to read the skill file at the start of your session:

```
Please read /path/to/imaging-data-commons-skill/SKILL.md and use it for IDC queries.
```

Ask your assistant to load reference guides as needed for specific topics:

```
Please also read /path/to/imaging-data-commons-skill/references/bigquery_guide.md      # BigQuery advanced queries
Please also read /path/to/imaging-data-commons-skill/references/dicomweb_guide.md      # DICOMweb API access
Please also read /path/to/imaging-data-commons-skill/references/index_tables_guide.md  # Table schemas and join columns
Please also read /path/to/imaging-data-commons-skill/references/sql_patterns.md        # Quick-reference SQL patterns
Please also read /path/to/imaging-data-commons-skill/references/use_cases.md           # End-to-end workflow examples
Please also read /path/to/imaging-data-commons-skill/references/digital_pathology_guide.md  # Pathology (SM, ANN, SEG)
Please also read /path/to/imaging-data-commons-skill/references/clinical_data_guide.md # Clinical/tabular data
Please also read /path/to/imaging-data-commons-skill/references/cloud_storage_guide.md # Direct GCS/S3 access
Please also read /path/to/imaging-data-commons-skill/references/cli_guide.md           # idc-index CLI tools
Please also read /path/to/imaging-data-commons-skill/references/parquet_access_guide.md # Direct Parquet queries
Please also read /path/to/imaging-data-commons-skill/references/mcp_guide.md            # Hosted IDC MCP server
Please also read /path/to/imaging-data-commons-skill/references/rest_api_guide.md       # Hosted IDC REST API
```

### Verifying Installation

After installing, verify by asking your assistant:
```
What skills do you have for medical imaging data?
```

Or invoke directly:
```
/imaging-data-commons
```

## IDC MCP Server (Optional)

IDC operates a hosted [MCP](https://modelcontextprotocol.io/) server that exposes IDC
discovery, cohort building, and metadata queries as agent tools:

| Property | Value |
|----------|-------|
| URL | `https://api.imaging.datacommons.cancer.gov/mcp` |
| Transport | Streamable HTTP |
| Authentication | None |

This is optional and independent of the skill — the skill is fully functional without it. When
both are present, the skill routes discovery and metadata to the server and keeps downloads,
local analysis, DICOMweb, and BigQuery for `idc-index`. See
[references/mcp_guide.md](references/mcp_guide.md) for the full division of labor.

Adding the server is worthwhile if you do a lot of interactive exploration, or if you work in
an assistant without local Python. If you mainly download data and analyze it locally, the
skill alone is enough.

Registration is agent-specific; consult your agent's MCP documentation. For Claude Code:

```bash
claude mcp add --transport http idc https://api.imaging.datacommons.cancer.gov/mcp
```

On claude.ai, add it under [Settings > Connectors](https://claude.ai/customize/connectors) as
a custom connector with the URL above.

Two Claude Code notes if you write permission rules: tools are namespaced by the server name
you choose, so a CLI install named `idc` produces `mcp__idc__*` while a claude.ai connector
produces `mcp__claude_ai_<name>__*`. Allow rules require a literal server segment —
`mcp__idc__*` works, `mcp__*` is ignored.

## IDC REST API (No Setup Required)

The same service is also a plain REST API at `https://api.imaging.datacommons.cancer.gov/v3`,
with no authentication and nothing to register. The skill uses it when an assistant has no
local Python, when the client is another language, or when the user wants shell commands they
can re-run:

```bash
curl -s https://api.imaging.datacommons.cancer.gov/v3/version
```

The only setup it may need is network access: in a sandboxed assistant, add
`api.imaging.datacommons.cancer.gov` to the allowed domains alongside the storage domains
listed above. See [references/rest_api_guide.md](references/rest_api_guide.md) for the endpoint
reference, and [the Swagger UI](https://api.imaging.datacommons.cancer.gov/v3/docs) to try
endpoints in a browser.

## API Setup

If you're calling an LLM API directly (any provider), include the contents of `SKILL.md` in your system prompt. Include additional reference guides from [references/](references/) as needed for advanced features.

### Example with the Anthropic API

```python
import anthropic
from pathlib import Path

# Read skill files
skill_content = Path('SKILL.md').read_text()

# Optionally include reference guides for advanced features:
# skill_content += "\n\n" + Path('references/bigquery_guide.md').read_text()      # BigQuery queries
# skill_content += "\n\n" + Path('references/dicomweb_guide.md').read_text()      # DICOMweb API
# skill_content += "\n\n" + Path('references/index_tables_guide.md').read_text()  # Table schemas
# skill_content += "\n\n" + Path('references/digital_pathology_guide.md').read_text()  # Pathology
# skill_content += "\n\n" + Path('references/clinical_data_guide.md').read_text() # Clinical data
# skill_content += "\n\n" + Path('references/cloud_storage_guide.md').read_text() # GCS/S3 access

client = anthropic.Anthropic(api_key="your-api-key")

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=skill_content,  # Include skill as system context
    messages=[
        {"role": "user", "content": "Find CT scans of lung cancer in IDC"}
    ]
)
```

## Keeping the Skill Up to Date

The skill is refined frequently, and IDC publishes periodic (roughly quarterly) data releases. A skill that was accurate against one IDC release can return stale answers once a newer one lands, so it is worth staying current.

When network access is available, the skill checks at the start of a session and prints a notice if a newer `idc-index` package or a newer skill release is available. You can also subscribe to release notifications and update manually as described below.

### Get notified of new releases

The skill follows [Semantic Versioning](https://semver.org/) and publishes a GitHub Release for each update. On the [repository page](https://github.com/ImagingDataCommons/imaging-data-commons-skill), click **Watch → Custom → Releases** to be alerted whenever a new version is tagged. Skim the release notes first — they flag breaking changes, such as column renames or other schema changes.

### Update the skill

**claude.ai and Claude Desktop** — a custom skill is updated by replacing it:

1. Download the latest release ZIP from the [Releases page](https://github.com/ImagingDataCommons/imaging-data-commons-skill/releases/latest).
2. Confirm **Code execution and file creation** is enabled under **Settings > Capabilities**.
3. At https://claude.ai/customize, select **Skills**, delete the existing `imaging-data-commons` skill (**···** → **Delete**), and upload the new ZIP.

**Claude Code and other coding agents** — re-run the installer to pull the latest version:

```bash
npx skills add ImagingDataCommons/imaging-data-commons-skill
```

If you installed by symlinking a local clone (USAGE Options 1–2), just `git pull` in that clone — the symlink always reflects the latest checked-out version.

### Start a fresh conversation after updating

A skill loads into a conversation when the assistant decides it is relevant, at the session level. Updating the skill in settings does **not** change a conversation already underway. After updating, **start a new conversation** so the new version is picked up.

## Example Workflows

### Basic Data Discovery

```
User: "What collections in IDC have prostate MRI data?"
Assistant: [Uses skill to query and list relevant collections]
```

### Download Dataset

```
User: "Download all CT scans from the NSCLC-Radiomics collection"
Assistant: [Provides idc-index download command with proper parameters]
```

### License Checking

```
User: "Can I use TCGA-BRCA data for commercial purposes?"
Assistant: [Checks license and explains usage restrictions]
```

## Limitations

### Command Execution

- **Assistants with code execution** (e.g., Claude Desktop, Claude Code, other coding agents): Can execute commands directly, such as installing `idc-index` with pip
- **Assistants without code execution**: Can only provide guidance. Users will need to manually run installation commands like `pip install idc-index`

### Data Access

- The skill provides guidance for accessing IDC data but does not directly download or store data
- Users need Python and internet access to download actual DICOM files
- Some operations (like BigQuery access) may require Google Cloud Platform authentication

## Troubleshooting

### Skill Not Loading

- **Claude Code and other coding agents**: Verify the symlink exists in the agent's skills directory (e.g., `~/.claude/skills/imaging-data-commons`) and points to the correct location
- **ZIP attachment** (Claude.ai): Ensure the release ZIP is attached to your conversation before asking IDC-related questions
- **File size**: The ZIP file is large. If the assistant seems unaware of IDC, the file may not have been fully loaded

### Skill Not Responding as Expected

- **Verify skill is loaded**: Ask your assistant "What do you know about the Imaging Data Commons?" — it should give a detailed response
- **Be specific**: Use clear questions like "Find lung CT scans in IDC" rather than just "find scans"
- **Report issues**: If the skill fails to answer expected questions, [open an issue](https://github.com/ImagingDataCommons/imaging-data-commons-skill/issues/new/choose)

### Installation Commands Fail

- **Python environment**: Ensure Python 3.10+ is installed and accessible (idc-index requires Python >= 3.10)
- **Network access**: Verify internet connectivity for pip installations
- **Permissions**: Some systems may require `pip install --user idc-index` instead

### BigQuery or DICOMweb Issues

- See the [IDC BigQuery Guide](references/bigquery_guide.md) or [DICOMweb Guide](references/dicomweb_guide.md) for advanced troubleshooting
- Access to IDC BigQuery tables requires Google Cloud authentication setup
- IDC offers a public DICOMweb proxy (no auth required) and a Google Healthcare API endpoint (requires gcloud authentication for higher quotas)

## Resources

- [SKILL.md](SKILL.md) - Comprehensive skill documentation
- [references/](references/) - Reference guides (BigQuery, DICOMweb, SQL patterns, pathology, clinical data, cloud storage, CLI, Parquet, MCP server, REST API)
- [IDC Documentation](https://learn.canceridc.dev/)
- [idc-index Package](https://pypi.org/project/idc-index/)
- [IDC Portal](https://portal.imaging.datacommons.cancer.gov/)

## Support

For questions about:
- **The skill itself**: [Open a GitHub issue](https://github.com/ImagingDataCommons/imaging-data-commons-skill/issues)
- **IDC data or platform**: [IDC Forum](https://discourse.canceridc.dev/)
- **idc-index package**: [idc-index Issues](https://github.com/ImagingDataCommons/idc-index/issues)
