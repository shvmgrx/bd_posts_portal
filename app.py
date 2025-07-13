import requests
from flask import Flask, render_template, request, jsonify
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://sygtqsesegnaxkqdduic.supabase.co")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN5Z3Rxc2VzZWduYXhrcWRkdWljIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAxNTM5MTMsImV4cCI6MjA2NTcyOTkxM30.vd4JKrRH6163aa1XmOysD-8NXphe8J2UWUpJ-lybt1g")

app = Flask(__name__)

@app.route("/")
def index():
    """Renders the main application shell."""
    return render_template("index.html")

@app.route("/api/posts")
def api_posts():
    """
    A unified API endpoint to fetch posts.
    Handles searching, sorting, and pagination.
    """
    try:
        # --- Get and validate request parameters ---
        q = request.args.get("q", "").strip()
        sort_by = request.args.get("sort_by", "timestamp")
        order = request.args.get("order", "desc")
        page = int(request.args.get("page", 1))
        per_page = 20  # Define how many posts per page

        # --- Sanitize inputs to prevent abuse ---
        if sort_by not in ["timestamp", "likesCount"]:
            sort_by = "timestamp"
        if order not in ["asc", "desc"]:
            order = "desc"
        if page < 1:
            page = 1

        # Calculate the offset for Supabase pagination
        offset = (page - 1) * per_page

        # --- Prepare Supabase API request ---
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Prefer": "count=exact"  # Request the total count for pagination
        }
        url = f"{SUPABASE_URL}/rest/v1/bd_posts"

        # Construct the final query parameters
        params = {
            "select": "*",
            "order": f"{sort_by}.{order},id.asc", # Secondary sort by id for stable ordering
            "limit": per_page,
            "offset": offset,
        }

        # Add the search filter if a query 'q' is provided
        if q:
            # CORRECTED: The value for the 'or' parameter must start with '(', not 'or('.
            search_filter = f"(caption.ilike.*{q}*,locationName.ilike.*{q}*)"
            params["or"] = search_filter

        # --- Execute the request ---
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()  # Raise an exception for bad status codes

        posts = r.json()

        # Extract total count from 'Content-Range' header (e.g., "0-19/500")
        content_range = r.headers.get("Content-Range")
        total_posts = 0
        if content_range:
            total_posts_str = content_range.split("/")[-1]
            if total_posts_str != '*':
                total_posts = int(total_posts_str)

        return jsonify({
            "posts": posts,
            "total": total_posts,
            "page": page,
            "per_page": per_page,
        })

    except requests.exceptions.RequestException as e:
        print(f"Error querying Supabase: {e}")
        return jsonify({"error": "Could not connect to the database."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)