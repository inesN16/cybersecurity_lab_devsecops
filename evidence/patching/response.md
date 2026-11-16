```diff
--- baseline_secure_coding_api.py
+++ baseline_secure_coding_api.py
@@ -107,6 +107,11 @@
 
 @app.post("/grades/update")
 def update_grade():
+    if "user" not in flask.session:
+        return {"error": "unauthenticated"}, 401
+    if flask.session.get("role") not in ["professor", "admin"]:
+        return {"error": "unauthorized"}, 403
+
     data = flask.request.get_json()
 
     student_id = data["student_id"]
@@ -122,8 +127,15 @@
 
 @app.get("/files")
 def download_file():
+    if "user" not in flask.session:
+        return {"error": "unauthenticated"}, 401
+
     raw_path = flask.request.args.get("path", "")
-    target = MATERIALS_DIR / raw_path
+    
+    target = (MATERIALS_DIR / raw_path).resolve()
+    if not target.is_relative_to(MATERIALS_DIR.resolve()):
+        return {"error": "access denied"}, 403
+
     return flask.send_file(target)

```

**Implemented Controls**

* **Authentication Validation**: Both the `/grades/update` and `/files` endpoints now verify that a `"user"` key exists within `flask.session` to ensure the user is authenticated.


* **Role-Based Access Control (RBAC)**: The `/grades/update` endpoint inspects the `"role"` value in `flask.session`. It blocks access with a 403 status code unless the role is explicitly `"professor"` or `"admin"`.


* **Path Normalization and Confinement**: The `/files` endpoint now constructs the file path and calls `.resolve()` to evaluate all `../` components, stripping them out. It then uses `is_relative_to()` to guarantee the final targeted file remains strictly inside the bounded `MATERIALS_DIR` base directory.



**Assumptions and Limitations**

* **Python Version**: The use of `.is_relative_to()` assumes the environment runs Python 3.9 or newer.
* **Session Integrity**: The security of this implementation relies entirely on Flask's cryptographically signed session cookie (`SECRET_KEY = "dev-secret-key"`). Because a hardcoded development key is used in this file, an attacker who obtains this key can forge arbitrary session cookies and bypass these checks.


* **File Existence**: The patch mitigates traversal but delegates file existence and read errors to the global `handle_error` exception handler, which returns a 500 error instead of a cleaner 404.



**Suggested Regression Tests**

* **Test Path Traversal Blocks**: Send `GET /files?path=../baseline_secure_coding_api.py` with an authenticated session; assert the response is `403 Forbidden` and the file contents are not leaked.
* **Test RBAC for Grades**: Authenticate as a `"student"` (e.g., using "alice" or "bob" credentials) and send a `POST /grades/update` payload. Assert the response is `403 Forbidden` and the grade is not updated in the `GRADES` list.


* **Test Authentication Enforcement**: Send unauthenticated requests (no session cookie) to both `/files` and `/grades/update`. Assert both return `401 Unauthorized`.


* **Test Legitimate Use**: Authenticate as `"prof_srs"` and modify a grade; authenticate as a student and fetch `srs-summary.txt`. Assert both succeed to ensure legitimate functionality is intact.