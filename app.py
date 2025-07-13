import requests
from flask import Flask, render_template, request, jsonify

SUPABASE_URL = "https://sygtqsesegnaxkqdduic.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN5Z3Rxc2VzZWduYXhrcWRkdWljIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAxNTM5MTMsImV4cCI6MjA2NTcyOTkxM30.vd4JKrRH6163aa1XmOysD-8NXphe8J2UWUpJ-lybt1g"

app = Flask(__name__)

def fetch_all_posts():
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
    }
    url = f"{SUPABASE_URL}/rest/v1/bd_posts?select=*"
    posts = []
    limit = 1000
    offset = 0
    while True:
        params = {"limit": limit, "offset": offset}
        r = requests.get(url, headers=headers, params=params)
        batch = r.json() if r.status_code == 200 else []
        if not batch:
            break
        posts.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
    return posts

ALL_POSTS = []
try:
    ALL_POSTS = fetch_all_posts()
    print(f"Loaded {len(ALL_POSTS)} posts from Supabase.")
except Exception as e:
    print(f"Error loading posts: {e}")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search")
def search():
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify([])
    def matches(p):
        return q in (p.get("locationName") or "").lower() or q in (p.get("caption") or "").lower()
    results = [p for p in ALL_POSTS if matches(p)]
    results.sort(key=lambda p: p.get("timestamp", ""), reverse=True)
    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
