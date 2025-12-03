from flask import Flask, render_template, abort
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import certifi
import streamlit as st

app = Flask(__name__)

# MongoDB connection
aws_key = st.secrets["URI"]
MONGO_URI = aws_key
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["instagram_db"]

# Collections
users_collection = db["users"]
posts_collection = db["posts"]
comments_collection = db["comments"]
likes_collection = db["likes"]
followers_collection = db["followers"]


def get_user_by_id(user_id):
    """Get user by ObjectId or string id"""
    try:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        return users_collection.find_one({"_id": user_id})
    except:
        return None


def get_user_by_username(username):
    """Get user by username"""
    return users_collection.find_one({"username": username})


def get_followers_count(user_id):
    """Get count of followers for a user"""
    try:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        return followers_collection.count_documents({"following_id": user_id})
    except:
        return 0


def get_following_count(user_id):
    """Get count of users this user is following"""
    try:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        return followers_collection.count_documents({"follower_id": user_id})
    except:
        return 0


def get_followers_list(user_id):
    """Get list of users who follow this user"""
    try:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        follower_docs = followers_collection.find({"following_id": user_id})
        followers = []
        for doc in follower_docs:
            user = get_user_by_id(doc["follower_id"])
            if user:
                followers.append(user)
        return followers
    except:
        return []


def get_following_list(user_id):
    """Get list of users this user follows"""
    try:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        following_docs = followers_collection.find({"follower_id": user_id})
        following = []
        for doc in following_docs:
            user = get_user_by_id(doc["following_id"])
            if user:
                following.append(user)
        return following
    except:
        return []


def get_user_posts(user_id):
    """Get all posts by a user"""
    try:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        return list(posts_collection.find({"user_id": user_id}).sort("created_at", -1))
    except:
        return []


def get_post_comments(post_id):
    """Get all comments on a post"""
    try:
        if isinstance(post_id, str):
            post_id = ObjectId(post_id)
        comments = list(comments_collection.find({"post_id": post_id}).sort("created_at", 1))
        # Add user info to each comment
        for comment in comments:
            comment["user"] = get_user_by_id(comment.get("user_id"))
        return comments
    except:
        return []


def get_post_likes(post_id):
    """Get all likes on a post"""
    try:
        if isinstance(post_id, str):
            post_id = ObjectId(post_id)
        likes = list(likes_collection.find({"post_id": post_id}))
        # Add user info to each like
        for like in likes:
            like["user"] = get_user_by_id(like.get("user_id"))
        return likes
    except:
        return []


def get_likes_count(post_id):
    """Get count of likes on a post"""
    try:
        if isinstance(post_id, str):
            post_id = ObjectId(post_id)
        return likes_collection.count_documents({"post_id": post_id})
    except:
        return 0


@app.route("/")
def index():
    """Homepage - display all users"""
    users = list(users_collection.find())
    # Add follower/following counts to each user
    for user in users:
        user["followers_count"] = get_followers_count(user["_id"])
        user["following_count"] = get_following_count(user["_id"])
    return render_template("index.html", users=users)


@app.route("/user/<user_id>")
def user_profile(user_id):
    """User detail page"""
    user = get_user_by_id(user_id)
    if not user:
        abort(404)

    # Get user stats and data
    user["followers_count"] = get_followers_count(user["_id"])
    user["following_count"] = get_following_count(user["_id"])

    posts = get_user_posts(user["_id"])
    # Add likes count to each post
    for post in posts:
        post["likes_count"] = get_likes_count(post["_id"])

    followers = get_followers_list(user["_id"])
    following = get_following_list(user["_id"])

    return render_template(
        "user.html",
        user=user,
        posts=posts,
        followers=followers,
        following=following
    )


@app.route("/post/<post_id>")
def post_detail(post_id):
    """Post detail page"""
    try:
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
    except:
        abort(404)

    if not post:
        abort(404)

    # Get post author
    post["user"] = get_user_by_id(post.get("user_id"))

    # Get comments and likes
    comments = get_post_comments(post_id)
    likes = get_post_likes(post_id)
    likes_count = len(likes)

    return render_template(
        "post.html",
        post=post,
        comments=comments,
        likes=likes,
        likes_count=likes_count
    )


@app.template_filter("format_date")
def format_date(value):
    """Format datetime for display"""
    if isinstance(value, datetime):
        return value.strftime("%B %d, %Y at %I:%M %p")
    return value


@app.template_filter("time_ago")
def time_ago(value):
    """Convert datetime to 'time ago' format"""
    if not isinstance(value, datetime):
        return value

    now = datetime.utcnow()
    diff = now - value

    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}m ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours}h ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days}d ago"
    else:
        weeks = int(seconds / 604800)
        return f"{weeks}w ago"


if __name__ == "__main__":
    app.run(debug=True, port=5000)
