# Changelog

All notable changes to the IDC Claude Skill are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- Removed `CHANGELOG.md` from release zip artifact; changelog is available on the GitHub releases page and not needed in the install package

## [1.6.0] - 2026-05-07

### Added

- `tests/test_bq_snippets.py`: BigQuery snippet validation using `bq query --dry_run` — 33 tests covering all SQL examples in `references/bigquery_guide.md` (dicom_all, original_collections_metadata, segmentations, quantitative_measurements, qualitative_measurements, private elements, and clinical tables); skips automatically when `bq` CLI is unavailable or unauthenticated

### Security

- Fixed auto-upgrade subprocess call to pin `idc-index` to `REQUIRED_VERSION` (was `"idc-index"`, now `f"idc-index=={REQUIRED_VERSION}"`), ensuring the installed version always matches the tested version declared in the frontmatter
- Added network access transparency note to Overview documenting expected external endpoints (GCS, S3, BigQuery, DICOMweb proxy, Google Healthcare API) and clarifying that no credentials or environment variables are accessed by the skill
- Added tested-with version comment to optional dependency install block (`pandas>=1.5, numpy>=1.23, pydicom>=2.3`)

### Changed

- Updated frontmatter description to be directive about skill triggering: now explicitly instructs invocation for IDC-related queries even without the word "IDC" in the prompt
- Extracted "Batch Processing and Filtering" (section 6) from SKILL.md to `references/use_cases.md` (Use Case 5); replaced inline code block with a 2-sentence summary and pointer
- Extracted "Integration with Analysis Pipelines" (section 9) from SKILL.md to `references/use_cases.md` (Use Case 6); replaced inline pydicom/SimpleITK code blocks with a 2-sentence summary and pointer
- SKILL.md reduced from 865 → 775 lines (−90 lines); `references/use_cases.md` expanded from 187 → 278 lines
- Updated to idc-index 0.12.1 (idc-index-data 24.0.4, IDC data version v24)
- IDC v24 adds 15 new collections (161 → 176), ~39K new series, ~4 TB new data (99.27 TB total, 85,682 cases)
- Updated `collections_index` column names to snake_case (idc-index-data 24.0.0 breaking change):
  `CancerTypes` → `cancer_types`, `TumorLocations` → `tumor_locations`,
  `Subjects` → `subjects`, `Species` → `species`, `Sources` → `sources`,
  `SupportingData` → `supporting_data`, `Program` → `program_id`
- Updated `analysis_results_index` column names to snake_case (idc-index-data 24.0.4 breaking change):
  `Subjects` → `subjects`, `Collections` → `collections`, `Modalities` → `modalities`

## [1.5.0] - 2026-04-08

### Added

- `volume_geometry_index` table documentation: 3D geometry validation for single-frame CT, MR, and PT series; boolean checks (orientation, spacing, dimensions, slice positions) and composite `regularly_spaced_3d_volume` flag; join via `SeriesInstanceUID`
- `rtstruct_index` table documentation: RT Structure Set metadata (total ROIs, ROI names, generation algorithms, interpreted types, referenced image series UID); join via `SeriesInstanceUID`
- New reference guide `references/parquet_access_guide.md`: direct DuckDB queries against public GCS Parquet files without installing idc-index; URL pattern, available files, and query examples for main index, `volume_geometry_index`, and `rtstruct_index`
- SQL patterns for `volume_geometry_index` and `rtstruct_index` in `references/sql_patterns.md`
- Detailed documentation for BigQuery-only derived tables in `references/bigquery_guide.md`:
  - `segmentations`: per-segment anatomy with full schema, column descriptions, and queries for discovering structures, filtering by coded concept, and linking to SR measurements; note on gap vs `seg_index` in idc-index
  - `quantitative_measurements`: radiomics and clinical numeric measurements from DICOM SR TID1500 (volume, diameter, shape descriptors, texture, intensity statistics); full schema with column descriptions and query examples
  - `qualitative_measurements`: coded assessments from DICOM SR TID1500 (malignancy rating, calcification, texture, margin); full schema with column descriptions and query examples
  - `measurement_groups`: parent grouping table for SR measurements
  - Combined example joining all three derived tables for LIDC-IDRI nodule analysis (malignancy + volume + diameter)
- SKILL.md section 7 now explicitly lists per-segment anatomy search, quantitative SR measurements, and qualitative SR measurements as BigQuery-only use cases with no idc-index equivalent

### Changed

- Updated to idc-index 0.11.14 (idc-index-data 23.10.1)
- Added `SOPClassUID` and `TransferSyntaxUID` columns to Key Columns Reference in `references/index_tables_guide.md`
- Added Direct Parquet Access entry to Data Access Options table and pointer in SKILL.md
- Added `parquet_access_guide.md` to Quick Navigation table in SKILL.md

## [1.4.0] - 2026-03-04

### Added

- New "Identifying Tumor vs Normal Slides" section in digital pathology guide with two approaches:
  - Structured DICOM tissue type via `primaryAnatomicStructureModifier_CodeMeaning` (works across all SM collections)
  - TCGA barcode parsing via `ContainerIdentifier` (TCGA collections only, catches metastatic edge cases)
- TCGA-BRCA worked examples showing tumor vs normal slide counts
- Documentation references to GDC TCGA barcode format and sample type codes
- Specimen preparation query examples: filtering by staining (H&E), embedding medium (FFPE vs frozen), and fixative, with note about array column syntax (`array_to_string`, `list_contains`)
- "Finding Pre-Computed Analysis Results" section: discovering derived datasets (nuclei segmentations, TIL maps) via `analysis_results_index`, with example joining annotations back to source slides
- Note about per-annotation measurements in DICOM ANN objects (extractable via highdicom after download), with link to [microscopy_dicom_ann_intro](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/pathomics/microscopy_dicom_ann_intro.ipynb) tutorial

### Changed

- Updated to idc-index 0.11.10 (adds `ContainerIdentifier` column to `sm_index`)
- Updated `sm_index` table description to reflect newly available columns (container/slide ID, tissue type, anatomic structure, diagnosis)

## [1.3.1] - 2026-02-11

### Added

- Automatic idc-index package version check with upgrade prompt before any queries
- Version check compares installed version against `metadata.idc-index` in frontmatter and triggers `pip install --upgrade` when outdated

### Fixed

- Prevents "table not found" errors when using newer index tables (e.g., `contrast_index`) with older idc-index versions

## [1.3.0] - 2026-02-10

### Added

- Digital pathology reference guide (`references/digital_pathology_guide.md`) with SM, ANN, and SEG query patterns, join examples, and pathology tool recommendations
- `seg_index` coverage in digital pathology guide with cross-domain clarification (SEG used for both radiology and pathology) and query for finding pathology-specific segmentations
- `AnnotationGroupLabel` filtering examples for finding annotation groups by name
- SM + ANN cross-reference queries showing how to find annotations on slide microscopy images
- Index discovery guidance before BigQuery section to ensure all local indices are checked first
- Documentation for new `ann_index` and `ann_group_index` tables (Microscopy Bulk Simple Annotations)
- Example queries for annotation series and annotation group metadata
- Explanation of downloaded DICOM file naming convention (`<crdc_instance_uuid>.dcm`)
- New reference guides extracted from SKILL.md:
  - `references/index_tables_guide.md` - Table schemas, DataFrame access, join column reference
  - `references/sql_patterns.md` - Quick-reference SQL patterns for common queries
  - `references/use_cases.md` - End-to-end workflow examples
- Quick Navigation section in SKILL.md with decision triggers for when to load each reference
- `idc-data-version` field in frontmatter metadata
- Documentation for new `contrast_index` table (contrast bolus metadata for CT, MR, PT, XA, RF series)

### Changed

- Updated to idc-index 0.11.9 (IDC data version v23)
- Reduced SKILL.md from 1,245 to 825 lines by extracting secondary content to reference files
- Core Capabilities sections remain inline to ensure correct API pattern usage
- Refactored detailed SM/ANN content from SKILL.md into `references/digital_pathology_guide.md`, keeping brief summaries with pointers in main skill
- Made IDC version (v23) more prominent in SKILL.md with verification guidance to prevent responses using older versions
- Clarified distinction between `index_tables_guide.md` (structure/access) and `sql_patterns.md` (query examples)

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
