import psycopg2
import os


def get_connection(db_name):
    connection = psycopg.connect(
        dbname=db_name,
        host='***',
        port='****',
        user='****',
        password='*****'
    )
    return connection


def main():
    with get_connection('cook') as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS recipes (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    ingredients TEXT NOT NULL,
                    preparation_time TEXT NOT NULL,
                    instructions TEXT NOT NULL,
                    author VARCHAR(100)
                )
                """
            )
            conn.commit()

            cursor.execute(
                """
                INSERT INTO recipes(name, category, description, ingredients, preparation_time, instructions, author)
                VALUES ('Cake', 'Dessert', 'Tasty cake', 'Money', '60 min', 'Take a delivery', 'author 1'),
                       ('Cookie', 'Dessert', 'Tasty cookie', 'Money', '55 min', 'Take a delivery', 'author 2'),
                       ('Pasta', 'Main Course', 'Delicious pasta', 'Money', '30 min', 'Boil pasta', 'author 3')
                """
            )
            conn.commit()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS recipe_images (
                    id SERIAL PRIMARY KEY,
                    recipe_id INTEGER,
                    image_path TEXT,
                    FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON UPDATE CASCADE ON DELETE CASCADE
                )
                """
            )
            conn.commit()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS comments (
                    id SERIAL PRIMARY KEY,
                    recipe_id INTEGER,
                    content TEXT,
                    author VARCHAR(100),
                    FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON UPDATE CASCADE ON DELETE CASCADE
                )
                """
            )
            conn.commit()

            image_dir = os.path.join('static', 'images')  # Directory containing the images
            image_paths = [
                os.path.join(image_dir, filename)
                for filename in os.listdir(image_dir)

                if os.path.isfile(os.path.join(image_dir, filename))
            ]
            cursor.execute("SELECT id FROM recipes")  # Retrieve all recipe IDs
            recipe_ids = [row[0] for row in cursor.fetchall()]

            for recipe_id, image_path in zip(recipe_ids, image_paths):
                cursor.execute(
                    """
                    INSERT INTO recipe_images (recipe_id, image_path)
                    VALUES (%s, %s)
                    """,
                    (recipe_id, image_path)
                )

            conn.commit()


if __name__ == '__main__':
    main()
