# Changelog

All notable changes to the IDC Claude Skill are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
