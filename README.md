# TestVar Flashcards 📚✨

Welcome to TestVar Flashcards, a dynamic and user-friendly flashcard website that allows you to create, share, and study flashcards effortlessly. The platform is backed by a Django-powered REST API aligned with an OpenAPI specification, ensuring a standardized and clean architecture.

# Overview 🌐

Core Idea: Create sets of flashcards, add cards, rate sets, post comments, and manage daily limits on flashcard and set creation.
Technology Stack: Django, Django REST Framework, TailwindCSS, JavaScript, and SQLite for simplicity.
API Standard: The backend aligns with an OpenAPI specification for clarity and interoperability.


# Key Features 🌟
User Management:

1. Sign up and log in securely.
   Admin dashboard (via Django admin) to adjust global creation limits and manage content.

3. Create up to 5 flashcard sets per day (default, adjustable by admin).
Add up to 50 flashcards per day (default, adjustable by admin).
Each flashcard shows difficulty (Easy/Medium/Hard) with color-coded tags.
Comments and Ratings:

4. Users can comment on sets and collections.
Rate sets with a 1–5 star system. View average rating in real-time.
Collections:

5. Organize sets into collections.
Add/remove sets from collections easily.
Daily collection creation limits are enforced.
Search & Browse:

6. Quickly find sets by keyword.
Browse sets and view details (some content available without logging in).

## installing dependancies

```python
pip install -r requirements.txt
```

## To collect static files:

```python
python manage.py collectstatic
```

## To run this application:

```python
python manage.py runserver
```
