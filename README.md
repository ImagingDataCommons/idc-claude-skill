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

## Versioning

This skill follows [Semantic Versioning](https://semver.org/).

- **Requires:** [idc-index](https://github.com/ImagingDataCommons/idc-index)

See [CHANGELOG.md](CHANGELOG.md) for version history and [Releases](https://github.com/ImagingDataCommons/idc-claude-skill/releases) for downloads.

## Credits

This skill was created and is maintained by [Andrey Fedorov (@fedorov)](https://github.com/fedorov) and the [Imaging Data Commons](https://imaging.datacommons.cancer.gov/) team.

For comprehensive documentation about the skill's capabilities, see [SKILL.md](SKILL.md).

Development of this skill as part of Imaging Data Commons development has been funded in whole or in part with Federal funds from the National Cancer Institute, National Institutes of Health, under Task Order No. HHSN26110071 under Contract No. HHSN261201500003I. 

If you use this skill in your research, please acknowledge IDC by citing the following publication:


> Fedorov, A., Longabaugh, W. J. R., Pot, D., Clunie, D. A., Pieper, S. D., Gibbs, D. L., Bridge, C., Herrmann, M. D., Homeyer, A., Lewis, R., Aerts, H. J. W. L., Krishnaswamy, D., Thiriveedhi, V. K., Ciausu, C., Schacherer, D. P., Bontempi, D., Pihl, T., Wagner, U., Farahani, K., Kim, E. & Kikinis, R. National cancer institute imaging data commons: Toward transparency, reproducibility, and scalability in imaging artificial intelligence. _Radiographics_ 43, (2023). [https://doi.org/10.1148/rg.230180](https://doi.org/10.1148/rg.230180)
  


## License

This skill is licensed under the MIT License. IDC data has individual collection licenses (see skill documentation for details).
