import os
import uuid
from flask import Flask, render_template, url_for, request, flash, redirect, send_from_directory
from init_db import get_connection
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.static_folder = os.path.join(os.path.dirname(__file__), 'static')
app.config['SECRET_KEY'] = '*****'
DATABASE_NAME = 'cook'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_post(post_id):
    with get_connection(DATABASE_NAME) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, name, category, description, ingredients, preparation_time, instructions, author "
                "FROM recipes WHERE id = %s",
                (post_id,)
            )
            post = cursor.fetchone()

            cursor.execute(
                "SELECT image_path FROM recipe_images WHERE recipe_id = %s",
                (post_id,)
            )
            images = cursor.fetchall()

            cursor.execute(
                "SELECT content, author FROM comments WHERE recipe_id = %s",
                (post_id,)
            )
            comments = cursor.fetchall()

    post_data = {
        'id': post[0],
        'name': post[1],
        'category': post[2],
        'description': post[3],
        'ingredients': post[4],
        'preparation_time': post[5],
        'instructions': post[6],
        'author': post[7],
        'images': [image[0] for image in images] if images else [],
        'comments': [{'content': comment[0], 'author': comment[1]} for comment in comments] if comments else []
    }

    return post_data


@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('static/images', filename)


@app.route('/', methods=['GET', 'POST'])
def index():
    search_query = request.form.get('search') if request.method == 'POST' else None
    category = request.form.get('category') if request.method == 'POST' else None

    with get_connection(DATABASE_NAME) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT category FROM recipes")
            categories = [row[0] for row in cursor.fetchall()]

            condition = ""
            params = []

            if search_query:
                condition += " AND (LOWER(name) LIKE %s OR LOWER(ingredients) LIKE %s OR LOWER(category) LIKE %s)"
                params.extend(['%{}%'.format(search_query.lower())] * 3)

            if category and category != 'All categories':
                condition += " AND LOWER(category) = %s"
                params.append(category.lower())

            cursor.execute(
                "SELECT id, name, category, description, ingredients, preparation_time, instructions, author "
                "FROM recipes "
                "WHERE 1 = 1" + condition,
                params
            )
            posts = cursor.fetchall()

            posts_data = []

            for post in posts:
                recipe_id = post[0]
                cursor.execute(
                    "SELECT image_path FROM recipe_images WHERE recipe_id = %s",
                    (recipe_id,)
                )
                images = cursor.fetchall()

                posts_data.append(
                    {
                        'id': post[0],
                        'name': post[1],
                        'category': post[2],
                        'description': post[3],
                        'ingredients': post[4],
                        'preparation_time': post[5],
                        'instructions': post[6],
                        'author': post[7],
                        'images': [image[0] for image in images]
                    }
                )

    return render_template('index.html', posts=posts_data, categories=categories,
                           selected_category=category, search_query=search_query)


@app.route('/posts/<int:post_id>')
def post(post_id):
    post = get_post(post_id)

    return render_template('post.html', post=post)


@app.route('/create-post', methods=['GET', 'POST'])
def create():
    if request.method == "POST":
        name = request.form['name']
        category = request.form['category']
        description = request.form['description']
        ingredients = request.form['ingredients']
        preparation_time = request.form['preparation_time']
        instructions = request.form['instructions']
        author = request.form['author']
        image = request.files['image']

        if not (
                name and category and description and ingredients and preparation_time and instructions and author and image):
            flash('Fill in all the fields')
        elif not allowed_file(image.filename):
            flash('Invalid file format. Allowed formats are: png, jpg, jpeg, gif')
        else:
            filename = secure_filename(image.filename)
            image_path = os.path.join('static/images', str(uuid.uuid4()) + '_' + filename)
            image.save(image_path)

            with get_connection(DATABASE_NAME) as conn:

                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO recipes(name, category, description, ingredients, preparation_time, "
                        "instructions, author) "
                        "VALUES(%s, %s, %s, %s, %s, %s, %s)",
                        (name, category, description, ingredients, preparation_time, instructions, author)
                    )
                    conn.commit()

                    cursor.execute(
                        "SELECT id FROM recipes WHERE name = %s AND category = %s AND description = %s "
                        "AND ingredients = %s AND preparation_time = %s AND instructions = %s AND author = %s",
                        (name, category, description, ingredients, preparation_time, instructions, author)
                    )
                    recipe_id = cursor.fetchone()[0]

                    cursor.execute(
                        "INSERT INTO recipe_images(recipe_id, image_path) VALUES(%s, %s)",
                        (recipe_id, image_path)
                    )
                    conn.commit()

            return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit(post_id):
    post = get_post(post_id)

    if request.method == "POST":
        name = request.form['name']
        category = request.form['category']
        description = request.form['description']
        ingredients = request.form['ingredients']
        preparation_time = request.form['preparation_time']
        instructions = request.form['instructions']
        author = request.form['author']
        image = request.files['image']

        if not (
                name and category and description and ingredients and preparation_time and instructions and author):
            flash('Fill in all the fields')
        elif image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join('static/images', str(uuid.uuid4()) + '_' + filename)
            image.save(image_path)

            with get_connection(DATABASE_NAME) as conn:

                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE recipes "
                        "SET name = %s, category = %s, description = %s, ingredients = %s, preparation_time = %s, "
                        "instructions = %s, author = %s "
                        "WHERE id = %s",
                        (name, category, description, ingredients, preparation_time, instructions, author, post_id)
                    )
                    conn.commit()

                    cursor.execute(
                        "SELECT image_path FROM recipe_images WHERE recipe_id = %s",
                        (post_id,)
                    )
                    existing_image_path = cursor.fetchone()

                    if existing_image_path:
                        os.remove(existing_image_path[0])
                        cursor.execute(
                            "UPDATE recipe_images "
                            "SET image_path = %s "
                            "WHERE recipe_id = %s",
                            (image_path, post_id)
                        )

                    else:
                        cursor.execute(
                            "INSERT INTO recipe_images (recipe_id, image_path) "
                            "VALUES (%s, %s)",
                            (post_id, image_path)
                        )

                    conn.commit()

            flash('Post updated successfully')
            return redirect(url_for('post', post_id=post_id))

        else:
            flash('Invalid file format. Allowed formats are: png, jpg, jpeg, gif')

    return render_template('edit.html', post=post)


@app.route('/add-comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    content = request.form['content']
    author = request.form['author']

    with get_connection(DATABASE_NAME) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO comments (recipe_id, content, author) VALUES (%s, %s, %s)",
                (post_id, content, author)
            )
            conn.commit()

    return redirect(url_for('post', post_id=post_id))


@app.route('/<int:post_id>/delete', methods=['POST', ])
def delete(post_id):
    with get_connection(DATABASE_NAME) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"""DELETE FROM recipes WHERE id = {post_id}""")
            conn.commit()

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
