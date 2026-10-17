
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SET statement_timeout = 5000")
    cursor.execute(
        "SELECT code, subject_id FROM subjects_cefrlevel LIMIT 10"
    )
    print("CEFR yozuvlari:", cursor.fetchall())

    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'subjects_cefrlevel'
        ORDER BY ordinal_position
    """)
    print("Jadval ustunlari:", cursor.fetchall())
