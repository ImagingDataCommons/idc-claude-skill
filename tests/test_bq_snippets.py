"""
BigQuery snippet validation for references/bigquery_guide.md.

Uses `bq query --dry_run` (validates syntax and schema, scans no data, no cost)
to confirm all SQL snippets reference tables and columns that exist in the
current IDC BigQuery datasets.

Requires:
  - gcloud CLI (`bq`) installed and on PATH
  - Active credentials (gcloud auth application-default login)
  - A GCP project accessible for quota (set via BQ_PROJECT_ID env or hardcoded default)
"""

import os
import shutil
import subprocess
import pytest

PROJECT_ID = os.environ.get("BQ_PROJECT_ID", "idc-dev-etl")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dry_run(sql: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "bq", "query",
            "--dry_run",
            "--nouse_cache",
            "--use_legacy_sql=false",
            f"--project_id={PROJECT_ID}",
            sql,
        ],
        capture_output=True,
        text=True,
    )


def assert_valid(sql: str):
    result = _dry_run(sql)
    assert result.returncode == 0, (
        f"BQ dry-run failed\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# Session-scoped guard: skip entire module when bq is unavailable / unauthed
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def require_bq():
    if shutil.which("bq") is None:
        pytest.skip("bq CLI not found — install Google Cloud SDK to run BQ tests")
    probe = _dry_run(
        "SELECT 1 FROM `bigquery-public-data.idc_current.dicom_all` LIMIT 1"
    )
    if probe.returncode != 0:
        pytest.skip(
            f"bq not authenticated or project not accessible "
            f"(project={PROJECT_ID}): {probe.stderr.strip()}"
        )


# ===========================================================================
# dicom_all
# ===========================================================================

class TestDicomAll:
    """Core dicom_all queries from bigquery_guide.md."""

    def test_basic_ct_query(self):
        assert_valid("""
            SELECT
              collection_id,
              PatientID,
              StudyInstanceUID,
              SeriesInstanceUID,
              Modality,
              BodyPartExamined,
              SeriesDescription,
              gcs_url,
              license_short_name
            FROM `bigquery-public-data.idc_current.dicom_all`
            WHERE Modality = 'CT'
              AND BodyPartExamined = 'CHEST'
            LIMIT 10
        """)

    def test_collections_by_criteria(self):
        assert_valid("""
            SELECT
              collection_id,
              COUNT(DISTINCT PatientID) as patient_count,
              COUNT(DISTINCT SeriesInstanceUID) as series_count,
              ARRAY_AGG(DISTINCT Modality) as modalities
            FROM `bigquery-public-data.idc_current.dicom_all`
            WHERE BodyPartExamined LIKE '%BRAIN%'
            GROUP BY collection_id
            HAVING patient_count > 50
            ORDER BY patient_count DESC
        """)

    def test_get_download_urls(self):
        assert_valid("""
            SELECT
              SeriesInstanceUID,
              gcs_url
            FROM `bigquery-public-data.idc_current.dicom_all`
            WHERE collection_id = 'rider_pilot'
              AND Modality = 'CT'
        """)

    def test_studies_with_multiple_modalities(self):
        assert_valid("""
            SELECT
              StudyInstanceUID,
              ARRAY_AGG(DISTINCT Modality) as modalities,
              COUNT(DISTINCT SeriesInstanceUID) as series_count
            FROM `bigquery-public-data.idc_current.dicom_all`
            GROUP BY StudyInstanceUID
            HAVING ARRAY_LENGTH(ARRAY_AGG(DISTINCT Modality)) > 1
            LIMIT 100
        """)

    def test_license_filtering(self):
        assert_valid("""
            SELECT
              collection_id,
              license_short_name,
              COUNT(*) as instance_count
            FROM `bigquery-public-data.idc_current.dicom_all`
            WHERE license_short_name = 'CC BY 4.0'
            GROUP BY collection_id, license_short_name
        """)


# ===========================================================================
# original_collections_metadata
# ===========================================================================

class TestOriginalCollectionsMetadata:
    def test_lung_collections(self):
        assert_valid("""
            SELECT
              collection_id,
              CancerTypes,
              TumorLocations,
              Subjects,
              src.source_doi,
              src.ImageTypes,
              src.license.license_short_name
            FROM `bigquery-public-data.idc_current.original_collections_metadata`,
            UNNEST(Sources) AS src
            WHERE CancerTypes LIKE '%Lung%'
        """)


# ===========================================================================
# segmentations
# ===========================================================================

class TestSegmentations:
    def test_find_segmentations_with_source_images(self):
        assert_valid("""
            SELECT
              src.collection_id,
              seg.SeriesInstanceUID as seg_series,
              seg.SegmentedPropertyType,
              src.SeriesInstanceUID as source_series,
              src.Modality as source_modality
            FROM `bigquery-public-data.idc_current.segmentations` seg
            JOIN `bigquery-public-data.idc_current.dicom_all` src
              ON seg.segmented_SeriesInstanceUID = src.SeriesInstanceUID
            WHERE src.collection_id = 'qin_prostate_repeatability'
            LIMIT 10
        """)

    def test_discover_structures(self):
        assert_valid("""
            SELECT
              SegmentedPropertyCategory.CodeMeaning AS category,
              SegmentedPropertyType.CodeMeaning AS structure,
              SegmentAlgorithmType,
              COUNT(DISTINCT SeriesInstanceUID) AS seg_series_count
            FROM `bigquery-public-data.idc_current.segmentations`
            GROUP BY 1, 2, 3
            ORDER BY seg_series_count DESC
            LIMIT 20
        """)

    def test_find_specific_structure_with_join(self):
        assert_valid("""
            SELECT
              seg.SeriesInstanceUID AS seg_series,
              seg.SegmentNumber,
              seg.SegmentedPropertyType.CodeMeaning AS structure,
              seg.SegmentAlgorithmType,
              seg.SegmentAlgorithmName,
              img.collection_id,
              img.PatientID,
              img.Modality,
              seg.viewer_url
            FROM `bigquery-public-data.idc_current.segmentations` seg
            JOIN `bigquery-public-data.idc_current.dicom_all` img
              ON seg.segmented_SeriesInstanceUID = img.SeriesInstanceUID
            WHERE seg.SegmentedPropertyType.CodeMeaning = 'Liver'
              AND seg.SegmentAlgorithmType = 'AUTOMATIC'
            LIMIT 20
        """)

    def test_segment_types_in_collection(self):
        assert_valid("""
            SELECT
              seg.SegmentedPropertyType.CodeMeaning AS structure,
              seg.SegmentAlgorithmType,
              COUNT(DISTINCT seg.SeriesInstanceUID) AS seg_series_count
            FROM `bigquery-public-data.idc_current.segmentations` seg
            JOIN `bigquery-public-data.idc_current.dicom_all` img
              ON seg.segmented_SeriesInstanceUID = img.SeriesInstanceUID
            WHERE img.collection_id = 'nlst'
            GROUP BY 1, 2
            ORDER BY seg_series_count DESC
        """)

    def test_link_segments_to_sr_measurements(self):
        assert_valid("""
            SELECT
              seg.SeriesInstanceUID AS seg_series,
              seg.SegmentNumber,
              seg.SegmentedPropertyType.CodeMeaning AS structure,
              qm.Quantity.CodeMeaning AS measurement,
              ROUND(CAST(qm.Value AS FLOAT64), 2) AS value,
              qm.Units.CodeMeaning AS units
            FROM `bigquery-public-data.idc_current.segmentations` seg
            JOIN `bigquery-public-data.idc_current.quantitative_measurements` qm
              ON seg.SeriesInstanceUID = qm.segmentationSeriesUID
              AND seg.SegmentNumber = qm.segmentationSegmentNumber
            WHERE seg.SegmentedPropertyType.CodeMeaning = 'Neoplasm'
              AND qm.Quantity.CodeMeaning = 'Volume from Voxel Summation'
            LIMIT 10
        """)


# ===========================================================================
# quantitative_measurements
# ===========================================================================

class TestQuantitativeMeasurements:
    def test_discover_measurement_types(self):
        assert_valid("""
            SELECT
              Quantity.CodeMeaning AS measurement,
              Units.CodeMeaning AS units,
              COUNT(*) AS measurement_count,
              COUNT(DISTINCT SeriesInstanceUID) AS sr_series_count
            FROM `bigquery-public-data.idc_current.quantitative_measurements`
            GROUP BY 1, 2
            ORDER BY measurement_count DESC
            LIMIT 20
        """)

    def test_liver_volume_query(self):
        assert_valid("""
            SELECT
              qm.PatientID,
              ROUND(CAST(qm.Value AS FLOAT64) / 1000, 1) AS volume_cm3,
              img.collection_id,
              qm.segmentationSeriesUID
            FROM `bigquery-public-data.idc_current.quantitative_measurements` qm
            JOIN `bigquery-public-data.idc_current.dicom_all` img
              ON qm.sourceSegmentedSeriesUID = img.SeriesInstanceUID
            WHERE qm.Quantity.CodeMeaning = 'Volume from Voxel Summation'
              AND qm.findingSite.CodeMeaning = 'Liver'
            ORDER BY volume_cm3 DESC
            LIMIT 20
        """)

    def test_patient_measurements(self):
        assert_valid("""
            SELECT
              qm.measurementGroup_number,
              qm.finding.CodeMeaning AS finding,
              qm.findingSite.CodeMeaning AS finding_site,
              qm.lateralityModifier.CodeMeaning AS laterality,
              qm.Quantity.CodeMeaning AS feature,
              ROUND(CAST(qm.Value AS FLOAT64), 3) AS value,
              qm.Units.CodeMeaning AS units
            FROM `bigquery-public-data.idc_current.quantitative_measurements` qm
            WHERE qm.PatientID = 'LIDC-IDRI-0001'
              AND qm.finding.CodeMeaning = 'Nodule'
            ORDER BY qm.measurementGroup_number, qm.Quantity.CodeMeaning
        """)


# ===========================================================================
# qualitative_measurements
# ===========================================================================

class TestQualitativeMeasurements:
    def test_discover_features(self):
        assert_valid("""
            SELECT
              Quantity.CodeMeaning AS feature,
              Value.CodeMeaning AS assessed_value,
              finding.CodeMeaning AS finding,
              COUNT(*) AS count
            FROM `bigquery-public-data.idc_current.qualitative_measurements`
            GROUP BY 1, 2, 3
            ORDER BY count DESC
            LIMIT 20
        """)

    def test_malignancy_filtering(self):
        assert_valid("""
            SELECT
              qm.PatientID,
              qm.trackingIdentifier AS nodule_id,
              qm.Value.CodeMeaning AS malignancy_rating,
              img.collection_id
            FROM `bigquery-public-data.idc_current.qualitative_measurements` qm
            JOIN `bigquery-public-data.idc_current.dicom_all` img
              ON qm.SeriesInstanceUID = img.SeriesInstanceUID
            WHERE qm.Quantity.CodeMeaning = 'Malignancy'
              AND qm.Value.CodeMeaning LIKE '%Suspicious%'
            ORDER BY qm.PatientID
            LIMIT 20
        """)


# ===========================================================================
# Combined derived tables
# ===========================================================================

class TestCombinedDerivedTables:
    def test_lidc_nodule_qual_quant(self):
        assert_valid("""
            SELECT
              qual.PatientID,
              qual.trackingIdentifier AS nodule_id,
              qual.Value.CodeMeaning AS malignancy_rating,
              ROUND(CAST(vol.Value AS FLOAT64), 1) AS volume_mm3,
              ROUND(CAST(diam.Value AS FLOAT64), 1) AS diameter_mm
            FROM `bigquery-public-data.idc_current.qualitative_measurements` qual
            JOIN `bigquery-public-data.idc_current.quantitative_measurements` vol
              ON qual.SOPInstanceUID = vol.SOPInstanceUID
              AND qual.measurementGroup_number = vol.measurementGroup_number
            JOIN `bigquery-public-data.idc_current.quantitative_measurements` diam
              ON qual.SOPInstanceUID = diam.SOPInstanceUID
              AND qual.measurementGroup_number = diam.measurementGroup_number
            WHERE qual.Quantity.CodeMeaning = 'Malignancy'
              AND vol.Quantity.CodeMeaning = 'Volume'
              AND diam.Quantity.CodeMeaning = 'Diameter'
            ORDER BY qual.PatientID, qual.trackingIdentifier
            LIMIT 20
        """)

    def test_all_three_derived_tables(self):
        assert_valid("""
            SELECT
              seg.SegmentedPropertyType.CodeMeaning AS structure,
              qual.Quantity.CodeMeaning AS qualitative_feature,
              qual.Value.CodeMeaning AS qualitative_value,
              qm.Quantity.CodeMeaning AS quantitative_feature,
              ROUND(CAST(qm.Value AS FLOAT64), 3) AS numeric_value,
              qm.Units.CodeMeaning AS units,
              img.collection_id
            FROM `bigquery-public-data.idc_current.segmentations` seg
            JOIN `bigquery-public-data.idc_current.qualitative_measurements` qual
              ON seg.SeriesInstanceUID = qual.segmentationSeriesUID
              AND seg.SegmentNumber = qual.segmentationSegmentNumber
            JOIN `bigquery-public-data.idc_current.quantitative_measurements` qm
              ON qual.SOPInstanceUID = qm.SOPInstanceUID
              AND qual.measurementGroup_number = qm.measurementGroup_number
            JOIN `bigquery-public-data.idc_current.dicom_all` img
              ON seg.segmented_SeriesInstanceUID = img.SeriesInstanceUID
            WHERE seg.SegmentedPropertyType.CodeMeaning = 'Neoplasm'
            LIMIT 10
        """)


# ===========================================================================
# Private DICOM elements
# ===========================================================================

class TestPrivateElements:
    def test_discover_available_private_tags(self):
        assert_valid("""
            SELECT
              other_elements.Tag,
              COUNT(*) AS instance_count,
              ARRAY_AGG(DISTINCT other_elements.Data[SAFE_OFFSET(0)] IGNORE NULLS LIMIT 5) AS sample_values
            FROM `bigquery-public-data.idc_current.dicom_all`,
              UNNEST(OtherElements) AS other_elements
            WHERE collection_id = 'qin_prostate_repeatability'
              AND Modality = 'MR'
              AND ARRAY_LENGTH(other_elements.Data) > 0
              AND other_elements.Data[SAFE_OFFSET(0)] IS NOT NULL
              AND other_elements.Data[SAFE_OFFSET(0)] != ''
            GROUP BY other_elements.Tag
            ORDER BY instance_count DESC
        """)

    def test_private_tags_for_specific_series(self):
        assert_valid("""
            SELECT
              other_elements.Tag,
              ARRAY_AGG(DISTINCT other_elements.Data[SAFE_OFFSET(0)] IGNORE NULLS) AS values
            FROM `bigquery-public-data.idc_current.dicom_all`,
              UNNEST(OtherElements) AS other_elements
            WHERE SeriesInstanceUID = '1.3.6.1.4.1.14519.5.2.1.7311.5101.206828891270520544417996275680'
              AND ARRAY_LENGTH(other_elements.Data) > 0
              AND other_elements.Data[SAFE_OFFSET(0)] IS NOT NULL
              AND other_elements.Data[SAFE_OFFSET(0)] != ''
            GROUP BY other_elements.Tag
        """)

    def test_identify_manufacturer(self):
        assert_valid("""
            SELECT DISTINCT Manufacturer, ManufacturerModelName
            FROM `bigquery-public-data.idc_current.dicom_all`
            WHERE collection_id = 'qin_prostate_repeatability'
              AND Modality = 'MR'
        """)

    def test_access_private_element_values(self):
        assert_valid("""
            SELECT
              SeriesInstanceUID,
              SeriesDescription,
              other_elements.Data[SAFE_OFFSET(0)] AS b_value
            FROM `bigquery-public-data.idc_current.dicom_all`,
              UNNEST(OtherElements) AS other_elements
            WHERE collection_id = 'qin_prostate_repeatability'
              AND other_elements.Tag = 'Tag_00431039'
            LIMIT 10
        """)

    def test_aggregate_private_values_by_series(self):
        assert_valid("""
            SELECT
              SeriesInstanceUID,
              ANY_VALUE(SeriesDescription) AS SeriesDescription,
              ARRAY_AGG(DISTINCT other_elements.Data[SAFE_OFFSET(0)]) AS b_values
            FROM `bigquery-public-data.idc_current.dicom_all`,
              UNNEST(OtherElements) AS other_elements
            WHERE collection_id = 'qin_prostate_repeatability'
              AND other_elements.Tag = 'Tag_00431039'
            GROUP BY SeriesInstanceUID
        """)

    def test_combine_standard_and_private_filters(self):
        assert_valid("""
            SELECT
              PatientID,
              SeriesInstanceUID,
              ANY_VALUE(SeriesDescription) AS SeriesDescription,
              ARRAY_AGG(DISTINCT other_elements.Data[SAFE_OFFSET(0)]) AS b_values,
              COUNT(DISTINCT SOPInstanceUID) AS n_slices
            FROM `bigquery-public-data.idc_current.dicom_all`,
              UNNEST(OtherElements) AS other_elements
            WHERE collection_id = 'qin_prostate_repeatability'
              AND Modality = 'MR'
              AND other_elements.Tag = 'Tag_00431039'
              AND ImageType[SAFE_OFFSET(0)] = 'ORIGINAL'
              AND other_elements.Data[SAFE_OFFSET(0)] = '1400'
            GROUP BY PatientID, SeriesInstanceUID
            ORDER BY PatientID
        """)

    def test_cross_collection_private_tag_survey(self):
        assert_valid("""
            SELECT
              collection_id,
              ARRAY_TO_STRING(ARRAY_AGG(DISTINCT other_elements.Data[SAFE_OFFSET(0)] IGNORE NULLS), ', ') AS values_found,
              ARRAY_AGG(DISTINCT Manufacturer IGNORE NULLS) AS manufacturers
            FROM `bigquery-public-data.idc_current.dicom_all`,
              UNNEST(OtherElements) AS other_elements
            WHERE other_elements.Tag = 'Tag_00431039'
              AND other_elements.Data[SAFE_OFFSET(0)] IS NOT NULL
              AND other_elements.Data[SAFE_OFFSET(0)] != ''
            GROUP BY collection_id
            ORDER BY collection_id
        """)


# ===========================================================================
# Clinical data
# ===========================================================================

class TestClinicalBigQuery:
    def test_table_metadata(self):
        assert_valid("""
            SELECT
              collection_id,
              table_name,
              table_description
            FROM `bigquery-public-data.idc_current_clinical.table_metadata`
            WHERE collection_id = 'nlst'
        """)

    def test_column_metadata(self):
        assert_valid("""
            SELECT
              collection_id,
              table_name,
              column,
              column_label,
              data_type,
              values
            FROM `bigquery-public-data.idc_current_clinical.column_metadata`
            WHERE collection_id = 'nlst'
              AND column_label LIKE '%stage%'
        """)

    def test_list_available_clinical_tables(self):
        assert_valid("""
            SELECT table_name
            FROM `bigquery-public-data.idc_current_clinical.INFORMATION_SCHEMA.TABLES`
            WHERE table_name NOT IN ('table_metadata', 'column_metadata')
        """)

    def test_find_collections_with_clinical_attributes(self):
        assert_valid("""
            SELECT DISTINCT collection_id, table_name, column, column_label
            FROM `bigquery-public-data.idc_current_clinical.column_metadata`
            WHERE LOWER(column_label) LIKE '%chemotherapy%'
        """)

    def test_nlst_cancer_staging(self):
        assert_valid("""
            SELECT
              dicom_patient_id,
              clinical_stag,
              path_stag,
              de_stag
            FROM `bigquery-public-data.idc_current_clinical.nlst_canc`
            WHERE clinical_stag IS NOT NULL
            LIMIT 10
        """)

    def test_join_clinical_with_imaging(self):
        assert_valid("""
            SELECT
              d.PatientID,
              d.StudyInstanceUID,
              d.Modality,
              c.clinical_stag,
              c.path_stag
            FROM `bigquery-public-data.idc_current.dicom_all` d
            JOIN `bigquery-public-data.idc_current_clinical.nlst_canc` c
              ON d.PatientID = c.dicom_patient_id
            WHERE d.collection_id = 'nlst'
              AND d.Modality = 'CT'
              AND c.clinical_stag = '400'
            LIMIT 20
        """)

    def test_cross_collection_clinical_search(self):
        assert_valid("""
            SELECT
              cm.collection_id,
              cm.table_name,
              cm.column,
              cm.column_label
            FROM `bigquery-public-data.idc_current_clinical.column_metadata` cm
            WHERE LOWER(cm.column_label) LIKE '%stage%'
            ORDER BY cm.collection_id
        """)

    def test_information_schema_columns(self):
        assert_valid("""
            SELECT column_name, data_type
            FROM `bigquery-public-data.idc_current_clinical.INFORMATION_SCHEMA.COLUMNS`
            WHERE table_name = 'nlst_canc'
        """)
