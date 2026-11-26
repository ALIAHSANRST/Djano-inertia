# Django + Inertia + React + shadcn/ui Starter Kit

A full-stack starter for building web apps with **Django** on the backend and **React** on the frontend, glued together by **Inertia.js** — no separate API, no separate SPA deployment. It ships with a production-ready **admin console** built on **shadcn/ui**: users, groups, permissions, light and dark themes.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/dashboard-dark.png">
  <img alt="Admin dashboard" src="docs/images/dashboard-light.png">
</picture>

## Features

- **Django 6** owns routing, authentication, permissions and validation
- **Inertia.js 2 + React 18** for SPA-speed navigation with server-side routing
- **shadcn/ui** (new-york, zinc) with the Geist font, light and dark themes
- **Admin console** — collapsible sidebar, breadcrumbs, ⌘K command palette, toasts, responsive mobile layout
- **User & group management** — search, sorting, pagination, validation, safe deletes
- **Secure by default** — Django model permissions, superuser-only privilege changes, self-lockout protection, password validation, login throttling, CSRF
- **Clean architecture** — views → services → selectors / policies, with DTOs at the boundaries ([details](docs/architecture.md))
- **Celery + Redis** for background jobs, with **Celery Beat** schedules editable in Django admin
- **Vite 7** dev server with HMR and manifest-based production builds
- **Tested** — 100+ Django tests, ESLint and Vitest on the frontend

## Screenshots

| Sign in | Users |
|---|---|
| ![Sign in page](docs/images/login-light.png) | ![Users list](docs/images/users-light.png) |
| **Edit user** | **Command palette (⌘K)** |
| ![Edit user form](docs/images/user-edit-light.png) | ![Command palette](docs/images/command-dark.png) |
| **Groups** | **Collapsed sidebar** |
| ![Groups list](docs/images/groups-dark.png) | ![Collapsed sidebar](docs/images/collapsed-light.png) |

<p>
  <img alt="Mobile dashboard" src="docs/images/mobile-light.png" width="260">
  &nbsp;
  <img alt="Mobile navigation" src="docs/images/mobile-nav-dark.png" width="260">
</p>

More in the [screenshot gallery](docs/screenshots.md).

## Quick start

**Requirements:** Python 3.12+ ([uv](https://github.com/astral-sh/uv) recommended) and Node.js 20.19+.

```bash
git clone git@github.com:crenspire/django-react-boilerplate.git
cd django-react-boilerplate

# Backend
uv run python starterkit/manage.py migrate
uv run python starterkit/manage.py createsuperuser
uv run python starterkit/manage.py runserver

# Frontend (second terminal)
cd starterkit/frontend
npm install
npm run dev
```

Open **http://127.0.0.1:8000** for the landing page and **http://127.0.0.1:8000/admin/** for the admin console.

Background jobs need Redis, a Celery worker and Beat. Start Redis with `docker compose up -d`, then run everything at once with `uvx honcho -f Procfile.dev start` (see [Background tasks](docs/background-tasks.md)).

The full walkthrough is in [Getting started](docs/getting-started.md).

## Project Budget Requests

Open `/budgets/` and sign in with a Django account. Django routes each user to the dashboard for their budget role.

| Role | Workflow |
|---|---|
| Client | Submit requests, track personal requests and review notes, and edit or withdraw pending requests. |
| Manager | Review the organization-wide queue and history. Approval notes are optional. Rejections require a note. |
| Admin | See organization-wide pending and approved funding totals, browse all requests, and permanently delete records. Django superusers have this role automatically. |

### Set up the budget workflow

From the repository root, install the locked dependencies, migrate the database, and create a superuser.

```bash
uv sync --locked
uv run python starterkit/manage.py migrate
uv run python starterkit/manage.py createsuperuser
```

Run `uv run python starterkit/manage.py runserver` from the repository root. In a second terminal, run `npm ci` and `npm run dev` from `starterkit/frontend`. Sign in to `/admin/` with the superuser and use **Users → Add user** to create separate accounts for the Client and Manager. Existing active accounts default to Client. As a superuser, use the **Budget role** picker on the user form to assign Client, Manager, or Admin. The management command remains available for server-side administration.

```bash
uv run python starterkit/manage.py set_budget_role budget-manager manager
uv run python starterkit/manage.py set_budget_role budget-admin admin
```

Use the actual account usernames in these commands. A separate Budget Admin account is optional. Django staff status controls access to the starter admin console independently of budget roles.

Local development defaults to SQLite at `starterkit/db.sqlite3`, debug mode, and the Vite dev server at `http://localhost:5173`. Set `DJANGO_SQLITE_PATH` for a custom database path. For deployment, set `DJANGO_DEBUG=false`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` for any additional trusted origins, and `VITE_DEV_MODE=false`. Run `npm ci` and `npm run build` in the frontend directory, then `uv run python starterkit/manage.py migrate` and `uv run python starterkit/manage.py collectstatic --noinput` from the root. See [Deployment](docs/deployment.md) for HTTPS, static files, cache, and process configuration. The budget workflow has no dependency on Celery or Redis for local use.

### Architecture and trade-offs

- Django retains the starter User model. An optional one-to-one profile holds the budget role. The trusted management command handles assignments. Native Django account mutations require a superuser. Delegated account management lives in the existing Inertia console and protects elevated budget accounts.
- The budgets app separates thin Inertia views, immutable input DTOs, workflow services, domain policies, and query selectors. React uses Inertia props and forms with existing shadcn/ui primitives.
- Status and reviewer metadata are constrained in the database. Conditional updates check both pending state and revision in the same statement to prevent double decisions, edits after a decision, and approval of a changed request.
- Withdrawal preserves the record and excludes it from the active queue and funding totals. Permanent deletion removes the record and its review details. Referenced users can be deactivated while their request or review history is retained.
- Totals use exact integer-cent aggregation. The workflow assumes one organization-wide currency with two decimal places. It uses the starter SQLite configuration and has no separate approval audit log, notifications, or currency conversion.

Run the feature tests with `uv run python starterkit/manage.py test apps.budgets`.

## Documentation

| Guide | What's inside |
|---|---|
| [Getting started](docs/getting-started.md) | Install, run, create an admin, project layout |
| [Architecture](docs/architecture.md) | Layers and rules, request lifecycle, adding a feature step by step |
| [Permissions](docs/permissions.md) | Who can do what in the admin and how to change it |
| [Frontend](docs/frontend.md) | Admin shell, pages, shadcn/ui components, routes, theming |
| [Background tasks](docs/background-tasks.md) | Celery workers, Beat schedules, Redis |
| [Configuration](docs/configuration.md) | Environment variables |
| [Deployment](docs/deployment.md) | Production build, static files, security checklist |
| [Testing](docs/testing.md) | Running and writing backend and frontend tests |

## Project structure

```
starterkit/
├── main/                     # Django project: settings, urls, middleware, Celery app, route map
├── apps/system/              # Maintenance services and Celery tasks
├── apps/admin_panel/         # Admin console
│   ├── api/                  #   views: parse request → call one service → respond
│   ├── services/             #   business logic and page props
│   ├── selectors/            #   all ORM queries
│   ├── domain/               #   permission policies
│   ├── dto/                  #   immutable input/output containers
│   ├── infrastructure/       #   adapters for external systems (cache)
│   └── tests/
├── frontend/                 # React + Vite + Inertia
│   ├── Pages/                #   one component per Inertia page
│   ├── Layouts/              #   AdminLayout, AuthLayout
│   ├── Components/           #   ui/ (shadcn/ui), admin/ (app components)
│   ├── composables/          #   React hooks
│   └── lib/                  #   pure helpers (+ unit tests)
├── templates/base.html       # Inertia root template
└── manage.py
```

## Tests

```bash
uv run python starterkit/manage.py test      # backend

cd starterkit/frontend
npm run lint && npm test                      # frontend
```

## License

MIT. Use this starter for personal or commercial projects.
