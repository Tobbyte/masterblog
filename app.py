"""A simple Flask app for a blog."""

import json
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from config import (
    DB_FILE_PATH,
    ERR_DB_CORRUPT,
    ERR_NO_POST_UID,
    ERR_SAVE_DATA_FAILED,
    ERR_SAVE_POST_UID,
    UID_FILE_PATH,
)
from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug import Response
from werkzeug.exceptions import InternalServerError


class Masterblog:
    """A simple Flask app for a blog."""

    def __init__(self) -> None:
        """Initialize the Flask app.

        Sets routes, loads initial data.
        """
        self.app = Flask(__name__)

        self.make_sure_files_exist()

        # Would normally live in .env
        self.app.secret_key = "super-geheimer-uid-keyseed"  # noqa: S105

        # db error throws on startup (not as request). so set flag in db
        # startup (not raise there) and abort per before_request.
        self.db_error = False
        self.app.before_request(self.check_db_health)

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

        self.app.add_url_rule(
            "/like/<int:post_id>",
            view_func=self.route_like_post,
            methods=["POST"],
        )

        self.app.register_error_handler(404, self.page_not_found)
        self.app.register_error_handler(500, self.internal_server_error)

        # load data here (not only in index route) to prevent failing
        # when accessing f.e. /update directly
        self.blog_posts = self.load_data()

    def make_sure_files_exist(self) -> None:
        """Ensure that the necessary files exist."""
        try:
            if not DB_FILE_PATH.is_file():
                with DB_FILE_PATH.open(mode="w", encoding="utf-8") as file:
                    file.write("[]")

            if not UID_FILE_PATH.is_file():
                with UID_FILE_PATH.open(mode="w", encoding="utf-8") as file:
                    file.write("")

        except OSError as e:
            self.db_error = True
            raise InternalServerError from e

    def check_db_health(self) -> None:
        """Check db health before every request.

        Raises InternalServerError if db is corrupted.
        Gets called before every request.
        """
        if self.db_error:
            self.blog_posts = (
                self.load_data()
            )  # call fresh to update on the fly
            raise InternalServerError

    def page_not_found(self, _) -> tuple:  # noqa: ANN001
        """Render the 404 error page."""
        return render_template("404.html"), 404

    def internal_server_error(self, error: type[Exception] | int) -> tuple:
        """Render the 500 error page."""
        return render_template("500.html", error=error), 500

    def get_last_uid_from_posts(self) -> int:
        """Cycles through all blog posts to get last id."""
        if self.blog_posts:
            return max(post["id"] for post in self.blog_posts)
        return 0

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
        except OSError:
            print(ERR_NO_POST_UID)
            last_uid = ""

        try:
            new_uid = int(last_uid) + 1
        except ValueError:
            new_uid = self.get_last_uid_from_posts() + 1
        self.save_uid(new_uid)
        return new_uid

    def save_uid(self, new_uid: int) -> None:
        """Save the new UID to a file for future use."""
        try:
            with UID_FILE_PATH.open("w", encoding="utf-8") as f:
                f.write(str(new_uid))
        except OSError as e:
            print(ERR_SAVE_POST_UID)
            raise InternalServerError from e

    def route_index(self) -> str:
        """Render the index page with blog posts."""
        self.blog_posts = self.load_data()
        return render_template(
            "index.html",
            posts=self.blog_posts,  # refresh
            uuid=self.get_user_uid(),
            blogtitle="Mein Blog",
        )

    def route_add(self) -> str | Response:
        """Render form on get or save post on post."""
        if request.method == "POST":
            self.add_post(request.form.to_dict())  # use flat=False for multi
            return redirect(url_for("route_index"))

        return render_template("add.html")

    def route_delete(self, post_id: int) -> Response:
        """Delete a blog post by its ID."""
        if request.method == "POST":
            self.del_post(post_id)  # use flat=False for multi

        return redirect(url_for("route_index"))

    def get_user_uid(self) -> str:
        """Get or create a user uid (for the current session)."""
        if "user_uid" not in session:
            session["user_uid"] = str(uuid.uuid4())
        return session["user_uid"]

    def route_like_post(self, post_id: int) -> Response:
        """Route for toggling like status for a post by its ID."""
        user_uid = self.get_user_uid()
        self.toggle_like(post_id, user_uid)
        return redirect(url_for("route_index"))

    def toggle_like(self, post_id: int, user_uid: str) -> None:
        """Toggle the like status for a post by its ID."""
        posts_copy = deepcopy(self.blog_posts)
        for post in posts_copy:
            if post["id"] == post_id:
                likes = post.setdefault("liked_by", [])
                if user_uid in likes:
                    likes.remove(user_uid)
                else:
                    likes.append(user_uid)
        self.save_data(posts_copy)

    def fetch_post_by_id(self, post_id: int) -> dict | None:
        """Fetch a blog post from runtime data by its ID."""
        return next(
            filter(lambda post: post["id"] == post_id, self.blog_posts),
            None,
        )

    def route_update_post(self, post_id: int) -> str | tuple | Response:
        """Render the update page on GET or save changes on POST."""
        post = self.fetch_post_by_id(post_id)
        if post is None:
            return redirect(url_for("route_index"), 404)

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
            with DB_FILE_PATH.open("w", encoding="utf-8") as f:
                f.write(json.dumps(blog_posts))
        except OSError as e:
            raise InternalServerError(ERR_SAVE_DATA_FAILED) from e
        else:
            # update view only if crud went successful
            self.blog_posts = blog_posts

    def load_data(self) -> list:
        """Load blog posts from a JSON file."""
        # db file exists, but is empty
        if DB_FILE_PATH.stat().st_size == 0:
            self.blog_posts = []
        else:
            try:
                with DB_FILE_PATH.open(encoding="utf-8") as f:
                    self.blog_posts = json.load(f)
            except json.JSONDecodeError:
                print(ERR_DB_CORRUPT)
                self.db_error = True
            else:
                # reset in case error went puff
                self.db_error = False
        return self.blog_posts

    def run(self, **kwargs: Any) -> None:  # noqa: ANN401
        """Start the Flask app."""
        self.app.run(**kwargs)


if __name__ == "__main__":
    Masterblog().run(debug=True)
