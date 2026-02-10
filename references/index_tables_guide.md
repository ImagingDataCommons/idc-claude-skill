# Index Tables Guide for IDC

**Tested with:** idc-index 0.11.8 (IDC data version v23)

This guide covers advanced patterns for working with IDC index tables: JOIN queries, programmatic schema discovery, and direct DataFrame access. For the overview of available tables and their purposes, see the "Index Tables" section in the main SKILL.md.

**Complete index table documentation:** https://idc-index.readthedocs.io/en/latest/indices_reference.html

## When to Use This Guide

Load this guide when you need to:
- Write complex SQL JOIN queries across multiple index tables
- Discover table schemas and column types programmatically
- Access index tables as pandas DataFrames (not via SQL)
- Understand key columns for filtering and joining

## Prerequisites

```bash
pip install --upgrade idc-index
```

## Example Joins

The index tables can be joined to combine metadata. Always fetch the required indices first using `client.fetch_index()`.

```python
from idc_index import IDCClient
client = IDCClient()

# Join index with collections_index to get cancer types
client.fetch_index("collections_index")
result = client.sql_query("""
    SELECT i.SeriesInstanceUID, i.Modality, c.CancerTypes, c.TumorLocations
    FROM index i
    JOIN collections_index c ON i.collection_id = c.collection_id
    WHERE i.Modality = 'MR'
    LIMIT 10
""")

# Join index with sm_index for slide microscopy details
client.fetch_index("sm_index")
result = client.sql_query("""
    SELECT i.collection_id, i.PatientID, s.ObjectiveLensPower, s.min_PixelSpacing_2sf
    FROM index i
    JOIN sm_index s ON i.SeriesInstanceUID = s.SeriesInstanceUID
    LIMIT 10
""")

# Join ann_group_index with ann_index and index for annotation details
client.fetch_index("ann_index")
client.fetch_index("ann_group_index")
result = client.sql_query("""
    SELECT g.AnnotationGroupLabel, g.GraphicType, g.NumberOfAnnotations,
           i.collection_id, a.referenced_SeriesInstanceUID as source_series
    FROM ann_group_index g
    JOIN ann_index a ON g.SeriesInstanceUID = a.SeriesInstanceUID
    JOIN index i ON a.SeriesInstanceUID = i.SeriesInstanceUID
    LIMIT 10
""")

# Join seg_index with index to find segmentations and their source images
client.fetch_index("seg_index")
result = client.sql_query("""
    SELECT
        s.SeriesInstanceUID as seg_series,
        s.AlgorithmName,
        s.total_segments,
        src.collection_id,
        src.Modality as source_modality,
        src.BodyPartExamined
    FROM seg_index s
    JOIN index src ON s.segmented_SeriesInstanceUID = src.SeriesInstanceUID
    WHERE s.AlgorithmType = 'AUTOMATIC'
    LIMIT 10
""")
```

## Accessing Index Tables

### Via SQL (recommended for filtering/aggregation)

```python
from idc_index import IDCClient
client = IDCClient()

# Query the primary index (always available)
results = client.sql_query("SELECT * FROM index WHERE Modality = 'CT' LIMIT 10")

# Fetch and query additional indices
client.fetch_index("collections_index")
collections = client.sql_query("SELECT collection_id, CancerTypes, TumorLocations FROM collections_index")

client.fetch_index("analysis_results_index")
analysis = client.sql_query("SELECT * FROM analysis_results_index LIMIT 5")
```

### As pandas DataFrames (direct access)

```python
# Primary index (always available after client initialization)
df = client.index

# Fetch and access on-demand indices
client.fetch_index("sm_index")
sm_df = client.sm_index
```

## Discovering Table Schemas

The `indices_overview` dictionary contains complete schema information for all tables. **Always consult this when writing queries or exploring data structure.**

**DICOM attribute mapping:** Many columns are populated directly from DICOM attributes in the source files. The column description in the schema indicates when a column corresponds to a DICOM attribute (e.g., "DICOM Modality attribute" or references a DICOM tag). This allows leveraging DICOM knowledge when querying — standard DICOM attribute names like `PatientID`, `StudyInstanceUID`, `Modality`, `BodyPartExamined` work as expected.

```python
from idc_index import IDCClient
client = IDCClient()

# List all available indices with descriptions
for name, info in client.indices_overview.items():
    print(f"\n{name}:")
    print(f"  Installed: {info['installed']}")
    print(f"  Description: {info['description']}")

# Get complete schema for a specific index (columns, types, descriptions)
schema = client.indices_overview["index"]["schema"]
print(f"\nTable: {schema['table_description']}")
print("\nColumns:")
for col in schema['columns']:
    desc = col.get('description', 'No description')
    # Description indicates if column is from DICOM attribute
    print(f"  {col['name']} ({col['type']}): {desc}")

# Find columns that are DICOM attributes (check description for "DICOM" reference)
dicom_cols = [c['name'] for c in schema['columns'] if 'DICOM' in c.get('description', '').upper()]
print(f"\nDICOM-sourced columns: {dicom_cols}")
```

**Alternative: use `get_index_schema()` method:**
```python
schema = client.get_index_schema("index")
# Returns same schema dict: {'table_description': ..., 'columns': [...]}
```

## Key Columns Reference

Most common columns in the primary `index` table (use `indices_overview` for complete list and descriptions):

| Column | Type | DICOM | Description |
|--------|------|-------|-------------|
| `collection_id` | STRING | No | IDC collection identifier |
| `analysis_result_id` | STRING | No | If applicable, indicates what analysis results collection given series is part of |
| `source_DOI` | STRING | No | DOI linking to dataset details; use for learning more about the content and for attribution (see citations below) |
| `PatientID` | STRING | Yes | Patient identifier |
| `StudyInstanceUID` | STRING | Yes | DICOM Study UID |
| `SeriesInstanceUID` | STRING | Yes | DICOM Series UID — use for downloads/viewing |
| `Modality` | STRING | Yes | Imaging modality (CT, MR, PT, SM, SEG, ANN, RTSTRUCT, etc.) |
| `BodyPartExamined` | STRING | Yes | Anatomical region |
| `SeriesDescription` | STRING | Yes | Description of the series |
| `Manufacturer` | STRING | Yes | Equipment manufacturer |
| `StudyDate` | STRING | Yes | Date study was performed |
| `PatientSex` | STRING | Yes | Patient sex |
| `PatientAge` | STRING | Yes | Patient age at time of study |
| `license_short_name` | STRING | No | License type (CC BY 4.0, CC BY-NC 4.0, etc.) |
| `series_size_MB` | FLOAT | No | Size of series in megabytes |
| `instanceCount` | INTEGER | No | Number of DICOM instances in series |

**DICOM = Yes**: Column value extracted from the DICOM attribute with the same name. Refer to the [DICOM standard](https://dicom.nema.org/medical/dicom/current/output/chtml/part06/chapter_6.html) for numeric tag mappings. Use standard DICOM knowledge for expected values and formats.

## Common Join Patterns

| Join | Purpose |
|------|---------|
| `index JOIN collections_index ON collection_id` | Get collection metadata (cancer types, locations) |
| `index JOIN sm_index ON SeriesInstanceUID` | Get slide microscopy details |
| `seg_index JOIN index ON segmented_SeriesInstanceUID = SeriesInstanceUID` | Find source images for segmentations |
| `ann_index JOIN index ON SeriesInstanceUID` | Get annotation context |
| `ann_group_index JOIN ann_index ON SeriesInstanceUID` | Get annotation group details |

## Troubleshooting

**Issue:** Query returns empty results when joining tables
- **Cause:** Target index not fetched before query
- **Solution:** Always call `client.fetch_index("table_name")` before using a table in SQL

**Issue:** Column not found in table
- **Cause:** Column name misspelled or doesn't exist in that table
- **Solution:** Use `client.indices_overview["table_name"]["schema"]["columns"]` to list available columns

**Issue:** DataFrame access returns None
- **Cause:** Index not fetched or property name incorrect
- **Solution:** Fetch first with `client.fetch_index()`, then access via property matching the index name

## Resources

- Complete index table documentation: https://idc-index.readthedocs.io/en/latest/indices_reference.html
- Main SKILL.md for available tables overview
- `references/clinical_data_guide.md` for clinical data joins
- `references/digital_pathology_guide.md` for pathology-specific indices (sm_index, ann_index, seg_index)
- `references/bigquery_guide.md` for advanced queries requiring full DICOM metadata
