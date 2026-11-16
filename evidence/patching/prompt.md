We are now repairing a confirmed vulnerability in the supplied application.

Confirmed finding:

Finding 1 (Path Traversal): In the download_file function, the path argument from the URL is just added directly to MATERIALS_DIR. An attacker can use "../" to escape the folder and read any file on the server.

Finding 2 (Broken Access Control): The update_grade function doesn't check if the user is logged in or what role they have. Anyone can just send a POST request with JSON data and change a grade.

Required behavior:

R1: We need to enforce authentication (valid session) for both of these endpoints.

R3: Only users with the "professor" or "admin" role should be allowed to modify grades in update_grade. Students must get a 403 error.

R6: The download_file endpoint must use path normalization to block access outside the intended materials directory.

Propose a minimal, reviewable patch addressing the root cause.
Preserve the API's legitimate functionality and relevant response contracts.
Do not delete endpoints, disable features, weaken tests, or suppress scanner rules to hide the issue. Identify all affected paths that need the same control.
Return a unified diff, explain the control being implemented, and identify remaining assumptions or limitations. Suggest additional regression tests.