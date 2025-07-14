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

@app.route("/api/countries")
def api_countries():
    """
    Fetches a list of countries, their post counts, and a sample image
    by calling a Supabase RPC function 'get_countries_with_counts'.
    """
    try:
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        }
        url = f"{SUPABASE_URL}/rest/v1/rpc/get_countries_with_counts"
        r = requests.post(url, headers=headers)
        r.raise_for_status()
        countries = r.json()
        return jsonify(countries)

    except requests.exceptions.RequestException as e:
        print(f"Error querying Supabase countries: {e}")
        return jsonify({"error": "Could not connect to the database."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


@app.route("/api/posts")
def api_posts():
    """
    A unified API endpoint to fetch posts.
    Handles searching, sorting, pagination, and country filtering.
    """
    try:
        q = request.args.get("q", "").strip()
        sort_by = request.args.get("sort_by", "timestamp")
        order = request.args.get("order", "desc")
        page = int(request.args.get("page", 1))
        country = request.args.get("country")
        per_page = 20

        if sort_by not in ["timestamp", "likesCount", "commentsCount"]:
            sort_by = "timestamp"
        if order not in ["asc", "desc"]:
            order = "desc"
        if page < 1:
            page = 1

        offset = (page - 1) * per_page

        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Prefer": "count=exact"
        }
        url = f"{SUPABASE_URL}/rest/v1/bd_posts"

        params = {
            "select": "*,commentsCount",
            "order": f"{sort_by}.{order},id.asc",
            "limit": per_page,
            "offset": offset,
        }

        if country:
            params['guessed_country'] = f'eq.{country}'

        if q:
            search_filter = f"(caption.ilike.*{q}*,locationName.ilike.*{q}*)"
            params["or"] = search_filter

        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()

        posts = r.json()

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

# --- UPDATED TIMELINE ENDPOINT WITH PAGINATION ---
@app.route("/api/timeline_posts")
def api_timeline_posts():
    """
    Fetches a lightweight list of posts for the timeline view with pagination.
    Only returns essential fields to keep the payload small and fast.
    """
    try:
        # --- Get pagination parameters ---
        page = int(request.args.get("page", 1))
        per_page = 500 # Fetch 500 posts at a time as requested.
        
        if page < 1:
            page = 1
        
        offset = (page - 1) * per_page

        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        }
        url = f"{SUPABASE_URL}/rest/v1/bd_posts"
        
        params = {
            "select": "id,timestamp,guessed_country,bucketMedia,url",
            "order": "timestamp.desc",
            "limit": per_page,
            "offset": offset,
        }

        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        posts = r.json()
        return jsonify(posts)

    except requests.exceptions.RequestException as e:
        print(f"Error querying Supabase timeline: {e}")
        return jsonify({"error": "Could not connect to the database."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)