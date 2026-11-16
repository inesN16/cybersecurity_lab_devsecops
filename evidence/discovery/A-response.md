Here is the static security review of the provided application source.

### Summary of Findings

| ID | Title | Severity | Area |
| --- | --- | --- | --- |
| **VULN-001** | Path Traversal / Arbitrary File Read | Critical | `/files` Endpoint |
| **VULN-002** | Unauthenticated Grade Modification | Critical | `/grades/update` Endpoint |
| **VULN-003** | Broken Access Control / IDOR | High | Profile and Grades Retrieval Endpoints |
| **VULN-004** | Hardcoded Session Secret Key | High | Global Configuration |
| **VULN-005** | Plaintext Password Storage | High | User Data Model |

---

### Detailed Findings

#### VULN-001: Path Traversal / Arbitrary File Read

1. **Identifier and Title**: VULN-001 - Path Traversal in `/files` endpoint.
2. **Location**: `baseline_secure_coding_api.py`, `download_file()` function, lines 105-108.


3. **Execution/Data-Flow Path**: The attacker-controlled query parameter `path` is retrieved via `flask.request.args.get("path", "")` and concatenated directly to `MATERIALS_DIR` using the `pathlib` division operator (`MATERIALS_DIR / raw_path`). This target path is then passed directly to `flask.send_file(target)`.


4. **Missing/Incorrect Control and Root Cause**: The application lacks input validation and directory normalization. While `pathlib` is used, resolving paths with relative traversal segments (`../`) can escape the intended `MATERIALS_DIR` base directory.
5. **Preconditions and Potential Impact**: No authentication is required. An attacker can read arbitrary files on the server (e.g., source code, configuration files, system password files), leading to a severe breach of confidentiality.
6. **Proposed Test**: Send an unauthenticated request: `GET /files?path=../baseline_secure_coding_api.py`. If successful, the server will return its own source code instead of a file from the `materials` directory.
7. **Assumptions, Uncertainty, and Confidence**: Confidence is high. It is assumed the underlying operating system permits traversal using standard relative notation and the application runs with sufficient privileges to read sensitive files.

#### VULN-002: Unauthenticated Grade Modification

1. **Identifier and Title**: VULN-002 - Unauthenticated Grade Modification.
2. **Location**: `baseline_secure_coding_api.py`, `update_grade()` function, lines 91-103.


3. **Execution/Data-Flow Path**: The endpoint reads JSON data (`student_id`, `course_id`, `grade`) from `flask.request.get_json()`. It passes these values directly to `find_grade()` and subsequently mutates the global `GRADES` list.


4. **Missing/Incorrect Control and Root Cause**: The endpoint lacks both authentication (checking if a user is logged in) and authorization (checking if the user has the "professor" or "admin" role). The root cause is the absence of session validation logic prior to data mutation.
5. **Preconditions and Potential Impact**: No preconditions. Any network-adjacent attacker can manipulate academic records. Impact is a critical loss of data integrity.
6. **Proposed Test**: Send a POST request to `/grades/update` with `{ "student_id": 1001, "course_id": "SRS", "grade": 20 }` without providing any session cookie. Fetch `/grades/1001` to verify the grade changed.
7. **Assumptions, Uncertainty, and Confidence**: Confidence is high. The inferred security requirement is that only authorized personnel (like `prof_srs`) should modify grades, whereas the code demonstrates zero restrictions.

#### VULN-003: Broken Access Control / IDOR

1. **Identifier and Title**: VULN-003 - Insecure Direct Object Reference (IDOR) on Student Data.
2. **Location**: `baseline_secure_coding_api.py`, `get_profile()` (lines 80-84) and `get_grades()` (lines 86-89).


3. **Execution/Data-Flow Path**: The `student_id` is supplied in the URL path, converted to an integer, and directly used to query the `STUDENT_PROFILES` dictionary and `GRADES` list to return JSON responses.


4. **Missing/Incorrect Control and Root Cause**: There are no checks to verify that the requester is either the student matching `student_id`, a professor, or an admin. The code relies solely on the object identifier provided in the URI.
5. **Preconditions and Potential Impact**: None; the endpoints are entirely unauthenticated. An attacker can iterate over student IDs to scrape all profiles and academic records, violating confidentiality (PII and FERPA/GDPR equivalents).
6. **Proposed Test**: As an unauthenticated user (or while authenticated as "bob"), make a request to `GET /students/1001/profile`. If the application returns Alice's profile, the vulnerability is confirmed.
7. **Assumptions, Uncertainty, and Confidence**: Confidence is high. It is assumed that student records are meant to be private, despite the code treating them as publicly addressable resources.

#### VULN-004: Hardcoded Session Secret Key

1. **Identifier and Title**: VULN-004 - Hardcoded Cryptographic Secret.
2. **Location**: `baseline_secure_coding_api.py`, global configuration, line 8.


3. **Execution/Data-Flow Path**: The string `"dev-secret-key"` is directly assigned to `app.config["SECRET_KEY"]`. Flask uses this key to cryptographically sign session cookies.


4. **Missing/Incorrect Control and Root Cause**: The application fails to separate sensitive configuration from source code (e.g., via environment variables or a secure vault). The root cause is hardcoding secrets in the repository.
5. **Preconditions and Potential Impact**: An attacker must discover the key (e.g., via open source repository, or VULN-001 arbitrary file read). Once known, the attacker can forge Flask session cookies locally, bypass the `/login` endpoint entirely, and escalate privileges to "admin".
6. **Proposed Test**: Decode a legitimate Flask session cookie to get its structure. Using an offline script and the string `"dev-secret-key"`, sign a new session payload where `"user": "admin1"` and `"role": "admin"`. Inject this cookie into the browser and attempt to access protected resources.
7. **Assumptions, Uncertainty, and Confidence**: Confidence is high. The code clearly shows a non-production secret ("dev-secret-key"), assuming the file represents what is deployed.

#### VULN-005: Plaintext Password Storage

1. **Identifier and Title**: VULN-005 - Plaintext Password Storage.
2. **Location**: `baseline_secure_coding_api.py`, global `USERS` dictionary, lines 29-37.


3. **Execution/Data-Flow Path**: Passwords are mathematically compared as strings directly during login: `if user is None or user.password != password:`.


4. **Missing/Incorrect Control and Root Cause**: The application lacks a cryptographic hashing mechanism (like Argon2 or bcrypt) for passwords at rest.
5. **Preconditions and Potential Impact**: The attacker must gain read access to the application’s memory or source file (which is highly likely due to VULN-001). Impact is total compromise of all user accounts and potential credential stuffing attacks on other services used by these users.
6. **Proposed Test**: Examine the source code or use the VULN-001 Path Traversal to read the file and visually confirm the presence of `"alicepw"`, `"bobpw"`, `"profpw"`, and `"adminpw"`.


7. **Assumptions, Uncertainty, and Confidence**: Confidence is high. While this is an in-memory test database, it demonstrates a complete absence of cryptographic controls in the login flow.