"""
Regression tests for all queries and code snippets documented in the IDC Claude Skill.

Covers: SKILL.md, references/sql_patterns.md, references/index_tables_guide.md,
        references/clinical_data_guide.md

Excluded (require auth or network I/O beyond metadata):
  - Actual DICOM downloads
  - DICOMweb endpoints
  - Direct S3/GCS access
  - pydicom / SimpleITK integration (no downloaded files)

BigQuery snippets are covered separately in test_bq_snippets.py (uses bq CLI dry-run).
"""

import pandas as pd
import pytest
import idc_index
from idc_index import IDCClient


# ---------------------------------------------------------------------------
# Shared client fixture – one per test session to avoid re-downloading indices
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def client():
    return IDCClient()


@pytest.fixture(scope="session")
def client_with_all_indices(client):
    """Client with every on-demand index pre-fetched."""
    for table in [
        "collections_index",
        "analysis_results_index",
        "clinical_index",
        "sm_index",
        "seg_index",
        "ann_index",
        "ann_group_index",
        "contrast_index",
        "volume_geometry_index",
        "rtstruct_index",
        "version_metadata_index",
    ]:
        client.fetch_index(table)
    return client


# ===========================================================================
# SKILL.md – Version and setup
# ===========================================================================

class TestVersionAndSetup:
    """SKILL.md: version check and IDC data version."""

    def test_package_version_meets_requirement(self):
        required = "0.12.2"
        assert idc_index.__version__ >= required, (
            f"idc-index {idc_index.__version__} < required {required}"
        )

    def test_idc_data_version_is_v24(self, client):
        assert client.get_idc_version() == "v24"

    def test_series_version_columns_present(self, client):
        cols = client.index.columns.tolist()
        assert "series_init_idc_version" in cols
        assert "series_revised_idc_version" in cols

    def test_version_metadata_index_available(self, client):
        assert "version_metadata_index" in client.indices_overview
        assert client.indices_overview["version_metadata_index"]["installed"]

    def test_version_metadata_index_query(self, client_with_all_indices):
        df = client_with_all_indices.sql_query(
            "SELECT idc_version, version_timestamp FROM version_metadata_index ORDER BY idc_version"
        )
        assert len(df) > 0
        assert "idc_version" in df.columns
        assert "version_timestamp" in df.columns

    def test_series_version_columns_query(self, client):
        df = client.sql_query("""
            SELECT SeriesInstanceUID, series_init_idc_version, series_revised_idc_version
            FROM index
            WHERE series_init_idc_version IS NOT NULL
            LIMIT 10
        """)
        assert len(df) > 0

    def test_join_index_with_version_metadata(self, client_with_all_indices):
        df = client_with_all_indices.sql_query("""
            SELECT i.SeriesInstanceUID, i.series_init_idc_version, v.version_timestamp
            FROM index i
            JOIN version_metadata_index v ON i.series_init_idc_version = v.idc_version
            LIMIT 5
        """)
        assert len(df) > 0
        assert "version_timestamp" in df.columns


# ===========================================================================
# SKILL.md – Overall statistics
# ===========================================================================

class TestOverallStats:
    """SKILL.md: data statistics snippet."""

    def test_stats_query(self, client):
        df = client.sql_query("""
            SELECT
                COUNT(DISTINCT collection_id) as collections,
                COUNT(DISTINCT analysis_result_id) as analysis_results,
                COUNT(DISTINCT PatientID) as patients,
                COUNT(DISTINCT StudyInstanceUID) as studies,
                COUNT(DISTINCT SeriesInstanceUID) as series,
                SUM(instanceCount) as instances,
                SUM(series_size_MB)/1000000 as size_TB
            FROM index
        """)
        assert len(df) == 1
        row = df.iloc[0]
        assert row["collections"] > 0
        assert row["series"] > 0


# ===========================================================================
# SKILL.md – Data discovery
# ===========================================================================

class TestDataDiscovery:
    """SKILL.md: §1 Data Discovery and Exploration."""

    def test_collections_summary(self, client):
        df = client.sql_query("""
            SELECT
              collection_id,
              COUNT(DISTINCT PatientID) as patients,
              COUNT(DISTINCT SeriesInstanceUID) as series,
              SUM(series_size_MB) as size_mb
            FROM index
            GROUP BY collection_id
            ORDER BY patients DESC
        """)
        assert len(df) > 0
        assert "collection_id" in df.columns

    def test_collections_index(self, client_with_all_indices):
        df = client_with_all_indices.sql_query("""
            SELECT collection_id, cancer_types, tumor_locations, species, subjects, supporting_data
            FROM collections_index
        """)
        assert len(df) > 0

    def test_analysis_results_index(self, client_with_all_indices):
        df = client_with_all_indices.sql_query("""
            SELECT analysis_result_id, analysis_result_title, subjects, collections, modalities
            FROM analysis_results_index
        """)
        assert len(df) > 0

    def test_analysis_results_index_column_names(self, client_with_all_indices):
        cols = client_with_all_indices.analysis_results_index.columns.tolist()
        for expected in ("updated", "description"):
            assert expected in cols, f"Expected lowercase column '{expected}' in analysis_results_index"
        assert "Updated" not in cols
        assert "Description" not in cols


# ===========================================================================
# SKILL.md – SQL queries
# ===========================================================================

class TestSQLQueries:
    """SKILL.md: §2 Querying Metadata with SQL."""

    def test_modalities_with_counts(self, client):
        df = client.sql_query("""
            SELECT DISTINCT Modality, COUNT(*) as series_count
            FROM index
            GROUP BY Modality
            ORDER BY series_count DESC
        """)
        assert len(df) > 0
        assert "CT" in df["Modality"].tolist()

    def test_body_parts_for_mr(self, client):
        df = client.sql_query("""
            SELECT DISTINCT BodyPartExamined, COUNT(*) as series_count
            FROM index
            WHERE Modality = 'MR' AND BodyPartExamined IS NOT NULL
            GROUP BY BodyPartExamined
            ORDER BY series_count DESC
            LIMIT 20
        """)
        assert len(df) > 0

    def test_breast_mri_query(self, client):
        df = client.sql_query("""
            SELECT
              collection_id, PatientID, SeriesInstanceUID,
              Modality, SeriesDescription, license_short_name
            FROM index
            WHERE Modality = 'MR' AND BodyPartExamined = 'BREAST'
            LIMIT 20
        """)
        assert df is not None

    def test_join_collections_index_breast(self, client_with_all_indices):
        df = client_with_all_indices.sql_query("""
            SELECT i.collection_id, i.PatientID, i.SeriesInstanceUID, i.Modality
            FROM index i
            JOIN collections_index c ON i.collection_id = c.collection_id
            WHERE c.cancer_types LIKE '%Breast%' AND i.Modality = 'MR'
            LIMIT 20
        """)
        assert df is not None


# ===========================================================================
# SKILL.md – Licenses and citations
# ===========================================================================

class TestLicensesAndCitations:
    """SKILL.md: §5 Licenses and citations."""

    def test_license_query(self, client):
        df = client.sql_query("""
            SELECT DISTINCT
              collection_id,
              license_short_name,
              COUNT(DISTINCT SeriesInstanceUID) as series_count
            FROM index
            GROUP BY collection_id, license_short_name
            ORDER BY collection_id
        """)
        assert len(df) > 0
        assert "license_short_name" in df.columns

    def test_citations_apa(self, client):
        citations = client.citations_from_selection(collection_id="rider_pilot")
        assert len(citations) > 0

    def test_citations_bibtex(self, client):
        citations = client.citations_from_selection(
            collection_id="rider_pilot",
            citation_format=IDCClient.CITATION_FORMAT_BIBTEX,
        )
        assert len(citations) > 0

    def test_citations_from_series(self, client):
        df = client.sql_query(
            "SELECT SeriesInstanceUID FROM index WHERE collection_id = 'tcga_luad' LIMIT 5"
        )
        citations = client.citations_from_selection(
            seriesInstanceUID=list(df["SeriesInstanceUID"].values)
        )
        assert citations is not None


# ===========================================================================
# SKILL.md – Batch processing and manifest generation
# ===========================================================================

class TestBatchAndManifest:
    """SKILL.md: §6 Batch Processing; Command-Line Download / manifest."""

    def test_batch_filter_query(self, client):
        df = client.sql_query("""
            SELECT SeriesInstanceUID, PatientID, collection_id, ManufacturerModelName
            FROM index
            WHERE Modality = 'CT'
              AND BodyPartExamined = 'CHEST'
              AND Manufacturer = 'GE MEDICAL SYSTEMS'
              AND license_short_name = 'CC BY 4.0'
            LIMIT 100
        """)
        assert df is not None

    def test_manifest_generation_query(self, client):
        df = client.sql_query("""
            SELECT series_aws_url
            FROM index
            WHERE collection_id = 'rider_pilot' AND Modality = 'CT'
        """)
        assert len(df) > 0
        assert "series_aws_url" in df.columns


# ===========================================================================
# SKILL.md – Viewer URLs
# ===========================================================================

class TestViewerURLs:
    """SKILL.md: §4 Visualizing IDC Images."""

    @pytest.fixture(scope="class")
    def rider_pilot_row(self, client):
        df = client.sql_query("""
            SELECT SeriesInstanceUID, StudyInstanceUID
            FROM index
            WHERE collection_id = 'rider_pilot' AND Modality = 'CT'
            LIMIT 1
        """)
        return df.iloc[0]

    def test_viewer_url_series(self, client, rider_pilot_row):
        url = client.get_viewer_URL(seriesInstanceUID=rider_pilot_row["SeriesInstanceUID"])
        assert url.startswith("http")

    def test_viewer_url_study(self, client, rider_pilot_row):
        url = client.get_viewer_URL(studyInstanceUID=rider_pilot_row["StudyInstanceUID"])
        assert url.startswith("http")


# ===========================================================================
# index_tables_guide.md
# ===========================================================================

class TestIndexTablesGuide:
    """references/index_tables_guide.md."""

    def test_primary_index_sql(self, client):
        df = client.sql_query("SELECT * FROM index WHERE Modality = 'CT' LIMIT 10")
        assert len(df) == 10

    def test_collections_index_sql(self, client_with_all_indices):
        df = client_with_all_indices.sql_query(
            "SELECT collection_id, cancer_types, tumor_locations FROM collections_index"
        )
        assert len(df) > 0

    def test_analysis_results_sql(self, client_with_all_indices):
        df = client_with_all_indices.sql_query(
            "SELECT * FROM analysis_results_index LIMIT 5"
        )
        assert len(df) > 0

    def test_primary_index_dataframe(self, client):
        df = client.index
        assert df is not None and len(df) > 0

    def test_sm_index_dataframe(self, client_with_all_indices):
        sm_df = client_with_all_indices.sm_index
        assert sm_df is not None

    def test_indices_overview_structure(self, client):
        for name, info in client.indices_overview.items():
            assert "installed" in info, f"'installed' missing for {name}"
            assert "description" in info, f"'description' missing for {name}"

    def test_schema_discovery_via_indices_overview(self, client):
        schema = client.indices_overview["index"]["schema"]
        assert "table_description" in schema
        assert "columns" in schema
        assert len(schema["columns"]) > 0

    def test_get_index_schema(self, client):
        schema = client.get_index_schema("index")
        assert "table_description" in schema
        assert "columns" in schema


# ===========================================================================
# sql_patterns.md – Filter discovery
# ===========================================================================

class TestFilterDiscovery:
    """references/sql_patterns.md – Discover Available Filter Values."""

    def test_distinct_modalities(self, client):
        df = client.sql_query("SELECT DISTINCT Modality FROM index")
        assert len(df) > 0

    def test_body_parts_ct(self, client):
        df = client.sql_query("""
            SELECT DISTINCT BodyPartExamined, COUNT(*) as n
            FROM index WHERE Modality = 'CT' AND BodyPartExamined IS NOT NULL
            GROUP BY BodyPartExamined ORDER BY n DESC
        """)
        assert len(df) > 0

    def test_manufacturers_mr(self, client):
        df = client.sql_query("""
            SELECT DISTINCT Manufacturer, COUNT(*) as n
            FROM index WHERE Modality = 'MR'
            GROUP BY Manufacturer ORDER BY n DESC
        """)
        assert len(df) > 0


# ===========================================================================
# sql_patterns.md – Annotations and segmentations
# ===========================================================================

class TestAnnotationsAndSegmentations:
    """references/sql_patterns.md – Find Annotations and Segmentations."""

    def test_seg_rtstruct_by_modality(self, client):
        df = client.sql_query("""
            SELECT collection_id, Modality, COUNT(*) as series_count
            FROM index
            WHERE Modality IN ('SEG', 'RTSTRUCT')
            GROUP BY collection_id, Modality
            ORDER BY series_count DESC
        """)
        assert df is not None

    def test_segmentations_tcga_luad(self, client):
        df = client.sql_query("""
            SELECT SeriesInstanceUID, SeriesDescription, analysis_result_id
            FROM index
            WHERE collection_id = 'tcga_luad' AND Modality = 'SEG'
        """)
        assert df is not None

    def test_analysis_results_for_tcga_luad(self, client_with_all_indices):
        df = client_with_all_indices.sql_query("""
            SELECT analysis_result_id, analysis_result_title
            FROM analysis_results_index
            WHERE collections LIKE '%tcga_luad%'
        """)
        assert df is not None

    def test_seg_index_by_algorithm(self, client_with_all_indices):
        df = client_with_all_indices.sql_query("""
            SELECT AlgorithmName, AlgorithmType, COUNT(*) as seg_count
            FROM seg_index
            WHERE AlgorithmName IS NOT NULL
            GROUP BY AlgorithmName, AlgorithmType
            ORDER BY seg_count DESC
            LIMIT 10
        """)
        assert df is not None

    def test_seg_join_chest_ct(self, client_with_all_indices):
        df = client_with_all_indices.sql_query("""
            SELECT
                s.SeriesInstanceUID as seg_series,
                s.AlgorithmName,
                s.total_segments,
                s.segmented_SeriesInstanceUID as source_series
            FROM seg_index s
            JOIN index src ON s.segmented_SeriesInstanceUID = src.SeriesInstanceUID
            WHERE src.Modality = 'CT' AND src.BodyPartExamined = 'CHEST'
            LIMIT 10
        """)
        assert df is not None

    def test_totalsegmentator_query(self, client_with_all_indices):
        df = client_with_all_indices.sql_query("""
            SELECT
                seg_info.collection_id,
                COUNT(DISTINCT s.SeriesInstanceUID) as seg_count,
                SUM(s.total_segments) as total_segments
            FROM seg_index s
            JOIN index seg_info ON s.SeriesInstanceUID = seg_info.SeriesInstanceUID
            WHERE s.AlgorithmName LIKE '%TotalSegmentator%'
            GROUP BY seg_info.collection_id
            ORDER BY seg_count DESC
        """)
        assert df is not None

    def test_ann_group_index_query(self, client_with_all_indices):
        df = client_with_all_indices.sql_query("""
            SELECT g.AnnotationGroupLabel, g.GraphicType, g.NumberOfAnnotations, i.collection_id
            FROM ann_group_index g
            JOIN ann_index a ON g.SeriesInstanceUID = a.SeriesInstanceUID
            JOIN index i ON a.SeriesInstanceUID = i.SeriesInstanceUID
            WHERE g.AlgorithmName IS NOT NULL
            LIMIT 10
        """)
        assert df is not None


# ===========================================================================
# sql_patterns.md – Size estimation
# ===========================================================================

class TestSizeEstimation:
    """references/sql_patterns.md – Estimate Download Size."""

    def test_size_estimation_nlst(self, client):
        df = client.sql_query("""
            SELECT SUM(series_size_MB) as total_mb, COUNT(*) as series_count
            FROM index
            WHERE collection_id = 'nlst' AND Modality = 'CT'
        """)
        assert len(df) == 1
        assert df.iloc[0]["series_count"] > 0


# ===========================================================================
# sql_patterns.md – Volume geometry and RT Structure Sets
# ===========================================================================

class TestVolumeGeometryAndRTSTRUCT:
    """references/sql_patterns.md – Volume Geometry Validation and RT Structure Sets."""

    def test_volume_geometry_valid_ct(self, client_with_all_indices):
        df = client_with_all_indices.sql_query("""
            SELECT i.collection_id, i.SeriesInstanceUID, i.BodyPartExamined,
                   v.obliquity_degrees
            FROM index i
            JOIN volume_geometry_index v ON i.SeriesInstanceUID = v.SeriesInstanceUID
            WHERE i.Modality = 'CT'
              AND v.regularly_spaced_3d_volume = TRUE
            LIMIT 10
        """)
        assert df is not None

    def test_volume_geometry_fraction_per_collection(self, client_with_all_indices):
        df = client_with_all_indices.sql_query("""
            SELECT i.collection_id,
                   COUNT(*) as total_ct,
                   SUM(CASE WHEN v.regularly_spaced_3d_volume THEN 1 ELSE 0 END) as valid_3d,
                   ROUND(100.0 * SUM(CASE WHEN v.regularly_spaced_3d_volume THEN 1 ELSE 0 END)
                         / COUNT(*), 1) as pct_valid
            FROM index i
            JOIN volume_geometry_index v ON i.SeriesInstanceUID = v.SeriesInstanceUID
            WHERE i.Modality = 'CT'
            GROUP BY i.collection_id
            ORDER BY total_ct DESC
            LIMIT 10
        """)
        assert len(df) > 0

    def test_rtstruct_index_query(self, client_with_all_indices):
        df = client_with_all_indices.sql_query("""
            SELECT i.collection_id, i.SeriesInstanceUID,
                   r.total_rois, r.ROINames, r.RTROIInterpretedTypes,
                   r.referenced_SeriesInstanceUID
            FROM index i
            JOIN rtstruct_index r ON i.SeriesInstanceUID = r.SeriesInstanceUID
            LIMIT 10
        """)
        assert df is not None

    def test_rtstruct_per_collection(self, client_with_all_indices):
        df = client_with_all_indices.sql_query("""
            SELECT i.collection_id,
                   COUNT(*) as rtstruct_series,
                   ROUND(AVG(r.total_rois), 1) as avg_rois
            FROM index i
            JOIN rtstruct_index r ON i.SeriesInstanceUID = r.SeriesInstanceUID
            GROUP BY i.collection_id
            ORDER BY rtstruct_series DESC
            LIMIT 10
        """)
        assert df is not None

    def test_rtstruct_source_ct(self, client_with_all_indices):
        df = client_with_all_indices.sql_query("""
            SELECT r.SeriesInstanceUID as rtstruct_uid,
                   r.total_rois, r.ROINames,
                   src.SeriesInstanceUID as source_ct_uid,
                   src.collection_id, src.BodyPartExamined
            FROM rtstruct_index r
            JOIN index src ON r.referenced_SeriesInstanceUID = src.SeriesInstanceUID
            LIMIT 10
        """)
        assert df is not None


# ===========================================================================
# sql_patterns.md – Clinical data link and slide microscopy
# ===========================================================================

class TestClinicalLinkAndSM:
    """references/sql_patterns.md – Link to Clinical Data and Slide Microscopy."""

    def test_clinical_index_summary(self, client_with_all_indices):
        df = client_with_all_indices.sql_query("""
            SELECT collection_id, table_name, COUNT(DISTINCT column_label) as columns
            FROM clinical_index
            GROUP BY collection_id, table_name
            ORDER BY collection_id
        """)
        assert len(df) > 0

    def test_sm_index_join(self, client_with_all_indices):
        df = client_with_all_indices.sql_query("""
            SELECT i.collection_id, COUNT(*) as sm_series
            FROM index i
            JOIN sm_index s ON i.SeriesInstanceUID = s.SeriesInstanceUID
            GROUP BY i.collection_id
            ORDER BY sm_series DESC
            LIMIT 10
        """)
        assert df is not None

    def test_contrast_index_join(self, client_with_all_indices):
        df = client_with_all_indices.sql_query("""
            SELECT i.SeriesInstanceUID, i.Modality, i.collection_id
            FROM index i
            JOIN contrast_index c ON i.SeriesInstanceUID = c.SeriesInstanceUID
            LIMIT 10
        """)
        assert df is not None


# ===========================================================================
# clinical_data_guide.md
# ===========================================================================

class TestClinicalDataGuide:
    """references/clinical_data_guide.md."""

    def test_clinical_index_columns(self, client_with_all_indices):
        cols = client_with_all_indices.clinical_index.columns.tolist()
        for expected in ("collection_id", "short_table_name", "column", "column_label"):
            assert expected in cols, f"Expected column '{expected}' in clinical_index"

    def test_collections_with_clinical_data(self, client_with_all_indices):
        collections = client_with_all_indices.clinical_index["collection_id"].unique().tolist()
        assert len(collections) > 0

    def test_nlst_has_clinical_columns(self, client_with_all_indices):
        nlst_rows = client_with_all_indices.clinical_index[
            client_with_all_indices.clinical_index["collection_id"] == "nlst"
        ]
        assert len(nlst_rows) > 0

    def test_search_stage_attributes(self, client_with_all_indices):
        stage_attrs = client_with_all_indices.clinical_index[
            client_with_all_indices.clinical_index["column_label"].str.contains(
                "[Ss]tage", na=False
            )
        ]
        assert len(stage_attrs) > 0

    def test_load_clinical_table_nlst_canc(self, client_with_all_indices):
        df = client_with_all_indices.get_clinical_table("nlst_canc")
        assert df is not None
        assert len(df) > 0
        assert "dicom_patient_id" in df.columns

    def test_coded_values_mapping(self, client_with_all_indices):
        nlst_rows = client_with_all_indices.clinical_index[
            client_with_all_indices.clinical_index["collection_id"] == "nlst"
        ]
        stag_rows = nlst_rows[nlst_rows["column"] == "clinical_stag"]
        if len(stag_rows) == 0:
            pytest.skip("clinical_stag column not present in this idc-index version")
        values = stag_rows["values"].values[0]
        mapping = {item["option_code"]: item["option_description"] for item in values}
        assert len(mapping) > 0

    def test_join_clinical_imaging_pandas(self, client_with_all_indices):
        nlst_canc = client_with_all_indices.get_clinical_table("nlst_canc")
        nlst_imaging = client_with_all_indices.index[
            (client_with_all_indices.index["collection_id"] == "nlst")
            & (client_with_all_indices.index["Modality"] == "CT")
        ]
        merged = pd.merge(
            nlst_imaging[["PatientID", "StudyInstanceUID"]].drop_duplicates(),
            nlst_canc[["dicom_patient_id"]],
            left_on="PatientID",
            right_on="dicom_patient_id",
            how="inner",
        )
        assert len(merged) > 0

    def test_join_clinical_imaging_sql(self, client_with_all_indices):
        # Clinical tables loaded via get_clinical_table() are not auto-registered
        # in DuckDB. Register manually before joining in SQL.
        nlst_canc_df = client_with_all_indices.get_clinical_table("nlst_canc")
        client_with_all_indices._duckdb_conn.register("nlst_canc", nlst_canc_df)
        df = client_with_all_indices.sql_query("""
            SELECT index.PatientID, index.StudyInstanceUID, index.Modality
            FROM index
            JOIN nlst_canc ON index.PatientID = nlst_canc.dicom_patient_id
            WHERE index.collection_id = 'nlst' AND index.Modality = 'CT'
        """)
        assert len(df) > 0

    def test_chemo_collections(self, client_with_all_indices):
        chemo = client_with_all_indices.clinical_index[
            client_with_all_indices.clinical_index["column_label"].str.contains(
                "[Cc]hemotherapy", na=False
            )
        ]["collection_id"].unique()
        assert chemo is not None  # may be empty – just verify it runs

    def test_patient_overlap_nlst(self, client_with_all_indices):
        nlst_canc = client_with_all_indices.get_clinical_table("nlst_canc")
        imaging_patients = set(
            client_with_all_indices.index[
                client_with_all_indices.index["collection_id"] == "nlst"
            ]["PatientID"].unique()
        )
        clinical_patients = set(nlst_canc["dicom_patient_id"].unique())
        overlap = imaging_patients & clinical_patients
        assert len(overlap) > 0
