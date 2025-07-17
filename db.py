# db.py
import sqlite3
def init_db():
    conn = sqlite3.connect("/data/profiles.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            city TEXT,
            skills TEXT,
            looking_for TEXT,
            experience INTEGER,
            description TEXT,
            photo_id TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_profile(user_id, name, city, skills, looking_for, experience, description, photo_id=None):
    conn = sqlite3.connect("/data/profiles.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO profiles (user_id, name, city, skills, looking_for, experience, description, photo_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, name, city, skills, looking_for, experience, description, photo_id))
    conn.commit()
    conn.close()

def get_profile(user_id):
    conn = sqlite3.connect("/data/profiles.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
    profile = cursor.fetchone()
    conn.close()
    return profile

def update_photo(user_id, photo_id):
    conn = sqlite3.connect("/data/profiles.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE profiles SET photo_id = ? WHERE user_id = ?", (photo_id, user_id))
    conn.commit()
    conn.close()

def get_random_profile(exclude_user_id: int):
    conn = sqlite3.connect("/data/profiles.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM profiles "
        "WHERE user_id != ? "
        "AND name IS NOT NULL "  # Теперь комментарий вне строки запроса
        "ORDER BY RANDOM() "
        "LIMIT 1",
        (exclude_user_id,)
    )
    profile = cursor.fetchone()
    conn.close()
    return profile


def get_unseen_profile(exclude_user_id: int, seen_ids: list):
    conn = sqlite3.connect("/data/profiles.db")
    cursor = conn.cursor()

    if not seen_ids:
        # Если нет просмотренных анкет, используем простой запрос
        query = """
            SELECT * FROM profiles 
            WHERE user_id != ? 
            AND name IS NOT NULL
            ORDER BY RANDOM() 
            LIMIT 1
        """
        params = [exclude_user_id]
    else:
        # Если есть просмотренные анкеты, исключаем их
        placeholders = ','.join(['?'] * len(seen_ids))
        query = f"""
            SELECT * FROM profiles 
            WHERE user_id != ? 
            AND user_id NOT IN ({placeholders})
            AND name IS NOT NULL
            ORDER BY RANDOM() 
            LIMIT 1
        """
        params = [exclude_user_id] + seen_ids

    cursor.execute(query, params)
    profile = cursor.fetchone()
    conn.close()
    return profile

def get_profile_by_id(user_id: int):
    conn = sqlite3.connect("/data/profiles.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
    profile = cursor.fetchone()
    conn.close()
    return profile

def delete_profile(user_id):
    conn = sqlite3.connect("/data/profiles.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM profiles WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_profiles_by_filters(city=None, experience=None, has_photo=None, exclude_ids=None):
    exclude_ids = exclude_ids or []
    query = "SELECT * FROM profiles WHERE 1=1"
    params = []

    if city:
        query += " AND city = ?"
        params.append(city)
    if experience is not None:
        query += " AND experience >= ?"
        params.append(experience)
    if has_photo is not None:
        if has_photo:
            query += " AND photo_id IS NOT NULL AND photo_id != ''"
        else:
            query += " AND (photo_id IS NULL OR photo_id = '')"
    if exclude_ids:
        placeholders = ",".join("?" for _ in exclude_ids)
        query += f" AND user_id NOT IN ({placeholders})"
        params.extend(exclude_ids)

    conn = sqlite3.connect("profiles.db")
    cursor = conn.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results