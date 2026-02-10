# Changelog

All notable changes to the IDC Claude Skill are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Digital pathology reference guide (`references/digital_pathology_guide.md`) with SM, ANN, and SEG query patterns, join examples, and pathology tool recommendations
- `seg_index` coverage in digital pathology guide with cross-domain clarification (SEG used for both radiology and pathology) and query for finding pathology-specific segmentations
- `AnnotationGroupLabel` filtering examples for finding annotation groups by name
- SM + ANN cross-reference queries showing how to find annotations on slide microscopy images
- Index discovery guidance before BigQuery section to ensure all local indices are checked first
- Documentation for new `ann_index` and `ann_group_index` tables (Microscopy Bulk Simple Annotations)
- Example queries for annotation series and annotation group metadata
- Explanation of downloaded DICOM file naming convention (`<crdc_instance_uuid>.dcm`)

### Changed

- Refactored detailed SM/ANN content from SKILL.md into `references/digital_pathology_guide.md`, keeping brief summaries with pointers in main skill
- Updated to idc-index 0.11.8 (IDC data version v23)
- Made IDC version (v23) more prominent in SKILL.md with verification guidance to prevent responses using older versions

## [1.2.0] - 2026-02-04

### Added

- Clinical data reference guide for navigating tabular data accompanying images
- Detailed patterns for mapping coded values (option_code to option_description)
- Examples for joining clinical data with imaging data via dicom_patient_id
- Expanded BigQuery guide with comprehensive clinical data coverage (metadata tables, cross-collection queries)
- Private DICOM elements documentation in BigQuery guide covering vendor-specific tags (e.g., diffusion b-values)
- Query patterns for discovering, accessing, and filtering by private tags in the OtherElements column

## [1.1.0] - 2026-02-02

### Added

- CLI reference guide for idc-index command-line tools
- Cloud storage reference guide explaining bucket organization and direct access via s5cmd
- GitHub Actions workflow for syncing skill updates to claude-scientific-skills repository

### Fixed

- Moved version field from top-level frontmatter to metadata section for compatibility
- Corrected s5cmd command-line syntax in cloud storage guide
- Clarified caveat about retracted data in DICOMweb guide

### Changed

- Updated DICOMweb reference to explain differences between the two available endpoints

## [1.0.0] - 2026-01-31

### Added

- Core IDC data model documentation with index tables reference
- Query and download workflows using idc-index Python package
- BigQuery integration guide for advanced queries
- DICOMweb API guide for programmatic access
- Visualization integration with IDC Portal and OHIF viewer
- License checking and citation generation examples
- SQL query patterns for common use cases
- DICOM metadata guidance and best practices
