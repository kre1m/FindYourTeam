import sqlite3

def delete_profile(user_id):
    conn = sqlite3.connect("/data/profiles.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM profiles WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# Замените на нужный user_id
delete_profile(975554054)
print("Анкета удалена.")
