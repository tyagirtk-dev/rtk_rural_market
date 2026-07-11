RTK Rural Market 🌾

A rural-focused e-commerce platform built with Flask, SQLAlchemy, Jinja2 and Bootstrap.
The project aims to provide a simple digital marketplace experience where users can browse products, manage carts, place orders and handle marketplace operations.

🚀 Features

User System

- User registration and login
- Secure password hashing
- User profile management
- Address management
- Wishlist support
- Notification system

Product Management

- Product categories
- Product listing
- Product images
- Stock management
- Product availability control
- Featured products

Shopping System

- Product browsing
- Cart management
- Order placement
- Order tracking flow
- Customer order history

Admin System

- Admin account management
- Product and category control
- Marketplace management
- Order monitoring

Security

- CSRF protection
- Login authentication
- Password hashing
- Rate limiting
- Error handling
- Application logging

🛠️ Tech Stack

- Python
- Flask
- Flask SQLAlchemy
- Flask Login
- Flask WTF
- Bootstrap 5
- SQLite (development)
- PostgreSQL (production ready)

📂 Project Structure

rtk_rural_market/
│
├── app.py
├── config.py
├── models/
├── routes/
├── templates/
├── static/
├── database/
└── logs/

⚙️ Installation

Clone repository:

git clone https://github.com/tyagirtk-dev/rtk_rural_market.git
cd rtk_rural_market

Install dependencies:

pip install -r requirements.txt

Run application:

python app.py

Application will start on:

http://127.0.0.1:5000

🔐 Default Admin

Admin account is created automatically from configuration settings.

Configure:

ADMIN_MOBILE
ADMIN_EMAIL
ADMIN_PASSWORD

before production deployment.

📌 Current Project Status

✅ Core marketplace system
✅ User authentication
✅ Product management
✅ Cart and order system
✅ Admin management

Future improvements:

- Seller/vendor dashboard
- Multi-vendor marketplace
- Online payment gateway integration
- Delivery tracking
- Mobile application

📄 License

This project is developed for learning and rural digital marketplace development.
