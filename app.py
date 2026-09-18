"""A simple Flask app for a blog."""

import json
from pathlib import Path

from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index() -> str:
    """Render the index page with blog posts."""
    with Path("data/database.json", encoding="utf-8").open() as f:
        blog_posts = json.load(f)
        print(blog_posts)
    return render_template(
        "index.html",
        posts=blog_posts,
        blogtitle="Mein Block",
    )


if __name__ == "__main__":
    app.run(debug=True)  # noqa: S201
