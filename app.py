"""A simple Flask app for a blog."""

import json
from pathlib import Path
from typing import Any

from flask import Flask, render_template


class Masterblog:
    """A simple Flask app for a blog."""

    def __init__(self) -> None:
        """Initialize the Flask app."""
        self.app = Flask(__name__)
        self.app.add_url_rule("/", view_func=self.index)

    def index(self) -> str:
        """Render the index page with blog posts."""
        with Path("data/database.json").open(encoding="utf-8") as f:
            blog_posts = json.load(f)
        return render_template(
            "index.html",
            posts=blog_posts,
            blogtitle="Mein Blog",
        )

    def run(self, **kwargs: Any) -> None:  # noqa: ANN401
        """Start the Flask app."""
        self.app.run(**kwargs)


if __name__ == "__main__":
    Masterblog().run(debug=True)
