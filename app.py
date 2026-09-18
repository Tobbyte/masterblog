"""A simple Flask app for a blog."""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from flask import Flask, redirect, render_template, request, url_for
from werkzeug import Response


class Masterblog:
    """A simple Flask app for a blog."""

    def __init__(self) -> None:
        """Initialize the Flask app."""
        self.app = Flask(__name__)
        self.app.add_url_rule("/", view_func=self.route_index)
        self.app.add_url_rule(
            "/add",
            view_func=self.route_add,
            methods=["GET", "POST"],
        )

        self.load_data()

    def route_index(self) -> str:
        """Render the index page with blog posts."""
        self.load_data()  # refresh
        return render_template(
            "index.html",
            posts=self.blog_posts,
            blogtitle="Mein Blog",
        )

    def route_add(self) -> str | Response:
        """Render form on get or save post on post."""
        if request.method == "POST":
            self.save_data(request.form.to_dict())  # use flat=False for multi
            return redirect(url_for("route_index"))

        return render_template("add.html")

    def save_data(self, new_post: dict) -> None:
        """Save a new blog post to the JSON file."""
        new_id = len(self.blog_posts) + 1
        new_post["id"] = new_id
        posts_copy = deepcopy(self.blog_posts)
        posts_copy.append(new_post)
        try:
            with Path("data/database.json").open("w", encoding="utf-8") as f:
                f.write(json.dumps(posts_copy))
        except OSError:
            print("Error writing to DB.")
        else:
            # update view only if crud went successful
            self.blog_posts = posts_copy
            print(self.blog_posts)

    def load_data(self) -> None:
        """Load blog posts from a JSON file."""
        try:
            with Path("data/database.json").open(encoding="utf-8") as f:
                self.blog_posts = json.load(f)
        except FileNotFoundError:
            print("Database file not found. Using empty blog posts.")
            self.blog_posts = []

    def run(self, **kwargs: Any) -> None:  # noqa: ANN401
        """Start the Flask app."""
        self.app.run(**kwargs)


if __name__ == "__main__":
    Masterblog().run(debug=True)
