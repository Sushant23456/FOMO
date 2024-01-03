from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import UniqueConstraint



db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    bio = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    friendships = db.relationship('Friendship', 
                                  primaryjoin="or_(User.id==Friendship.user_id, User.id==Friendship.friend_id)",
                                  lazy='dynamic')
    profile_picture = db.Column(db.String(120), nullable=True, default='default.jpg')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    media_path = db.Column(db.String(120), unique=True, nullable=False)
    caption = db.Column(db.String(250), nullable=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('posts', lazy=True))

    @staticmethod
    def create_post(user_id, media_path, caption):
        post = Post(user_id=user_id, media_path=media_path, caption=caption)
        db.session.add(post)
        db.session.commit()

class Friendship(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    user = db.relationship('User', foreign_keys=[user_id])
    friend = db.relationship('User', foreign_keys=[friend_id])

    @staticmethod
    def create_friendship(user1_id, user2_id):
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
        friendship = Friendship(user_id=user1_id, friend_id=user2_id)
        db.session.add(friendship)
        db.session.commit()

class FriendshipRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(10), nullable=False, default='pending')  # e.g., 'pending', 'accepted', 'declined'

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_requests')

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)  # Foreign key to the Post model

    user = db.relationship('User', backref='comments')
    post = db.relationship('Post', backref=db.backref('comments', lazy='dynamic'))



