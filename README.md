# Masterblog

A small Flask-based web application for managing a blog. Create, update, delete, and like posts using a custom file-based storage setup with simple session management.

## Requirements

- Python 3.10+
- Flask

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your web browser.

## Project structure

| File | Purpose |
| --- | --- |
| `app.py` | Flask routes, application setup, and core handlers |
| `blog_store.py` | `BlogStore` class for JSON persistence |
| `config.py` | Constants, file paths, and error messages |
| `templates/` | HTML templates for rendering pages |

## Acknowledgement

- Made with ❤️ and without ai or code completion (except this readme)