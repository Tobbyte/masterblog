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
        """Initialize the Flask app.

        Sets routes, loads initial data.
        """
        self.app = Flask(__name__)
        self.app.add_url_rule("/", view_func=self.route_index)
        self.app.add_url_rule(
            "/add",
            view_func=self.route_add,
            methods=["GET", "POST"],
        )
        self.app.add_url_rule(
            "/delete/<int:post_id>",
            view_func=self.route_delete,
            methods=["POST"],
        )
        self.app.add_url_rule(
            "/update/<int:post_id>",
            view_func=self.route_update_post,
            methods=["GET", "POST"],
        )

        self.blog_posts = self.load_data()

    def get_last_uid_from_posts(self) -> int:
        """Cycles through all blog posts to get last id."""
        return max(post["id"] for post in self.blog_posts)

    def get_uid(self) -> int:
        """Get a unique identifier for a new blog post.

        Reads the last used UID from a file and increments it for
        the next post.
        If the file does not exist or is empty, it finds the last id
        in existing posts and increases by +1. Saves to uid file.

        Note: This can lead to links to posts directing to the wring
        post if posts got deleted and the blog is setup fresh with
        empty uid file.
        """
        try:
            with Path("data/uid").open(encoding="utf-8") as f:
                last_uid = f.read()
        except FileNotFoundError:
            last_uid = ""

        try:
            new_uid = (
                int(last_uid) + 1
                if last_uid
                else self.get_last_uid_from_posts() + 1
            )
            self.save_uid(new_uid)
        except ValueError:
            return 1
        else:
            return new_uid

    def save_uid(self, new_uid: int) -> None:
        """Save the new UID to a file for future use."""
        with Path("data/uid").open("w", encoding="utf-8") as f:
            f.write(str(new_uid))
            print("newuid:", new_uid)

    def route_index(self) -> str:
        """Render the index page with blog posts."""
        return render_template(
            "index.html",
            posts=self.load_data(),  # refresh
            blogtitle="Mein Blog",
        )

    def route_add(self) -> str | Response:
        """Render form on get or save post on post."""
        if request.method == "POST":
            self.add_post(request.form.to_dict())  # use flat=False for multi
            return redirect(url_for("route_index"))

        return render_template("add.html")

    def route_delete(self, post_id) -> Response:
        """Delete a blog post by its ID."""
        if request.method == "POST":
            self.del_post(post_id)  # use flat=False for multi

        return redirect(url_for("route_index"))

    def fetch_post_by_id(self, post_id) -> dict:
        """Fetch a blog post from runtime data by its ID."""
        return next(
            filter(lambda post: post["id"] == post_id, self.blog_posts),
        )

    def route_update_post(self, post_id) -> str | tuple | Response:
        """Render the update page on GET or save changes on POST."""
        post = self.fetch_post_by_id(post_id)
        if post is None:
            return "Post not found", 404

        if request.method == "POST":
            posts_copy = deepcopy(self.blog_posts)
            new_post = request.form.to_dict()
            posts = [
                {**post, **new_post} if post["id"] == post_id else post
                for post in posts_copy
            ]
            self.save_data(posts)
            return redirect(url_for("route_index"))

        return render_template("update.html", post=post)

    def add_post(self, new_post: dict) -> None:
        """Add a new blog post."""
        new_id = self.get_uid()
        new_post["id"] = new_id
        posts_copy = deepcopy(self.blog_posts)
        posts_copy.append(new_post)
        self.save_data(posts_copy)

    def del_post(self, post_id: int) -> None:
        """Delete a blog post by its ID."""
        posts_copy = deepcopy(self.blog_posts)
        posts = [post for post in posts_copy if post["id"] != post_id]
        self.save_data(posts)

    def save_data(self, blog_posts: list) -> None:
        """Save blog posts data.

        Saves to db and updates runtime only on success.
        """
        try:
            with Path("data/database.json").open("w", encoding="utf-8") as f:
                f.write(json.dumps(blog_posts))
        except OSError:
            print("Error writing to DB.")
        else:
            # update view only if crud went successful
            self.blog_posts = blog_posts
            print(self.blog_posts)

    def load_data(self) -> list:
        """Load blog posts from a JSON file."""
        try:
            with Path("data/database.json").open(encoding="utf-8") as f:
                self.blog_posts = json.load(f)
        except FileNotFoundError:
            print("Database file not found. Using empty blog posts.")
            self.blog_posts = []
        return self.blog_posts

    def run(self, **kwargs: Any) -> None:  # noqa: ANN401
        """Start the Flask app."""
        self.app.run(**kwargs)


if __name__ == "__main__":
    Masterblog().run(debug=True)
