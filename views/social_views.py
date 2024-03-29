# social_views.py
from flask import request, jsonify
from models import Post, Like, Comment, Friendship, User
from extensions import db


def register_social_routes(app):
    @app.route('/create_post', methods=['POST'])
    def create_post():
        user_id = request.json['user_id']
        content = request.json['content']

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        new_post = Post(user_id=user_id, content=content, created_at=db.func.current_timestamp())
        db.session.add(new_post)
        db.session.commit()

        return jsonify({"message": "Post created successfully", "post_id": new_post.id}), 201

    @app.route('/like_post/<int:post_id>/<int:user_id>', methods=['POST'])
    def like_post(post_id, user_id):
        if not Post.query.get(post_id) or not User.query.get(user_id):
            return jsonify({"error": "Post or user not found"}), 404

        like = Like.query.filter_by(post_id=post_id, user_id=user_id).first()
        if like:
            return jsonify({"error": "Already liked"}), 400

        new_like = Like(post_id=post_id, user_id=user_id)
        db.session.add(new_like)
        db.session.commit()

        return jsonify({"message": "Post liked successfully"}), 201

    @app.route('/add_comment', methods=['POST'])
    def add_comment():
        user_id = request.json['user_id']
        post_id = request.json['post_id']
        content = request.json['content']

        if not Post.query.get(post_id) or not User.query.get(user_id):
            return jsonify({"error": "Post or user not found"}), 404

        new_comment = Comment(post_id=post_id, user_id=user_id, content=content, timestamp=db.func.current_timestamp())
        db.session.add(new_comment)
        db.session.commit()

        return jsonify({"message": "Comment added successfully"}), 201

    @app.route('/add_friend/<int:user_id>/<int:friend_id>', methods=['POST'])
    def add_friend(user_id, friend_id):
        if user_id == friend_id:
            return jsonify({"error": "Cannot add yourself as a friend"}), 400

        user = User.query.get(user_id)
        friend = User.query.get(friend_id)
        if not user or not friend:
            return jsonify({"error": "User or friend not found"}), 404

        existing_friendship = Friendship.query.filter(
            ((Friendship.user_id == user_id) & (Friendship.friend_id == friend_id)) |
            ((Friendship.user_id == friend_id) & (Friendship.friend_id == user_id))).first()
        if existing_friendship:
            return jsonify({"error": "Friendship already exists or request pending"}), 400

        new_friendship = Friendship(user_id=user_id, friend_id=friend_id, status="requested")
        db.session.add(new_friendship)
        db.session.commit()

        return jsonify({"message": "Friend request sent successfully"}), 201

    @app.route('/respond_friend_request/<int:user_id>/<int:friend_id>', methods=['POST'])
    def respond_friend_request(user_id, friend_id):
        data = request.get_json()
        action = data.get('action')  # Expecting 'accept' or 'decline'

        # Assuming the friend_id is the one who received the request and user_id is the one who sent it
        friendship = Friendship.query.filter_by(user_id=friend_id, friend_id=user_id, status="requested").first()
        if not friendship:
            return jsonify({"error": "Friend request not found"}), 404

        if action == "accept":
            friendship.status = "accepted"
        elif action == "decline":
            db.session.delete(friendship)
        else:
            return jsonify({"error": "Invalid action"}), 400

        db.session.commit()

        action_response = "accepted" if action == "accept" else "declined"
        return jsonify({"message": f"Friend request {action_response}"}), 200

    @app.route('/remove_friend/<int:user_id>/<int:friend_id>', methods=['DELETE'])
    def remove_friend(user_id, friend_id):
        # Check if there's a friendship or a friend request from user_id to friend_id
        friendship = Friendship.query.filter(
            ((Friendship.user_id == user_id) & (Friendship.friend_id == friend_id) &
             (Friendship.status.in_(["accepted", "requested"]))) |
            ((Friendship.user_id == friend_id) & (Friendship.friend_id == user_id) &
             (Friendship.status == "requested"))
        ).first()

        if not friendship:
            return jsonify({"error": "Friendship or friend request not found"}), 404

        # If a "requested" friendship is found where the current user is the recipient, this implies declining the
        # request
        if friendship.status == "requested" and friendship.user_id == friend_id:
            action = "declined"
        else:
            # Otherwise, it's either canceling sent request or removing an accepted friendship
            action = "canceled" if friendship.status == "requested" else "removed"

        db.session.delete(friendship)
        db.session.commit()

        return jsonify({"message": f"Friend request {action} successfully"}), 200

