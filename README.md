# IDC Claude Skill

A Claude AI skill for querying and downloading public cancer imaging data from the National Cancer Institute's [Imaging Data Commons (IDC)](https://imaging.datacommons.cancer.gov/).

## What This Skill Does

- Find imaging datasets by cancer type, imaging modality (CT, MR, PET, etc.), or anatomy
- Check data licenses and generate proper citations
- Generate download commands using the `idc-index` Python package
- Provide links to browser-based DICOM viewers for data preview
- Answer questions about IDC data structure and DICOM metadata

## Example Questions

Once the skill is loaded, you can ask questions like:

- "Find CT scans of lung cancer in IDC"
- "How do I download all breast MRI data with commercial-use licenses?"
- "Show me the available collections in IDC and their sizes"
- "Generate a citation for the TCGA-BRCA collection"

## Reporting Issues

If the skill provides incorrect or incomplete answers, please [open an issue](https://github.com/ImagingDataCommons/idc-claude-skill/issues/new/choose) using our issue template.

## Setup Instructions

See [USAGE.md](USAGE.md) for detailed instructions on loading this skill in Claude Desktop or via the API.

## Also Available In

This skill is included in the [K-Dense-AI/claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills) collection alongside other scientific skills.

**Choose this repo if:** You only need Imaging Data Commons functionality

**Choose the collection if:** You want multiple scientific skills in one place

## Credits

This skill was created and is maintained by [Andrey Fedorov (@fedorov)](https://github.com/fedorov) and the [Imaging Data Commons](https://imaging.datacommons.cancer.gov/) team.

For comprehensive documentation about the skill's capabilities, see [SKILL.md](SKILL.md).

## License

This skill is licensed under the MIT License. IDC data has individual collection licenses (see skill documentation for details).
