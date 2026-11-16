### Static Security Review Findings

| ID | Title | Severity | Affected Function |
| --- | --- | --- | --- |
| **FINDING-1** | Path Traversal in File Download | Critical | `download_file` |
| **FINDING-2** | Unauthenticated Grade Modification | Critical | `update_grade` |
| **FINDING-3** | Missing Authentication / IDOR on Student Data | High | `get_profile`, `get_grades` |
| **FINDING-4** | Hardcoded Flask Secret Key | High | Global Configuration |
| **FINDING-5** | Information Exposure via Global Exception Handler | Medium | `handle_error` |

---

### Supporting Explanations

#### FINDING-1: Path Traversal in File Download

1. **Identifier and Title:** FINDING-1: Path Traversal in File Download.
2. **Location:** `baseline_secure_coding_api.py`, function `download_file`, line `target = MATERIALS_DIR / raw_path`.


3. **Execution/Data-Flow Path:** The attacker provides the `path` query parameter. This flows into `raw_path` and is concatenated with `MATERIALS_DIR` via `pathlib`. The resulting `target` is passed directly to `flask.send_file(target)`.


4. **Missing Control & Root Cause:** Missing input validation and path normalization checks. The root cause is blindly trusting user input to construct filesystem paths.
5. **Preconditions & Impact:** The application must have OS-level read access to the targeted files. The impact is arbitrary file read, allowing attackers to download source code, credentials, or sensitive system files (e.g., `/etc/passwd`).
6. **Proposed Test:** Issue `GET /files?path=../baseline_secure_coding_api.py` to attempt to download the application's source code.
7. **Assumptions & Confidence:** High confidence. It is a demonstrable code fact that `path` is unsanitized. I assume the underlying OS resolves `../` or absolute paths injected via the query parameter, which is standard behavior.



#### FINDING-2: Unauthenticated Grade Modification

1. **Identifier and Title:** FINDING-2: Unauthenticated Grade Modification.
2. **Location:** `baseline_secure_coding_api.py`, function `update_grade`.


3. **Execution/Data-Flow Path:** The attacker sends a POST request with JSON containing `student_id`, `course_id`, and `grade`. The data flows directly into updating the `GRADES` list in memory.


4. **Missing Control & Root Cause:** Missing authentication verification and Role-Based Access Control (RBAC). The root cause is the absence of any checks against `flask.session` to verify the user is logged in and holds a "professor" or "admin" role.


5. **Preconditions & Impact:** The API endpoint must be reachable. The impact is complete loss of integrity for the academic records, as any user (authenticated or not) can overwrite or create grades.
6. **Proposed Test:** Send `POST /grades/update` without session cookies and a JSON body of `{"student_id": 1001, "course_id": "SRS", "grade": 20}`. Verify the change via the `/grades/1001` endpoint.


7. **Assumptions & Confidence:** High confidence. The lack of checks is a code fact. The inferred security requirement is that only authorized personnel (professors/admins) should modify grades.

#### FINDING-3: Missing Authentication / IDOR on Student Data

1. **Identifier and Title:** FINDING-3: Missing Authentication / Insecure Direct Object Reference (IDOR) on Student Data.
2. **Location:** `baseline_secure_coding_api.py`, functions `get_profile` and `get_grades`.


3. **Execution/Data-Flow Path:** The attacker provides `student_id` in the URL path. This ID is used directly as a lookup key in `STUDENT_PROFILES` and `GRADES`, and the resulting data is returned to the user via `flask.jsonify`.


4. **Missing Control & Root Cause:** Missing authentication and authorization boundary enforcement. The root cause is the lack of session validation to ensure the requester is either the student matching the `student_id`, a professor, or an admin.
5. **Preconditions & Impact:** None. The impact is a breach of confidentiality, exposing Personally Identifiable Information (PII) and academic performance data to unauthorized parties.
6. **Proposed Test:** Issue unauthenticated `GET /students/1001/profile` and `GET /grades/1002` requests to observe the successful data retrieval.
7. **Assumptions & Confidence:** High confidence. I assume the policy dictates that student profiles and grades are confidential and should only be visible to the respective student or authorized faculty.

#### FINDING-4: Hardcoded Flask Secret Key

1. **Identifier and Title:** FINDING-4: Hardcoded Flask Secret Key.
2. **Location:** `baseline_secure_coding_api.py`, line `app.config["SECRET_KEY"] = "dev-secret-key"`.


3. **Execution/Data-Flow Path:** The Flask framework utilizes this hardcoded string to cryptographically sign session cookies generated during `login()`.


4. **Missing Control & Root Cause:** Missing secret management. The root cause is the hardcoding of cryptographic material directly in the source code.
5. **Preconditions & Impact:** The attacker must know or guess the key (trivial here as it is "dev-secret-key"). The impact is session forgery; an attacker can craft a valid session cookie to impersonate any user, including the "admin1" user.


6. **Proposed Test:** Use a tool to sign a Flask session cookie containing `{"user": "admin1", "role": "admin"}` using the key "dev-secret-key", then pass this cookie to `GET /me`.
7. **Assumptions & Confidence:** High confidence. Code fact: The key is static and weak.



#### FINDING-5: Information Exposure via Global Exception Handler

1. **Identifier and Title:** FINDING-5: Information Exposure via Global Exception Handler.
2. **Location:** `baseline_secure_coding_api.py`, function `handle_error`.


3. **Execution/Data-Flow Path:** Any unhandled exception triggered by malformed input routes to `handle_error`. The exception string `str(exc)` and type `exc.__class__.__name__` are extracted and returned in the HTTP response.


4. **Missing Control & Root Cause:** Improper error handling. The root cause is passing raw system/application exception messages directly to the client instead of generic error messages.
5. **Preconditions & Impact:** The attacker must trigger an application error (e.g., sending a string to an endpoint expecting an integer, causing a `ValueError` in `int(student_id)`). The impact is information disclosure of internal logic, variable types, or file paths. Additionally, the application runs with `debug=True`, which can expose interactive debuggers on crashes.


6. **Proposed Test:** Issue `GET /students/not_a_number/profile` to trigger a `ValueError` and observe the detailed response.
7. **Assumptions & Confidence:** High confidence. Code fact: Exception details are serialized into the JSON response.