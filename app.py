from flask import Flask, render_template, redirect, url_for, request, session, flash
from models import db, User, Post, Comment
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret'

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
        user = request.form['username']
        pw = request.form['password']

        if User.query.filter_by(username=user).first():
            flash('Uz existuje')
            return redirect(url_for('register'))

        new_user = User(username=user, password_hash=generate_password_hash(pw))
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()

        if user and check_password_hash(user.password_hash, request.form['password']):
            session['user_id'] = user.id
            return redirect(url_for('index'))

        flash('Spatne udaje')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/post/create', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        post = Post(
            title=request.form['title'],
            content=request.form['content'],
            user_id=session['user_id']
        )
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('create_post.html')


@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)

    if request.method == 'POST':
        if 'user_id' not in session:
            return redirect(url_for('login'))

        comment = Comment(
            content=request.form['content'],
            user_id=session['user_id'],
            post_id=post.id
        )
        db.session.add(comment)
        db.session.commit()

    return render_template('post_detail.html', post=post)


@app.route('/post/<int:post_id>/delete')
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if session.get('user_id') != post.user_id:
        return "No access"

    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)

@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if session.get('user_id') != post.user_id:
        return "No access"

    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        return redirect(url_for('post_detail', post_id=post.id))

    return render_template('create_post.html', post=post)