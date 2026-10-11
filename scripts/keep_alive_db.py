"""Gửi vài truy vấn đọc tới Postgres (Supabase) để project free tier không bị tạm dừng
(paused) do không có hoạt động trong 7 ngày. Chạy định kỳ bởi
.github/workflows/keep-alive.yml — KHÔNG ghi/sửa dữ liệu nào.

Biến môi trường: DATABASE_URL (giống hệt [database].url trong .streamlit/secrets.toml).
"""
import os
import sys

import psycopg


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("Thiếu biến môi trường DATABASE_URL.")
        return 1

    # prepare_threshold=None: pooler Supabase cổng 6543 (Transaction mode) không hỗ trợ
    # prepared statement dùng lại giữa các giao dịch.
    with psycopg.connect(url, connect_timeout=30, prepare_threshold=None) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT now()")
            print("DB time:", cur.fetchone()[0])
            for table in ("teachers", "classes", "exams", "submissions"):
                cur.execute(f"SELECT count(*) FROM {table}")
                print(f"{table}: {cur.fetchone()[0]} dòng")
    return 0


if __name__ == "__main__":
    sys.exit(main())
