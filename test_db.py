#!/usr/bin/env python
# -*- coding: utf-8 -*-

from database import Database

print("[TEST] Database test basliyor...")

db = Database()

print("\n[TEST] Baglandı, tablolar kontrol ediliyor...")

with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f"\n[OK] {len(tables)} tablo bulundu:\n")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Her tablonun kaç satırı olduğunu kontrol et
    print("\n[TEST] Tablo satir sayilari:\n")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  - {table_name}: {count} satir")

print("\n[OK] Database test tamamlandi!")
