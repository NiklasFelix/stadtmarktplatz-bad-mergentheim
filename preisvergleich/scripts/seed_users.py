"""Legt die initialen Benutzerkonten an (einmalig, z.B. beim ersten Deployment).
Passwoerter sollten danach von den jeweiligen Nutzern geaendert werden
(Passwort-Aenderung ist ueber PUT /auth/me/password moeglich).

Aufruf: python scripts/seed_users.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api"))

from common.db import get_cursor
from app.auth import hash_password

USERS = [
    {"username": "admin", "name": "Admin", "role": "admin", "password": "admin1234"},
    {"username": "einkauf", "name": "Einkauf", "role": "einkauf", "password": "einkauf1234"},
    {"username": "lager", "name": "Lager", "role": "lager", "password": "lager1234"},
    {"username": "management", "name": "Management", "role": "management", "password": "management1234"},
]


def main():
    with get_cursor() as cur:
        for u in USERS:
            cur.execute("SELECT id FROM users WHERE username = %s", (u["username"],))
            if cur.fetchone():
                print(f"existiert bereits: {u['username']}")
                continue
            cur.execute(
                "INSERT INTO users (username, password_hash, name, role) VALUES (%s, %s, %s, %s)",
                (u["username"], hash_password(u["password"]), u["name"], u["role"]),
            )
            print(f"angelegt: {u['username']} / Rolle {u['role']} / Passwort {u['password']}")


if __name__ == "__main__":
    main()
