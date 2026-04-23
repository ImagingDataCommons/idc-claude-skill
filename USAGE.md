# Usage Instructions

This document provides technical instructions for integrating the IDC Claude skill into your AI assistant environment.

## Claude.ai Web Interface

### Upload Repository as ZIP

1. Download this repository as a ZIP file (Code → Download ZIP on GitHub)
2. Start a new conversation at [claude.ai](https://claude.ai)
3. Click the attachment icon and upload the ZIP file
4. Claude will have access to all skill content including reference guides

This gives Claude the complete skill with all documentation in one upload.

### Settings > Capabilities

To enable web browsing and allow Claude to access IDC resources directly, configure the Capabilities settings:

1. Go to **Settings > Capabilities** in Claude.ai
2. Enable the following options:
   - **Web search** — allows Claude to look up live IDC data and documentation
3. Under **Allowed domains**, add the following:
   - `*.github.com`
   - `*.githubusercontent.com`
   - `*.googleapis.com`
   - `storage.googleapis.com`

These domains allow Claude to access the skill files from GitHub and IDC data from Google Cloud Storage.

## Claude Desktop Setup

Claude Desktop works the same as the Claude.ai web interface. Follow the [Claude.ai Web Interface](#claudeai-web-interface) instructions above to upload the ZIP and configure Settings > Capabilities.

For persistent access across conversations, create a **Project** in Claude Desktop, upload the ZIP to the project's knowledge base, and configure the allowed domains in the project's Capabilities settings.

### Verifying the Skill is Loaded

Ask Claude: "What do you know about the Imaging Data Commons?"

Claude should respond with specific information about IDC, the `idc-index` package, and how to query and download cancer imaging data.

## Claude Code Setup

If you're using [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (the CLI tool), you can install the skill for persistent access.

### Option 1: Install via npx (Recommended)

The simplest way to install this skill using the [Skills.sh](https://skills.sh/) framework:

```bash
npx skills add https://github.com/imagingdatacommons/idc-claude-skill --skill imaging-data-commons
```

This command will automatically detect all AI agents on your system and offer to install the skill across all of them, making it available system-wide. Once installed, invoke with `/imaging-data-commons` or let your AI assistant auto-detect based on questions about IDC.

### Option 2: Install as Personal Skill

Link or copy the skill to your personal skills directory. This makes it available across all projects:

```bash
# Create a symlink (keeps skill updated with repo)
ln -s /path/to/idc-claude-skill ~/.claude/skills/imaging-data-commons

# Or copy the entire directory
cp -r /path/to/idc-claude-skill ~/.claude/skills/imaging-data-commons
```

Once installed, invoke with `/imaging-data-commons` or let Claude auto-detect based on your questions about IDC.

### Option 3: Install as Project Skill

For project-specific use, link to your project's `.claude/skills/` directory:

```bash
mkdir -p /path/to/your-project/.claude/skills
ln -s /path/to/idc-claude-skill /path/to/your-project/.claude/skills/imaging-data-commons
```

This makes the skill available only when working in that project.

### Option 4: Import During Session

For one-time use, read the skill files directly:
```
/read /path/to/idc-claude-skill/SKILL.md
```

For BigQuery or DICOMweb features, also read the reference guides:
```
/read /path/to/idc-claude-skill/references/bigquery_guide.md
/read /path/to/idc-claude-skill/references/dicomweb_guide.md
```

### Verifying Installation

After installing, verify by asking Claude:
```
What skills do you have for medical imaging data?
```

Or invoke directly:
```
/imaging-data-commons
```

## Claude API Setup

If you're using the Claude API directly, include the contents of `SKILL.md` in your system prompt. For BigQuery or DICOMweb features, also include the relevant reference guides.

### Example with Anthropic API

```python
import anthropic
from pathlib import Path

# Read skill files
skill_content = Path('SKILL.md').read_text()

# Optionally include reference guides for advanced features
# skill_content += "\n\n" + Path('references/bigquery_guide.md').read_text()
# skill_content += "\n\n" + Path('references/dicomweb_guide.md').read_text()

client = anthropic.Anthropic(api_key="your-api-key")

message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system=skill_content,  # Include skill as system context
    messages=[
        {"role": "user", "content": "Find CT scans of lung cancer in IDC"}
    ]
)
```

## Example Workflows

### Basic Data Discovery

```
User: "What collections in IDC have prostate MRI data?"
Claude: [Uses skill to query and list relevant collections]
```

### Download Dataset

```
User: "Download all CT scans from the NSCLC-Radiomics collection"
Claude: [Provides idc-index download command with proper parameters]
```

### License Checking

```
User: "Can I use TCGA-BRCA data for commercial purposes?"
Claude: [Checks license and explains usage restrictions]
```

## Limitations

### Command Execution

- **Claude Desktop**: Can execute commands directly (e.g., installing `idc-index` with pip)
- **Other AI Assistants**: May only provide guidance without executing commands. Users will need to manually run installation commands like `pip install idc-index`

### Data Access

- The skill provides guidance for accessing IDC data but does not directly download or store data
- Users need Python and internet access to download actual DICOM files
- Some operations (like BigQuery access) may require Google Cloud Platform authentication

## Troubleshooting

### Skill Not Loading

- **Claude Code**: Verify the symlink exists at `~/.claude/skills/imaging-data-commons` and points to the correct directory
- **ZIP attachment** (Claude.ai): Ensure the repository ZIP is attached to your conversation before asking IDC-related questions
- **File size**: The ZIP file is large. If Claude seems unaware of IDC, the file may not have been fully loaded

### Skill Not Responding as Expected

- **Verify skill is loaded**: Ask Claude "What do you know about the Imaging Data Commons?" — it should give a detailed response
- **Be specific**: Use clear questions like "Find lung CT scans in IDC" rather than just "find scans"
- **Report issues**: If the skill fails to answer expected questions, [open an issue](https://github.com/ImagingDataCommons/idc-claude-skill/issues/new/choose)

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
- [IDC Documentation](https://learn.canceridc.dev/)
- [idc-index Package](https://pypi.org/project/idc-index/)
- [IDC Portal](https://portal.imaging.datacommons.cancer.gov/)

## Support

For questions about:
- **The skill itself**: [Open a GitHub issue](https://github.com/ImagingDataCommons/idc-claude-skill/issues)
- **IDC data or platform**: [IDC Forum](https://discourse.canceridc.dev/)
- **idc-index package**: [idc-index Issues](https://github.com/ImagingDataCommons/idc-index/issues)
