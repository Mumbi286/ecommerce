# Ecom - Django E-Commerce Store

A full-featured e-commerce web application built with **Django 4.2**. It has a product catalog, a session-based shopping cart with AJAX updates, user registration with email verification, password reset, and a checkout flow that turns the cart into persisted orders.

## Features

- **Product catalog** - browse all products on the home page and view individual product pages via SEO-friendly slugs (auto-generated and guaranteed unique)
- **Session-based shopping cart** - add, update, and remove items without page reloads (jQuery + `JsonResponse` endpoints); the cart lives in the session, so guests can shop without an account, and the cart badge is available on every page through a template context processor
- **User accounts**
  - Registration with **email verification** - accounts stay inactive until the user clicks a tokenized activation link sent to their inbox
  - Login / logout
  - Profile page for updating username and email
  - Full **password reset** flow using Django's built-in auth views with custom templates
- **Orders & checkout**
  - Shipping address form (one address per user, editable)
  - Checkout page showing the saved address
  - Placing an order converts the cart into `Order` + `OrderItem` records
- **Product images** via Django's media handling (Pillow)
- **Tailwind CSS** (CDN) styling with responsive templates

## Tech Stack

| Layer     | Technology                                  |
|-----------|---------------------------------------------|
| Backend   | Python 3.8, Django 4.2                      |
| Database  | SQLite (Django default, dev-friendly)       |
| Frontend  | Django templates, Tailwind CSS (CDN), jQuery |
| Images    | Pillow                                      |
| Email     | Django SMTP backend (Gmail) / console backend for dev |
| Extras    | django-mathfilters (arithmetic in templates) |

## Project Structure

```
ecom/
├── requirements.txt
└── mysite/                  # Django project root (manage.py lives here)
    ├── manage.py
    ├── db.sqlite3
    ├── media/               # uploaded product images (gitignored)
    ├── mysite/              # project settings & root URLconf
    ├── myapp/               # product catalog (Product model, home & detail pages)
    ├── cart/                # session-based cart (no DB model)
    │   ├── cart.py          #   the Cart class — all cart logic
    │   └── context_processors.py  # exposes {{ cart }} to every template
    ├── users/               # auth: register, email verification, login, profile, password reset
    │   └── token.py         #   custom activation-token generator
    └── orders/              # Address, Order, OrderItem models + checkout flow
```

## Getting Started

### Prerequisites

- Python 3.8+
- pip / virtualenv

### Installation

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd ecom
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv env
   source env/bin/activate       
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   pip install django-mathfilters  

   ```

4. **Apply database migrations**

   ```bash
   cd mysite
   python manage.py migrate
   ```

5. **Create an admin user** (to add products via the admin panel)

   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**

   ```bash
   python manage.py runserver
   ```

   Visit **http://127.0.0.1:8000/** for the store and **http://127.0.0.1:8000/admin/** to add products.


## How It Works

### Shopping cart

The cart is **not stored in the database**. `cart/cart.py` defines a `Cart` class that reads and writes `request.session['cart']`, a dictionary of `{product_id: {'price': ..., 'qty': ...}}`. Add / update / delete actions are sent by jQuery `POST` requests and answered with JSON, so the page never reloads — only the cart badge and totals update. A context processor (`cart.context_processors.cart`) makes the cart available as `{{ cart }}` in every template.

### Email verification

When a user registers, the account is created with `is_active = False` so they cannot log in yet. The app then emails them a link containing their base64-encoded user ID and a one-time token. The token generator (`users/token.py`) includes `is_active` in its hash, which means the link automatically stops working once the account has been activated. Clicking a valid link flips `is_active` to `True` and shows a success page.

### Checkout

An authenticated user saves a shipping address (one per account). On checkout, `place_order` reads the session cart, creates an `Order` with the cart total, and one `OrderItem` per cart line. Order totals per item are computed on the fly via the `OrderItem.total_price` property.

## URL Overview

| Path | Purpose |
|------|---------|
| `/` | Product listing (home) |
| `/<slug>` | Product detail |
| `/cart/cart-overview` | View cart |
| `/cart/add` · `/cart/update` · `/cart/delete` | AJAX cart endpoints |
| `/users/register/` | Sign up (triggers verification email) |
| `/users/login/` · `/users/logout/` | Authentication |
| `/users/profile/` | Edit profile |
| `/users/password-reset` | Password reset flow |
| `/orders/add-address/` | Add / edit shipping address |
| `/orders/checkout/` | Checkout page |
| `/orders/place-order` | AJAX order creation |
| `/admin/` | Django admin (manage products) |

## Roadmap

- [ ] Payment gateway integration (`Order.is_paid` exists but is never set)
- [ ] Order history page for users
- [ ] Product categories and search
- [ ] Pin `django-mathfilters` in `requirements.txt`

## License

This is a personal learning project - no license has been chosen yet.
