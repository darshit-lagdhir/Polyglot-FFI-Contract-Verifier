from datetime import datetime, timezone, timedelta

now = datetime.now(timezone.utc)
print(f"ISO: {now.isoformat()}")
iso_z = now.isoformat().replace("+00:00", "Z")
print(f"ISO Z: {iso_z}")

parsed = datetime.fromisoformat(iso_z.replace("Z", "+00:00"))
print(f"Parsed: {parsed}")
print(f"Equal: {now == parsed}")
