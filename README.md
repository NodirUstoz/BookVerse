# BookVerse - Online Bookstore & Reading Platform

BookVerse is a full-featured online bookstore and reading platform built with Django REST Framework and React. It provides a comprehensive book catalog, personalized recommendations, reading progress tracking, book clubs, wishlists, reviews, and a complete e-commerce checkout flow.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Features

### Bookstore
- Browse and search a comprehensive book catalog with advanced filtering
- Detailed book pages with descriptions, author info, and publisher data
- Genre-based navigation and curated collections
- Featured books, bestseller lists, and staff picks
- Shopping cart and secure checkout with order tracking

### Reading Platform
- Personal reading lists (Want to Read, Currently Reading, Finished)
- Reading progress tracking with page-level granularity
- Book clubs with member discussions and shared reading goals
- Personalized book recommendations powered by collaborative filtering
- Wishlists with sharing capabilities

### Social & Reviews
- Star ratings and detailed written reviews
- Helpful vote system for community-driven review quality
- Author pages with biographies and complete bibliographies
- User profiles with reading statistics and activity history

### Administration
- Full admin dashboard for inventory and order management
- Sales analytics and reporting
- User management and moderation tools
- Content curation for featured sections

## Architecture

```
                    +-------------------+
                    |    Nginx Proxy    |
                    +--------+----------+
                             |
              +--------------+--------------+
              |                             |
     +--------v---------+       +----------v----------+
     |  React Frontend  |       |  Django REST API     |
     |  (Port 3000)     |       |  (Port 8000)         |
     +------------------+       +----------+-----------+
                                           |
                          +----------------+----------------+
                          |                |                |
                 +--------v------+  +------v------+  +-----v--------+
                 |  PostgreSQL   |  |    Redis     |  | Elasticsearch|
                 |  (Port 5432)  |  | (Port 6379)  |  | (Port 9200)  |
                 +---------------+  +------+------+  +--------------+
                                           |
                                    +------v------+
                                    |   Celery    |
                                    |   Worker    |
                                    +-------------+
```

## Tech Stack

| Component       | Technology                          |
|-----------------|-------------------------------------|
| Backend         | Python 3.11, Django 4.2, DRF 3.14   |
| Frontend        | React 18, Redux Toolkit, Axios      |
| Database        | PostgreSQL 15                        |
| Cache / Broker  | Redis 7                              |
| Task Queue      | Celery 5.3                           |
| Search          | Elasticsearch 8.x                   |
| Reverse Proxy   | Nginx 1.25                           |
| Containerization| Docker, Docker Compose               |

## Getting Started

### Prerequisites

- Docker and Docker Compose (v2.0+)
- Git

### Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/bookverse.git
cd bookverse

# Copy environment file
cp .env.example .env

# Build and start all services
make build
make up

# Run database migrations
make migrate

# Create a superuser
make superuser

# Load sample data (optional)
make seed
```

The application will be available at:
- Frontend: http://localhost:3000
- API: http://localhost:8000/api/v1/
- Admin: http://localhost:8000/admin/
- API Docs: http://localhost:8000/api/v1/docs/

### Manual Setup (without Docker)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Frontend (in a separate terminal)
cd frontend
npm install
npm start
```

## Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

| Variable                  | Description                        | Default               |
|---------------------------|------------------------------------|-----------------------|
| `DJANGO_SECRET_KEY`       | Django secret key                  | (generated)           |
| `DJANGO_DEBUG`            | Enable debug mode                  | `True`                |
| `DJANGO_ALLOWED_HOSTS`    | Allowed host headers               | `localhost,127.0.0.1` |
| `DATABASE_URL`            | PostgreSQL connection string       | (see .env.example)    |
| `REDIS_URL`               | Redis connection string            | `redis://redis:6379/0`|
| `ELASTICSEARCH_URL`       | Elasticsearch URL                  | `http://es:9200`      |
| `CORS_ALLOWED_ORIGINS`    | Frontend origins for CORS          | `http://localhost:3000`|
| `EMAIL_HOST`              | SMTP server host                   | `smtp.gmail.com`      |
| `STRIPE_SECRET_KEY`       | Stripe API secret key              | (required for orders) |

See `.env.example` for the complete list.

## API Documentation

### Authentication

BookVerse uses JWT-based authentication. Obtain tokens via:

```
POST /api/v1/auth/token/
{
    "email": "user@example.com",
    "password": "yourpassword"
}
```

Include the access token in subsequent requests:

```
Authorization: Bearer <access_token>
```

### Key Endpoints

| Method | Endpoint                              | Description                   |
|--------|---------------------------------------|-------------------------------|
| GET    | `/api/v1/books/`                      | List books with filtering     |
| GET    | `/api/v1/books/{isbn}/`               | Book detail                   |
| GET    | `/api/v1/authors/`                    | List authors                  |
| GET    | `/api/v1/catalog/featured/`           | Featured books                |
| GET    | `/api/v1/catalog/bestsellers/`        | Bestseller list               |
| POST   | `/api/v1/orders/`                     | Create order                  |
| GET    | `/api/v1/reading/lists/`              | User reading lists            |
| POST   | `/api/v1/reading/progress/`           | Update reading progress       |
| GET    | `/api/v1/reading/clubs/`              | Book clubs                    |
| POST   | `/api/v1/reviews/`                    | Submit review                 |
| GET    | `/api/v1/recommendations/`            | Personalized recommendations  |
| GET    | `/api/v1/wishlist/`                   | User wishlist                 |

## Project Structure

```
bookverse/
├── backend/
│   ├── apps/
│   │   ├── accounts/       # User models, authentication, profiles
│   │   ├── books/          # Book, Author, Genre, Publisher models
│   │   ├── catalog/        # Featured books, bestsellers, collections
│   │   ├── orders/         # Shopping cart, orders, payments
│   │   ├── reviews/        # Ratings and reviews
│   │   ├── reading/        # Reading lists, progress, book clubs
│   │   ├── recommendations/# Recommendation engine
│   │   └── wishlist/       # User wishlists
│   ├── config/
│   │   ├── settings/       # Split settings (base, dev, prod)
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   └── celery.py
│   ├── utils/              # Shared utilities
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/            # API client and service modules
│   │   ├── components/     # Reusable React components
│   │   ├── pages/          # Page-level components
│   │   ├── store/          # Redux store and slices
│   │   ├── hooks/          # Custom React hooks
│   │   └── styles/         # Global styles
│   └── package.json
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
├── Makefile
└── .env.example
```

## Development

### Useful Commands

```bash
make up              # Start all services
make down            # Stop all services
make logs            # View container logs
make shell           # Django shell
make test            # Run backend tests
make test-frontend   # Run frontend tests
make lint            # Run linters
make migrate         # Run database migrations
make makemigrations  # Create new migrations
make seed            # Load sample data
make flush           # Reset database
```

### Code Quality

- Backend: `flake8`, `black`, `isort`, `mypy`
- Frontend: `eslint`, `prettier`
- Pre-commit hooks are configured for consistent code style

### Running Tests

```bash
# Backend tests
make test

# Frontend tests
make test-frontend

# Full test suite with coverage
make test-coverage
```

## Deployment

### Production Checklist

1. Set `DJANGO_DEBUG=False`
2. Configure a strong `DJANGO_SECRET_KEY`
3. Set up proper `DJANGO_ALLOWED_HOSTS`
4. Configure SSL/TLS certificates in Nginx
5. Set up proper email backend (SMTP)
6. Configure Stripe production keys
7. Set up database backups
8. Configure log aggregation
9. Set up monitoring and alerting
10. Review CORS and security headers

### Docker Production Build

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read our contributing guidelines and code of conduct before submitting changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
