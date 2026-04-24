from flask import Flask, render_template, redirect, url_for, request, session, flash
from models import db, User, Post, Comment
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secretkey'

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Vypln vsechna pole')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Uzivatel uz existuje')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        user = User(username=username, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash('Registrace probehla uspesne')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('Prihlaseni uspesne')
            return redirect(url_for('index'))

        flash('Spatne udaje')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Byl jsi odhlasen')
    return redirect(url_for('index'))


@app.route('/post/create', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title or not content:
            flash('Vypln vsechna pole')
            return redirect(url_for('create_post'))

        post = Post(
            title=title,
            content=content,
            user_id=session['user_id']
        )

        db.session.add(post)
        db.session.commit()

        flash('Prispevek vytvoren')
        return redirect(url_for('index'))

    return render_template('create_post.html', post=None)


@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)

    if request.method == 'POST':
        if 'user_id' not in session:
            return redirect(url_for('login'))

        content = request.form['content']

        if not content:
            flash('Komentar nesmi byt prazdny')
            return redirect(url_for('post_detail', post_id=post.id))

        comment = Comment(
            content=content,
            user_id=session['user_id'],
            post_id=post.id
        )

        db.session.add(comment)
        db.session.commit()

        flash('Komentar pridan')
        return redirect(url_for('post_detail', post_id=post.id))

    return render_template('post_detail.html', post=post)


@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if session.get('user_id') != post.user_id:
        flash('Nemate opravneni')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title or not content:
            flash('Vypln vsechna pole')
            return redirect(url_for('edit_post', post_id=post.id))

        post.title = title
        post.content = content
        db.session.commit()

        flash('Prispevek upraven')
        return redirect(url_for('post_detail', post_id=post.id))

    return render_template('create_post.html', post=post)


@app.route('/post/<int:post_id>/delete')
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if session.get('user_id') != post.user_id:
        flash('Nemate opravneni')
        return redirect(url_for('index'))

    db.session.delete(post)
    db.session.commit()

    flash('Prispevek smazan')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)