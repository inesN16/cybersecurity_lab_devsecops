| Finding ID | Title | Affected Component | Vulnerability Type |
| --- | --- | --- | --- |
| **F1** | Broken Access Control & Missing Authentication | `get_profile`, `get_grades`, `update_grade`, `download_file` | Authorization / Authentication Bypass |
| **F2** | Path Traversal via Unsanitized Input | `download_file` | Arbitrary File Read |
| **F3** | Insufficient Input Validation | `update_grade`, `get_profile`, `get_grades` | Data Integrity / Unhandled Exception |
| **F4** | Information Leakage in Global Error Handler | `handle_error` | Information Disclosure |

### F1: Broken Access Control & Missing Authentication

* **Location:** `baseline_secure_coding_api.py`, specifically functions `get_profile`, `get_grades`, `update_grade`, and `download_file`.


* **Attacker-controlled input and flow:** An attacker can issue HTTP `GET` and `POST` requests directly to protected routes such as `/students/<student_id>/profile`, `/grades/<student_id>`, `/grades/update`, and `/files`. The application router directs these to the respective functions without verifying the session.


* **Missing control and root cause:** The application lacks authentication checks (R1) and role/ownership authorization controls (R2, R3, R4) on all sensitive endpoints. The root cause is the absence of session verification (e.g., checking `flask.session`) and role-based logic within the route handlers.


* **Preconditions and impact:** Any user with network access to the API can exploit this. The impact is a complete loss of student privacy, allowing unauthorized viewing and modification of all grades and profiles.


* **Proposed test:** Send an unauthenticated `GET /students/1001/profile` request and verify that the server returns a 200 OK with Alice's profile data instead of a 401 Unauthorized response.
* **Assumptions, uncertainty, and confidence:** High confidence. It is assumed no external API gateway or invisible middleware handles authorization, as none is present in the source.



### F2: Path Traversal via Unsanitized Input

* **Location:** `baseline_secure_coding_api.py`, `download_file()` function, specifically `target = MATERIALS_DIR / raw_path`.


* **Attacker-controlled input and flow:** The `raw_path` variable is populated directly from the `path` URL query parameter (`flask.request.args.get("path", "")`). This string is concatenated with the base `MATERIALS_DIR` using `pathlib` and passed to `flask.send_file()`.


* **Missing control and root cause:** The application does not sanitize the `raw_path` input or verify that the resolved path remains within the `MATERIALS_DIR` boundary (R6). In Python's `pathlib`, appending an absolute path (e.g., `/etc/passwd`) to a base path overwrites the base path entirely.


* **Preconditions and impact:** Requires network access. An attacker can read arbitrary files on the host file system that the application process has permissions to read.
* **Proposed test:** Send the request `GET /files?path=/etc/passwd` or `GET /files?path=../../../../etc/passwd` and observe if the server returns the contents of the password file.
* **Assumptions, uncertainty, and confidence:** High confidence. Standard `pathlib.Path` concatenation allows absolute path overwrites and upward directory traversal if not explicitly constrained.



### F3: Insufficient Input Validation

* **Location:** `baseline_secure_coding_api.py`, `update_grade()` function. Secondary impact in `get_profile` and `get_grades`.


* **Attacker-controlled input and flow:** The JSON payload in `flask.request.get_json()` flows directly into variable assignment (`student_id`, `course_id`, `grade`) and then into the `GRADES` list.


* **Missing control and root cause:** Missing schema and range validation (R5). The application does not check if the grade is a numeric value between 0 and 20, rejects boolean types, validates known courses ("SRS", "SSD"), or ensures the `student_id` exists before updating. It also lacks error handling for missing JSON keys, which will throw a `KeyError`.


* **Preconditions and impact:** An attacker submitting data to `/grades/update` can corrupt the `GRADES` data structure with invalid types (e.g., booleans, strings) or out-of-bounds numbers. Missing JSON fields will crash the thread, triggering a 500 error.


* **Proposed test:** Send a `POST /grades/update` request with the JSON payload `{"student_id": 9999, "course_id": "UNKNOWN", "grade": true}` and verify that the application accepts and stores the invalid data.
* **Assumptions, uncertainty, and confidence:** High confidence. The code demonstrated relies entirely on naive dictionary extraction without type assertions.



### F4: Information Leakage in Global Error Handler

* **Location:** `baseline_secure_coding_api.py`, `handle_error(exc)` function.


* **Attacker-controlled input and flow:** Any malformed input that raises an unhandled exception (such as passing a non-integer string to `/students/abc/profile`, which calls `int(student_id)`) flows into the global `@app.errorhandler`.


* **Missing control and root cause:** The error handler takes the raw exception object and returns `str(exc)` and `exc.__class__.__name__` directly in the JSON response to the client (R7).


* **Preconditions and impact:** An attacker must induce an application exception. This leaks internal implementation details, exception logic, and potentially file paths or data structures to the client.


* **Proposed test:** Send an invalid type in a route variable, such as `GET /students/abc/profile`. Observe if the 500 response contains `"type": "ValueError"` and the string literal conversion error.
* **Assumptions, uncertainty, and confidence:** High confidence. Returning raw exception strings is a demonstrated code fact.