from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask import send_from_directory
from werkzeug.utils import secure_filename
from models import db, User, Post, Friendship, FriendshipRequest, Like, Comment
from sqlalchemy.exc import IntegrityError
from flask_migrate import Migrate
from PIL import Image
from flask import jsonify
from werkzeug.exceptions import BadRequest
from datetime import datetime
import base64
import os
import uuid
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your-secret-key'

db.init_app(app)
migrate = Migrate(app, db)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Make sure the directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def home():
    friends_ids = db.session.query(Friendship.friend_id).filter(Friendship.user_id == current_user.id).all()
    friends_ids = [fid for (fid,) in friends_ids]

    posts = Post.query.filter(Post.user_id.in_(friends_ids)).order_by(Post.timestamp.desc()).all()
    post_likes = {post.id: Like.query.filter_by(post_id=post.id).count() for post in posts}

    friend_requests = FriendshipRequest.query.filter_by(receiver_id=current_user.id).all()
    sent_friend_requests = FriendshipRequest.query.filter_by(sender_id=current_user.id).all()
    return render_template('index.html', posts=posts, post_likes=post_likes, friend_requests=friend_requests, sent_friend_requests=sent_friend_requests)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember') == 'on')
            print(user)
            return redirect(url_for('home'))
        
        else:
            flash('Invalid username or password')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            flash('Please enter all the fields', 'error')
            return redirect(url_for('register'))

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user is None:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username or email already exists', 'error')

    return render_template('register.html')


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
        else:
            image_data = request.form.get('image-cropped')
            if image_data:
                if 'data:image' in image_data and ';base64,' in image_data:
                    header, image_data = image_data.split(';base64,')
                image_data = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_data))
                if image.mode == 'RGBA':
                    image = image.convert('RGB')
                user_id_str = str(current_user.id)
                timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
                unique_identifier = str(uuid.uuid4())  # Optional: For additional randomness
                filename = f"user_{user_id_str}_{timestamp_str}_{unique_identifier}.jpg"

                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(file_path)
            else:
                flash('No file or image data provided', 'error')
                return redirect(request.url)
        try:
            new_post = Post(user_id=current_user.id, media_path=filename, caption=request.form.get('caption', ''))
            db.session.add(new_post)
            db.session.commit()
            flash('Post created successfully!', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while creating the post.', 'error')

        return redirect(url_for('home'))

    return render_template('upload.html')



# @app.route('/upload', methods=['GET', 'POST'])
# @login_required
# def upload_file():
#     if request.method == 'POST':

#         if 'file' not in request.files:
#             flash('No file part', 'error')
#             return redirect(request.url)

#         file = request.files['file']
        
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

#             try:
#                 if 'data:image' in image_data and ';base64,' in image_data:
#                     header, image_data = image_data.split(';base64,')


#                 image_data = base64.b64decode(image_data)

#                 image = Image.open(io.BytesIO(image_data))

#                 filename = 'your_generated_filename.jpg'
#                 file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

#                 image.save(file_path)

#                 with Image.open(temp_path) as img:
#                     width, height = img.size
#                     aspect_ratio = width / height

#                     landscape_ratio = 1.91
#                     portrait_ratio = 4 / 5

#                     if aspect_ratio < landscape_ratio or aspect_ratio > portrait_ratio:
#                         os.remove(temp_path) 
#                         raise BadRequest('Image does not meet aspect ratio requirements.')

#                 os.rename(temp_path, file_path)

#                 new_post = Post(user_id=current_user.id, media_path=filename, caption=request.form.get('caption', ''))
#                 db.session.add(new_post)
#                 db.session.commit()
#                 print(f"File saved at: {file_path}")

#                 flash('Post created successfully!', 'success')
#             except BadRequest as e:
#                 flash(str(e), 'error')
#             except IntegrityError as e:
#                 db.session.rollback()
#                 flash('A post with this file already exists.', 'error')
#                 print(f"Error: {str(e)}")

#             return redirect(url_for('home'))
    
#     return render_template('upload.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/search_users', methods=['POST'])
@login_required
def search_users():
    username = request.form['username']
    users = User.query.filter(User.username.like(f'%{username}%')).all()

    sent_requests = FriendshipRequest.query.filter_by(
        sender_id=current_user.id,
        status='pending'
    ).all()
    sent_requests_ids = [request.receiver_id for request in sent_requests]

    return render_template('search_results.html', users=users, sent_requests_ids=sent_requests_ids)


@app.route('/send_friend_request/<int:friend_id>', methods=['GET'])
@login_required
def send_friend_request(friend_id):
    existing_request = FriendshipRequest.query.filter(
        (FriendshipRequest.sender_id == current_user.id) &
        (FriendshipRequest.receiver_id == friend_id)
    ).first()

    if existing_request:
        flash('Friend request already sent', 'info')
    else:
        friend_request = FriendshipRequest(sender_id=current_user.id, receiver_id=friend_id)
        db.session.add(friend_request)
        db.session.commit()
        flash('Friend request sent', 'success')

    return redirect(url_for('home'))


@app.route('/upload_profile_picture', methods=['POST'])
def upload_profile_picture():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.root_path, 'static/profile_pics', filename)
        file.save(save_path)
        current_user.profile_picture = filename
        db.session.commit()

        return redirect(url_for('profile', filename=filename))

# @app.route('/profile')
# @login_required
# def profile():
#     posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.timestamp.desc()).all()
#     sent_friend_requests = FriendshipRequest.query.filter_by(sender_id=current_user.id).all()

#     friends_count = Friendship.query.filter_by(user_id=current_user.id).count()
#     friend_requests = FriendshipRequest.query.filter_by(receiver_id=current_user.id).all()

#     return render_template('profile.html', posts=posts, friends_count=friends_count, friend_requests=friend_requests, sent_friend_requests=sent_friend_requests)

@app.route('/myprofile')
@login_required
def my_profile():
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.timestamp.desc()).all()
    sent_friend_requests = FriendshipRequest.query.filter_by(sender_id=current_user.id).all()
    friends_count = Friendship.query.filter_by(user_id=current_user.id).count()
    friend_requests = FriendshipRequest.query.filter_by(receiver_id=current_user.id).all()

    print('posts', posts)
    return render_template('profile.html', posts=posts, friends_count=friends_count, friend_requests=friend_requests, sent_friend_requests=sent_friend_requests)

@app.route('/profile/<username>')
@login_required
def user_profile(username):
    user = User.query.filter_by(username=username).first()

    if user is None:
        abort(404) 

    posts = Post.query.filter_by(user_id=user.id).order_by(Post.timestamp.desc()).all()
    friends_count = Friendship.query.filter_by(user_id=user.id).count()


    return render_template('user_profile.html', user=user, posts=posts, friends_count=friends_count)


@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.root_path, 'static/profile_pics', filename)
            file.save(file_path)

            # Resize the image
            with Image.open(file_path) as img:
                img.thumbnail((360, 360))
                img.save(file_path)

            current_user.profile_picture = filename

    current_user.name = request.form['name']
    current_user.bio = request.form['bio']
    current_user.description = request.form['description']

    db.session.commit()

    flash('Your profile has been updated!', 'success')
    return redirect(url_for('my_profile'))



@app.route('/accept_friend_request/<int:request_id>')
@login_required
def accept_friend_request(request_id):
    request = FriendshipRequest.query.get(request_id)
    if request and request.receiver_id == current_user.id:
        request.status = 'accepted'

        existing_friendship = Friendship.query.filter(
            (Friendship.user_id == current_user.id) & (Friendship.friend_id == request.sender_id) |
            (Friendship.user_id == request.sender_id) & (Friendship.friend_id == current_user.id)
        ).first()

        if not existing_friendship:
            friendship = Friendship(user_id=current_user.id, friend_id=request.sender_id)
            db.session.add(friendship)

        db.session.commit()
        flash('Friend request accepted', 'success')
    else:
        flash('Friend request not found', 'error')

    return redirect(url_for('my_profile'))


@app.route('/decline_friend_request/<int:request_id>')
@login_required
def decline_friend_request(request_id):
    request = FriendshipRequest.query.get(request_id)
    if request and request.receiver_id == current_user.id:
        request.status = 'declined'
        db.session.commit()
        flash('Friend request declined', 'error')
    else:
        flash('Friend request not found', 'error')

    # Redirect back to the profile page
    return redirect(url_for('profile'))

@app.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()

    if like:
        # User already liked this post, so unlike it
        db.session.delete(like)
        liked = False
    else:
        # Add a new like
        new_like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(new_like)
        liked = True

    db.session.commit()
    like_count = Like.query.filter_by(post_id=post_id).count()

    return jsonify({'liked': liked, 'like_count': like_count, 'post_id': post_id})

@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def comment_post(post_id):
    post = Post.query.get_or_404(post_id)
    comment_content = request.form.get('comment')

    if comment_content:
        comment = Comment(user_id=current_user.id, post_id=post_id, content=comment_content)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been added.', 'success')
    else:
        flash('Comment cannot be empty.', 'error')

    return redirect(url_for('home'))

@app.route('/view_friends/<int:user_id>')
@login_required
def view_friends(user_id):
    user = User.query.get_or_404(user_id)

    # Retrieve the IDs of friends (both ways in the relationship)
    friend_ids = db.session.query(Friendship.friend_id).filter(Friendship.user_id == user_id).all()
    friend_ids += db.session.query(Friendship.user_id).filter(Friendship.friend_id == user_id).all()

    # Flatten the list of tuples and remove duplicates
    friend_ids = list(set([fid for sublist in friend_ids for fid in sublist]))

    # Retrieve User objects for each friend ID
    friends = User.query.filter(User.id.in_(friend_ids)).all()

    return render_template('view_friends.html', user=user, friends=friends)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
