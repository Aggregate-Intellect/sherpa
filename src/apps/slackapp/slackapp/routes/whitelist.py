from flask import Blueprint, jsonify, request
from sherpa_ai.database.user_usage_tracker import UserUsageTracker


whitelist_blueprint = Blueprint("auth", __name__)


@whitelist_blueprint.route("/add", methods=["POST"])
def add_to_whitelist():
    data = request.get_json()
    user_id = data.get("user_id")

    db = UserUsageTracker()
    if user_id:
        db.add_to_whitelist(user_id)
        return jsonify({"message": f"User {user_id} added to whitelist."}), 201
    else:
        return jsonify({"error": "User ID not provided."}), 400


@whitelist_blueprint.route("/", methods=["GET"])
def get_all_whitelists():
    db = UserUsageTracker()

    data = db.get_all_whitelisted_ids()
    return jsonify({"whitelisted_ids": data})
