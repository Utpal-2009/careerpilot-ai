
from src.utils.database import get_connection, initialize_database

VALID_STATUSES = {
    "Shortlisted",
    "Applied",
    "Interview",
    "Rejected",
    "Offer",
}


def shortlist_internship(internship):
    initialize_database()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO applications (
                internship_id, company, role, location,
                match_score, apply_url
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(internship_id) DO NOTHING
            """,
            (
                internship["id"],
                internship["company"],
                internship["role"],
                internship.get("location", ""),
                internship.get("match_score", 0),
                internship.get("apply_url", ""),
            ),
        )
        connection.commit()


def update_status(internship_id, status):
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")

    initialize_database()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE applications
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE internship_id = ?
            """,
            (status, internship_id),
        )
        connection.commit()

        return cursor.rowcount > 0


def get_applications():
    initialize_database()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM applications
            ORDER BY updated_at DESC, match_score DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]


def remove_application(internship_id):
    initialize_database()

    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM applications WHERE internship_id = ?",
            (internship_id,),
        )
        connection.commit()

        return cursor.rowcount > 0
