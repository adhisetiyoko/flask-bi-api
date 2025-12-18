# update_password.py
import pymysql

# Connect ke Railway
connection = pymysql.connect(
    host="switchback.proxy.rlwy.net",
    user="root",
    password="pZPecHJjNLcZENpzjNNIIoVtNvBWdPOA",
    database="railway",
    port=48397
)

print("✅ Connected to Railway MySQL\n")

cursor = connection.cursor()

# Password hash yang benar
new_password_hash = "$2b$12$JHUI5rI0/1xloz5n2ZL53e3ltUKQubOC4lReewecUV9IgnIvMjL7C"
phone = "6281391130647"

print(f"Updating password for: {phone}")
print(f"New hash: {new_password_hash}")
print(f"Hash length: {len(new_password_hash)} chars\n")

# Update password
cursor.execute(
    "UPDATE users SET password = %s WHERE no_hp = %s",
    (new_password_hash, phone)
)

connection.commit()

print(f"✅ Rows affected: {cursor.rowcount}\n")

# Verify
cursor.execute(
    "SELECT no_hp, LENGTH(password), password FROM users WHERE no_hp = %s",
    (phone,)
)
result = cursor.fetchone()

if result:
    phone_db, pwd_len, pwd_hash = result
    print("=" * 70)
    print("VERIFICATION:")
    print("=" * 70)
    print(f"Phone: {phone_db}")
    print(f"Password length: {pwd_len} chars")
    print(f"Password hash: {pwd_hash}")
    print(f"First 10 chars: {pwd_hash[:10]}")
    
    if pwd_hash == new_password_hash:
        print("\n✅ Password updated successfully!")
    else:
        print("\n❌ Password mismatch!")
        print(f"Expected: {new_password_hash}")
        print(f"Got: {pwd_hash}")
else:
    print("❌ User not found!")

cursor.close()
connection.close()