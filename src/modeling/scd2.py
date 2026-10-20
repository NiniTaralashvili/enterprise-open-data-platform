"""SCD Type 2 demonstration using in-memory records and ISO dates."""


def scd2_upsert(existing_rows, new_version, key_field, tracked_fields, effective_date):
    current_row = next(
        (row for row in existing_rows
         if row[key_field] == new_version[key_field] and row.get("is_current")),
        None,
    )
    if current_row is not None:
        changed = any(
            current_row.get(field) != new_version.get(field)
            for field in tracked_fields
        )
        if not changed:
            return existing_rows
        if effective_date <= current_row["valid_from"]:
            raise ValueError("New version must start after the current version.")

    result = [
        {**row, "valid_to": effective_date, "is_current": False}
        if row is current_row else dict(row)
        for row in existing_rows
    ]
    result.append({
        **new_version,
        "valid_from": effective_date,
        "valid_to": None,
        "is_current": True,
    })
    return result


if __name__ == "__main__":
    original = {"city": "Tbilisi", "latitude": 41.7151, "longitude": 44.8271}
    tracked = ["latitude", "longitude"]

    rows = scd2_upsert([], original, "city", tracked, "2026-08-01")
    assert len(rows) == 1
    assert rows[0]["is_current"] is True
    assert rows[0]["valid_from"] == "2026-08-01"
    assert rows[0]["valid_to"] is None
    print("Test 1 OK: first version created")

    unchanged = scd2_upsert(rows, original, "city", tracked, "2026-09-01")
    assert unchanged == rows
    assert len(unchanged) == 1
    print("Test 2 OK: unchanged data creates no version")

    corrected = {**original, "latitude": 41.7152}
    updated = scd2_upsert(rows, corrected, "city", tracked, "2026-09-01")
    assert len(updated) == 2
    assert updated[0]["is_current"] is False
    assert updated[0]["valid_to"] == "2026-09-01"
    assert updated[0]["latitude"] == 41.7151
    assert updated[1]["is_current"] is True
    assert updated[1]["valid_from"] == "2026-09-01"
    assert updated[1]["valid_to"] is None
    assert updated[1]["latitude"] == 41.7152
    assert rows[0]["is_current"] is True
    print("Test 3 OK: old version closed, new version created")
    print("All 3 tests passed")
