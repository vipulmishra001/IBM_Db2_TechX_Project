"""
MediTwin AI — Db2 Repository Layer
All database CRUD operations using parameterized prepared statements.
Never concatenates user input into SQL.
"""

import json
import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Try ibm_db import
try:
    import ibm_db
    IBM_DB_AVAILABLE = True
except ImportError:
    IBM_DB_AVAILABLE = False


class Db2Repository:
    """Repository for all Db2 CRUD operations using prepared statements."""

    def __init__(self, connection):
        """
        Args:
            connection: A Db2Connection instance (from db.connection).
        """
        self.connection = connection

    # ================================================================
    # PATIENT operations
    # ================================================================

    def create_patient(self, demo_code: str, display_name: str,
                       birth_year: Optional[int] = None) -> Optional[int]:
        """Insert a new patient. Returns patient_id."""
        sql = """
            INSERT INTO PATIENT (demo_code, display_name, birth_year)
            VALUES (?, ?, ?)
        """
        try:
            stmt = ibm_db.prepare(self.connection.conn, sql)
            ibm_db.bind_param(stmt, 1, demo_code)
            ibm_db.bind_param(stmt, 2, display_name)
            ibm_db.bind_param(stmt, 3, birth_year)
            ibm_db.execute(stmt)

            # Get the generated ID
            id_stmt = ibm_db.exec_immediate(
                self.connection.conn, "VALUES IDENTITY_VAL_LOCAL()"
            )
            row = ibm_db.fetch_tuple(id_stmt)
            patient_id = int(row[0]) if row else None
            self.connection.commit()
            return patient_id
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error creating patient: {e}")
            raise

    def get_patient(self, patient_id: int) -> Optional[Dict]:
        """Get a patient by ID."""
        sql = "SELECT * FROM PATIENT WHERE patient_id = ?"
        stmt = ibm_db.prepare(self.connection.conn, sql)
        ibm_db.bind_param(stmt, 1, patient_id)
        ibm_db.execute(stmt)
        row = ibm_db.fetch_assoc(stmt)
        return dict(row) if row else None

    def get_patient_by_code(self, demo_code: str) -> Optional[Dict]:
        """Get a patient by demo code."""
        sql = "SELECT * FROM PATIENT WHERE demo_code = ?"
        stmt = ibm_db.prepare(self.connection.conn, sql)
        ibm_db.bind_param(stmt, 1, demo_code)
        ibm_db.execute(stmt)
        row = ibm_db.fetch_assoc(stmt)
        return dict(row) if row else None

    def list_patients(self) -> List[Dict]:
        """Get all patients."""
        sql = "SELECT * FROM PATIENT ORDER BY patient_id"
        stmt = ibm_db.exec_immediate(self.connection.conn, sql)
        return self.connection.fetch_all(stmt)

    # ================================================================
    # DOCUMENT operations
    # ================================================================

    def create_document(self, patient_id: int, file_name: str,
                        document_type: str = "LAB_REPORT",
                        extracted_text: str = None,
                        source_hash: str = None) -> Optional[int]:
        """Insert a new document. Returns document_id."""
        sql = """
            INSERT INTO DOCUMENT (patient_id, file_name, document_type,
                                  extracted_text, source_hash)
            VALUES (?, ?, ?, ?, ?)
        """
        try:
            stmt = ibm_db.prepare(self.connection.conn, sql)
            ibm_db.bind_param(stmt, 1, patient_id)
            ibm_db.bind_param(stmt, 2, file_name)
            ibm_db.bind_param(stmt, 3, document_type)
            ibm_db.bind_param(stmt, 4, extracted_text)
            ibm_db.bind_param(stmt, 5, source_hash)
            ibm_db.execute(stmt)

            id_stmt = ibm_db.exec_immediate(
                self.connection.conn, "VALUES IDENTITY_VAL_LOCAL()"
            )
            row = ibm_db.fetch_tuple(id_stmt)
            doc_id = int(row[0]) if row else None
            self.connection.commit()
            return doc_id
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error creating document: {e}")
            raise

    def update_document_status(self, document_id: int, status: str,
                                extracted_text: str = None):
        """Update document parse status and optionally the extracted text."""
        if extracted_text is not None:
            sql = """
                UPDATE DOCUMENT SET parse_status = ?, extracted_text = ?
                WHERE document_id = ?
            """
            stmt = ibm_db.prepare(self.connection.conn, sql)
            ibm_db.bind_param(stmt, 1, status)
            ibm_db.bind_param(stmt, 2, extracted_text)
            ibm_db.bind_param(stmt, 3, document_id)
        else:
            sql = "UPDATE DOCUMENT SET parse_status = ? WHERE document_id = ?"
            stmt = ibm_db.prepare(self.connection.conn, sql)
            ibm_db.bind_param(stmt, 1, status)
            ibm_db.bind_param(stmt, 2, document_id)
        ibm_db.execute(stmt)
        self.connection.commit()

    def get_document(self, document_id: int) -> Optional[Dict]:
        """Get a document by ID."""
        sql = "SELECT * FROM DOCUMENT WHERE document_id = ?"
        stmt = ibm_db.prepare(self.connection.conn, sql)
        ibm_db.bind_param(stmt, 1, document_id)
        ibm_db.execute(stmt)
        row = ibm_db.fetch_assoc(stmt)
        return dict(row) if row else None

    def list_documents(self, patient_id: int = None) -> List[Dict]:
        """List documents, optionally filtered by patient."""
        if patient_id:
            sql = "SELECT * FROM DOCUMENT WHERE patient_id = ? ORDER BY uploaded_at DESC"
            stmt = ibm_db.prepare(self.connection.conn, sql)
            ibm_db.bind_param(stmt, 1, patient_id)
            ibm_db.execute(stmt)
        else:
            sql = "SELECT * FROM DOCUMENT ORDER BY uploaded_at DESC"
            stmt = ibm_db.exec_immediate(self.connection.conn, sql)
        return self.connection.fetch_all(stmt)

    # ================================================================
    # OBSERVATION operations
    # ================================================================

    def create_observation(self, patient_id: int, document_id: int,
                           test_name: str, test_code: str = None,
                           value_numeric: float = None, value_text: str = None,
                           unit: str = None, reference_low: float = None,
                           reference_high: float = None,
                           observed_at: str = None, source_page: int = None,
                           source_snippet: str = None,
                           extraction_confidence: float = None) -> Optional[int]:
        """Insert a new observation with PENDING status. Returns observation_id."""
        sql = """
            INSERT INTO OBSERVATION
                (patient_id, document_id, test_code, test_name,
                 value_numeric, value_text, unit,
                 reference_low, reference_high, observed_at,
                 source_page, source_snippet, extraction_confidence,
                 review_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
        """
        try:
            stmt = ibm_db.prepare(self.connection.conn, sql)
            ibm_db.bind_param(stmt, 1, patient_id)
            ibm_db.bind_param(stmt, 2, document_id)
            ibm_db.bind_param(stmt, 3, test_code)
            ibm_db.bind_param(stmt, 4, test_name)
            ibm_db.bind_param(stmt, 5, value_numeric)
            ibm_db.bind_param(stmt, 6, value_text)
            ibm_db.bind_param(stmt, 7, unit)
            ibm_db.bind_param(stmt, 8, reference_low)
            ibm_db.bind_param(stmt, 9, reference_high)
            ibm_db.bind_param(stmt, 10, observed_at)
            ibm_db.bind_param(stmt, 11, source_page)
            ibm_db.bind_param(stmt, 12, source_snippet)
            ibm_db.bind_param(stmt, 13, extraction_confidence)
            ibm_db.execute(stmt)

            id_stmt = ibm_db.exec_immediate(
                self.connection.conn, "VALUES IDENTITY_VAL_LOCAL()"
            )
            row = ibm_db.fetch_tuple(id_stmt)
            obs_id = int(row[0]) if row else None
            return obs_id
        except Exception as e:
            logger.error(f"Error creating observation: {e}")
            raise

    def update_observation_review(self, observation_id: int, status: str,
                                   reviewed_by: str = "REVIEWER",
                                   value_numeric: float = None,
                                   value_text: str = None,
                                   unit: str = None,
                                   observed_at: str = None):
        """Update observation review status and optionally correct values."""
        sql = """
            UPDATE OBSERVATION
            SET review_status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP,
                value_numeric = COALESCE(?, value_numeric),
                value_text = COALESCE(?, value_text),
                unit = COALESCE(?, unit),
                observed_at = COALESCE(?, observed_at)
            WHERE observation_id = ?
        """
        stmt = ibm_db.prepare(self.connection.conn, sql)
        ibm_db.bind_param(stmt, 1, status)
        ibm_db.bind_param(stmt, 2, reviewed_by)
        ibm_db.bind_param(stmt, 3, value_numeric)
        ibm_db.bind_param(stmt, 4, value_text)
        ibm_db.bind_param(stmt, 5, unit)
        ibm_db.bind_param(stmt, 6, observed_at)
        ibm_db.bind_param(stmt, 7, observation_id)
        ibm_db.execute(stmt)
        self.connection.commit()

    def get_pending_observations(self, patient_id: int = None) -> List[Dict]:
        """Get observations awaiting review."""
        if patient_id:
            sql = """
                SELECT o.*, d.file_name
                FROM OBSERVATION o
                JOIN DOCUMENT d ON o.document_id = d.document_id
                WHERE o.review_status = 'PENDING' AND o.patient_id = ?
                ORDER BY o.created_at DESC
            """
            stmt = ibm_db.prepare(self.connection.conn, sql)
            ibm_db.bind_param(stmt, 1, patient_id)
            ibm_db.execute(stmt)
        else:
            sql = """
                SELECT o.*, d.file_name
                FROM OBSERVATION o
                JOIN DOCUMENT d ON o.document_id = d.document_id
                WHERE o.review_status = 'PENDING'
                ORDER BY o.created_at DESC
            """
            stmt = ibm_db.exec_immediate(self.connection.conn, sql)
        return self.connection.fetch_all(stmt)

    def get_approved_observations(self, patient_id: int,
                                   test_code: str = None,
                                   start_date: str = None,
                                   end_date: str = None) -> List[Dict]:
        """Get approved observations for a patient, with optional filters."""
        conditions = ["o.review_status = 'APPROVED'", "o.patient_id = ?"]
        params = [patient_id]

        if test_code:
            conditions.append("o.test_code = ?")
            params.append(test_code)
        if start_date:
            conditions.append("o.observed_at >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("o.observed_at <= ?")
            params.append(end_date)

        where = " AND ".join(conditions)
        sql = f"""
            SELECT o.*, d.file_name
            FROM OBSERVATION o
            JOIN DOCUMENT d ON o.document_id = d.document_id
            WHERE {where}
            ORDER BY o.observed_at ASC
        """
        stmt = ibm_db.prepare(self.connection.conn, sql)
        for i, p in enumerate(params, 1):
            ibm_db.bind_param(stmt, i, p)
        ibm_db.execute(stmt)
        return self.connection.fetch_all(stmt)

    def get_observation(self, observation_id: int) -> Optional[Dict]:
        """Get a single observation by ID."""
        sql = """
            SELECT o.*, d.file_name
            FROM OBSERVATION o
            JOIN DOCUMENT d ON o.document_id = d.document_id
            WHERE o.observation_id = ?
        """
        stmt = ibm_db.prepare(self.connection.conn, sql)
        ibm_db.bind_param(stmt, 1, observation_id)
        ibm_db.execute(stmt)
        row = ibm_db.fetch_assoc(stmt)
        return dict(row) if row else None

    def get_distinct_test_codes(self, patient_id: int) -> List[Dict]:
        """Get distinct test codes/names for a patient (approved only)."""
        sql = """
            SELECT DISTINCT test_code, test_name
            FROM OBSERVATION
            WHERE patient_id = ? AND review_status = 'APPROVED'
            ORDER BY test_name
        """
        stmt = ibm_db.prepare(self.connection.conn, sql)
        ibm_db.bind_param(stmt, 1, patient_id)
        ibm_db.execute(stmt)
        return self.connection.fetch_all(stmt)

    def get_latest_observation(self, patient_id: int,
                                test_code: str) -> Optional[Dict]:
        """Get the most recent approved observation for a metric."""
        sql = """
            SELECT o.*, d.file_name
            FROM OBSERVATION o
            JOIN DOCUMENT d ON o.document_id = d.document_id
            WHERE o.patient_id = ? AND o.test_code = ?
                  AND o.review_status = 'APPROVED'
            ORDER BY o.observed_at DESC
            FETCH FIRST 1 ROW ONLY
        """
        stmt = ibm_db.prepare(self.connection.conn, sql)
        ibm_db.bind_param(stmt, 1, patient_id)
        ibm_db.bind_param(stmt, 2, test_code)
        ibm_db.execute(stmt)
        row = ibm_db.fetch_assoc(stmt)
        return dict(row) if row else None

    # ================================================================
    # TIMELINE_EVENT operations
    # ================================================================

    def create_timeline_event(self, patient_id: int, event_type: str,
                               event_time: str, title: str,
                               summary: str = None,
                               related_document_id: int = None) -> Optional[int]:
        """Insert a timeline event."""
        sql = """
            INSERT INTO TIMELINE_EVENT
                (patient_id, event_type, event_time, title, summary, related_document_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        stmt = ibm_db.prepare(self.connection.conn, sql)
        ibm_db.bind_param(stmt, 1, patient_id)
        ibm_db.bind_param(stmt, 2, event_type)
        ibm_db.bind_param(stmt, 3, event_time)
        ibm_db.bind_param(stmt, 4, title)
        ibm_db.bind_param(stmt, 5, summary)
        ibm_db.bind_param(stmt, 6, related_document_id)
        ibm_db.execute(stmt)
        self.connection.commit()

        id_stmt = ibm_db.exec_immediate(
            self.connection.conn, "VALUES IDENTITY_VAL_LOCAL()"
        )
        row = ibm_db.fetch_tuple(id_stmt)
        return int(row[0]) if row else None

    def get_timeline(self, patient_id: int) -> List[Dict]:
        """Get timeline events for a patient."""
        sql = """
            SELECT * FROM TIMELINE_EVENT
            WHERE patient_id = ?
            ORDER BY event_time DESC
        """
        stmt = ibm_db.prepare(self.connection.conn, sql)
        ibm_db.bind_param(stmt, 1, patient_id)
        ibm_db.execute(stmt)
        return self.connection.fetch_all(stmt)

    # ================================================================
    # AUDIT_LOG operations
    # ================================================================

    def log_audit(self, action: str, entity_type: str,
                  entity_id: int = None, actor_id: str = "SYSTEM",
                  details: dict = None):
        """Append an audit log entry."""
        sql = """
            INSERT INTO AUDIT_LOG (actor_id, action, entity_type, entity_id, details_json)
            VALUES (?, ?, ?, ?, ?)
        """
        details_json = json.dumps(details) if details else None
        stmt = ibm_db.prepare(self.connection.conn, sql)
        ibm_db.bind_param(stmt, 1, actor_id)
        ibm_db.bind_param(stmt, 2, action)
        ibm_db.bind_param(stmt, 3, entity_type)
        ibm_db.bind_param(stmt, 4, entity_id)
        ibm_db.bind_param(stmt, 5, details_json)
        ibm_db.execute(stmt)
        self.connection.commit()

    def get_audit_log(self, entity_type: str = None,
                      limit: int = 50) -> List[Dict]:
        """Get recent audit log entries."""
        if entity_type:
            sql = f"""
                SELECT * FROM AUDIT_LOG
                WHERE entity_type = ?
                ORDER BY logged_at DESC
                FETCH FIRST {int(limit)} ROWS ONLY
            """
            stmt = ibm_db.prepare(self.connection.conn, sql)
            ibm_db.bind_param(stmt, 1, entity_type)
            ibm_db.execute(stmt)
        else:
            sql = f"""
                SELECT * FROM AUDIT_LOG
                ORDER BY logged_at DESC
                FETCH FIRST {int(limit)} ROWS ONLY
            """
            stmt = ibm_db.exec_immediate(self.connection.conn, sql)
        return self.connection.fetch_all(stmt)

    # ================================================================
    # STATISTICS for Dashboard
    # ================================================================

    def get_dashboard_stats(self) -> Dict[str, int]:
        """Get summary counts for the dashboard."""
        stats = {}
        queries = {
            "total_patients": "SELECT COUNT(*) AS cnt FROM PATIENT",
            "total_documents": "SELECT COUNT(*) AS cnt FROM DOCUMENT",
            "total_observations": "SELECT COUNT(*) AS cnt FROM OBSERVATION WHERE review_status = 'APPROVED'",
            "pending_reviews": "SELECT COUNT(*) AS cnt FROM OBSERVATION WHERE review_status = 'PENDING'",
        }
        for key, sql in queries.items():
            try:
                stmt = ibm_db.exec_immediate(self.connection.conn, sql)
                row = ibm_db.fetch_assoc(stmt)
                stats[key] = int(row["CNT"]) if row else 0
            except Exception:
                stats[key] = 0
        return stats

    def search_observations_by_keyword(self, patient_id: int,
                                        keyword: str) -> List[Dict]:
        """Search approved observations by test name keyword."""
        sql = """
            SELECT o.*, d.file_name
            FROM OBSERVATION o
            JOIN DOCUMENT d ON o.document_id = d.document_id
            WHERE o.patient_id = ?
              AND o.review_status = 'APPROVED'
              AND UPPER(o.test_name) LIKE UPPER(?)
            ORDER BY o.observed_at DESC
        """
        stmt = ibm_db.prepare(self.connection.conn, sql)
        ibm_db.bind_param(stmt, 1, patient_id)
        ibm_db.bind_param(stmt, 2, f"%{keyword}%")
        ibm_db.execute(stmt)
        return self.connection.fetch_all(stmt)

