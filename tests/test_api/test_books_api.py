# tests/test_api/test_books_api.py
def test_create_book_api(client):
    response = client.post(
        "/api/v1/books",
        json={
            "title": "Atomic Habits",
            "author": "James Clear"
        }
    )

    assert response.status_code in (200, 201)
    assert "id" in response.json()
