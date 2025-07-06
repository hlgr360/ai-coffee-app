import pytest
import bcrypt

# AI: Test that the admin password hash in the database matches the password 'admin'.
def test_admin_password_hash_matches():
    # This hash must match the one in init_db.sql for password 'admin'
    hash_from_sql = "$2b$12$ovQIfjnEuhQAGAOE7JCbf.bfQRGAJxl5KkqYyvXxMIVS3bxf5P6vW"
    assert bcrypt.checkpw(b"admin", hash_from_sql.encode())
