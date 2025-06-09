# Testing Guide

## Running Unit Tests

We use `pytest` for unit testing.

1. **Install pytest**
   ```powershell
   pip install pytest
   ```

2. **Run tests**
   ```powershell
   pytest
   ```

## Test Coverage

- **GET /classes**: Returns all classes, checks for correct fields and timezones.
- **POST /book**: Validates booking, prevents overbooking, checks for missing fields.
- **GET /bookings**: Returns bookings for a given email, handles no bookings case.
- **Timezone**: Ensures class times are correctly converted to IST.
- **Error Handling**: Tests for invalid input, overbooking, and missing data.

## Example Test Case

```python
def test_overbooking(client):
    # Book all available slots
    for _ in range(available_slots):
        response = client.post("/book", json={...})
        assert response.status_code == 200
    # Try to overbook
    response = client.post("/book", json={...})
    assert response.status_code == 400
    assert "No slots available" in response.json()["detail"]
```
