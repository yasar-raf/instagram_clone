import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import certifi
import streamlit as st

# Page config
st.set_page_config(
    page_title="Instagram Clone",
    page_icon="📸",
    layout="wide"
)




# MongoDB connection
@st.cache_resource
def get_database():
    MONGO_URI = st.secrets["URI"]
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    return client["instagram_db"]

db = get_database()

# Collections
users_collection = db["users"]
posts_collection = db["posts"]
comments_collection = db["comments"]
likes_collection = db["likes"]
followers_collection = db["followers"]


# Helper functions
def get_user_by_id(user_id):
    """Get user by ObjectId or string id"""
    try:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        return users_collection.find_one({"_id": user_id})
    except:
        return None


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


def time_ago(value):
    """Convert datetime to 'time ago' format"""
    if not isinstance(value, datetime):
        return str(value)

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


def format_date(value):
    """Format datetime for display"""
    if isinstance(value, datetime):
        return value.strftime("%B %d, %Y at %I:%M %p")
    return str(value)


# Initialize session state for navigation
if "page" not in st.session_state:
    st.session_state.page = "home"
if "selected_user_id" not in st.session_state:
    st.session_state.selected_user_id = None
if "selected_post_id" not in st.session_state:
    st.session_state.selected_post_id = None


def navigate_to(page, user_id=None, post_id=None):
    st.session_state.page = page
    st.session_state.selected_user_id = user_id
    st.session_state.selected_post_id = post_id


# Custom CSS
st.markdown("""
<style>
    .user-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border: 1px solid #e9ecef;
    }
    .stat-box {
        text-align: center;
        padding: 10px;
    }
    .post-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #dbdbdb;
        margin: 10px 0;
    }
    .comment-box {
        background-color: #fafafa;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)


# Page: Home - Display all users
def show_home():
    st.title("Instagram Clone")
    st.subheader("All Users")

    users = list(users_collection.find())

    if not users:
        st.info("No users found.")
        return

    cols = st.columns(3)
    for idx, user in enumerate(users):
        with cols[idx % 3]:
            with st.container():
                st.markdown(f"### @{user.get('username', 'unknown')}")
                st.write(f"**{user.get('full_name', '')}**")
                if user.get('bio'):
                    st.write(user.get('bio'))

                followers = get_followers_count(user["_id"])
                following = get_following_count(user["_id"])

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Followers", followers)
                with col2:
                    st.metric("Following", following)

                if st.button("View Profile", key=f"view_{user['_id']}"):
                    navigate_to("user", user_id=str(user["_id"]))
                    st.rerun()

                st.divider()


# Page: User Profile
def show_user_profile():
    user_id = st.session_state.selected_user_id
    user = get_user_by_id(user_id)

    if not user:
        st.error("User not found!")
        if st.button("Back to Home"):
            navigate_to("home")
            st.rerun()
        return

    # Back button
    if st.button("< Back to Home"):
        navigate_to("home")
        st.rerun()

    st.title(f"@{user.get('username', 'unknown')}")

    # User info section
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        posts = get_user_posts(user["_id"])
        st.metric("Posts", len(posts))
    with col2:
        st.metric("Followers", get_followers_count(user["_id"]))
    with col3:
        st.metric("Following", get_following_count(user["_id"]))
    with col4:
        if user.get("is_verified"):
            st.write("Verified")

    st.write(f"**{user.get('full_name', '')}**")
    if user.get('bio'):
        st.write(user.get('bio'))
    if user.get('website'):
        st.write(f"[{user.get('website')}]({user.get('website')})")

    st.divider()

    # Tabs for posts, followers, following
    tab1, tab2, tab3 = st.tabs(["Posts", "Followers", "Following"])

    with tab1:
        posts = get_user_posts(user["_id"])
        if not posts:
            st.info("No posts yet.")
        else:
            for post in posts:
                with st.container():
                    st.markdown(f"**{post.get('caption', '')}**")
                    if post.get('image_url'):
                        st.image(post.get('image_url'), width=300)

                    likes_count = get_likes_count(post["_id"])
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"❤️ {likes_count} likes")
                    with col2:
                        if post.get('created_at'):
                            st.write(f"🕐 {time_ago(post.get('created_at'))}")
                    with col3:
                        if st.button("View Post", key=f"post_{post['_id']}"):
                            navigate_to("post", post_id=str(post["_id"]))
                            st.rerun()
                    st.divider()

    with tab2:
        followers = get_followers_list(user["_id"])
        if not followers:
            st.info("No followers yet.")
        else:
            for follower in followers:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**@{follower.get('username', 'unknown')}** - {follower.get('full_name', '')}")
                with col2:
                    if st.button("View", key=f"follower_{follower['_id']}"):
                        navigate_to("user", user_id=str(follower["_id"]))
                        st.rerun()

    with tab3:
        following = get_following_list(user["_id"])
        if not following:
            st.info("Not following anyone yet.")
        else:
            for follow in following:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**@{follow.get('username', 'unknown')}** - {follow.get('full_name', '')}")
                with col2:
                    if st.button("View", key=f"following_{follow['_id']}"):
                        navigate_to("user", user_id=str(follow["_id"]))
                        st.rerun()


# Page: Post Detail
def show_post_detail():
    post_id = st.session_state.selected_post_id

    try:
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
    except:
        post = None

    if not post:
        st.error("Post not found!")
        if st.button("Back to Home"):
            navigate_to("home")
            st.rerun()
        return

    # Get post author
    author = get_user_by_id(post.get("user_id"))

    # Back button
    if author:
        if st.button(f"< Back to @{author.get('username', 'unknown')}'s profile"):
            navigate_to("user", user_id=str(author["_id"]))
            st.rerun()
    else:
        if st.button("< Back to Home"):
            navigate_to("home")
            st.rerun()

    st.title("Post Detail")

    # Post content
    if author:
        st.write(f"**@{author.get('username', 'unknown')}**")

    if post.get('image_url'):
        st.image(post.get('image_url'), width=500)

    st.write(post.get('caption', ''))

    if post.get('created_at'):
        st.write(f"Posted: {format_date(post.get('created_at'))}")

    st.divider()

    # Likes section
    likes = get_post_likes(post_id)
    st.subheader(f"❤️ {len(likes)} Likes")

    if likes:
        with st.expander("View who liked this post"):
            for like in likes:
                user = like.get("user")
                if user:
                    st.write(f"@{user.get('username', 'unknown')}")

    st.divider()

    # Comments section
    comments = get_post_comments(post_id)
    st.subheader(f"💬 {len(comments)} Comments")

    if not comments:
        st.info("No comments yet.")
    else:
        for comment in comments:
            user = comment.get("user")
            username = user.get("username", "unknown") if user else "unknown"

            with st.container():
                st.markdown(f"**@{username}**: {comment.get('text', '')}")
                if comment.get('created_at'):
                    st.caption(time_ago(comment.get('created_at')))


# Main routing
if st.session_state.page == "home":
    show_home()
elif st.session_state.page == "user":
    show_user_profile()
elif st.session_state.page == "post":
    show_post_detail()
