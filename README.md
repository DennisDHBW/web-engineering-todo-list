# web-engineering-todo-list

This project is designed as a scalable, real-time task management backend.
It supports core features such as user authentication, project/task management,
real-time WebSocket updates and scheduled background reminders via Celery.
Several advanced features (2FA, RBAC, external integrations) were considered but left unimplemented due to time constraints.

## How attachments would work in a production-ready system

To implement secure file uploads, the backend would:
1. Accept files via multipart/form-data and validate their type and size.
2. Store the file using a UUID-based filename in a cloud object storage (e.g., AWS S3).
3. Save metadata (original name, user ID, task ID, timestamp) in the database.
4. Generate a secure download URL (presigned or tokenized) only accessible to project members.
5. Protect the file endpoint via JWT and role-based access.

This simulation avoids complexity but maintains a realistic structure for future integration.
