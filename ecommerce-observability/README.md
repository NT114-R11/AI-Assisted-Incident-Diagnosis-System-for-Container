DACN — E-Commerce Observability Progress

Project Goal

Build an E-Commerce application as the experimental environment for:
Design and Implementation of an AI-Assisted Incident Diagnosis System for Containerized Infrastructure Using Metrics, Logs, and Service Status

Approach:

Build E-Commerce first.

Stabilize it.

Add observability.

Add AI-assisted incident diagnosis.

Keep it practical for a 3-month timeline.

Avoid unnecessary over-engineering.

Architecture

4 services:

User Service: User, Authority

Product Service: Seller, Product

Cart Service: Cart, CartItem

Order Service: Customer, ShippingAddress, BillingAddress, Order

Infrastructure:

FastAPI

SQLAlchemy

PostgreSQL 16

psycopg

Pydantic

httpx

Docker / Docker Compose

Python 3.12

PostgreSQL is currently shared by all services for infrastructure simplicity. Services keep separate models/routers/sessions and communicate through HTTP.

Ports

Service

Host

Container

Product

8002

8000

Cart

8003

8000

Order

8004

8000

User

TBD

8000

Internal URLs:

http://product-service:8000

http://cart-service:8000

http://order-service:8000

http://user-service:8000

Product Service

CRUD is complete and tested.

Endpoints:

GET    /products/
GET    /products/{product_id}
POST   /products/
PUT    /products/{product_id}
DELETE /products/{product_id}

Current Product fields:

product_id
product_name
quantity
description
manufacturer
categories
price

Seller addition

Seller was identified as a missing E-Commerce domain.

Planned relationship:

Seller 1 ───── N Product

Product will therefore contain:

seller_id

Seller belongs in Product Service because the seller manages products and stock.

Seller does not need a direct FK in Order.

Cart Service

Cart CRUD is complete and tested.

Endpoints:

POST   /carts/
GET    /carts/{cart_id}
POST   /carts/{cart_id}/items
PUT    /carts/{cart_id}/items/{item_id}
DELETE /carts/{cart_id}/items/{item_id}
DELETE /carts/{cart_id}

Cart calls Product Service:

PRODUCT_SERVICE_URL = "http://product-service:8000"

Add-item flow:

Check Cart.

GET Product.

Product unavailable → 503.

Product missing → 404.

Check stock.

Existing product → increase quantity.

New product → create CartItem.

Snapshot Product price into CartItem.

Recalculate total_price.

Commit.

Cart:

cart_id
customer_id
total_price

CartItem:

item_id
quantity
price
product_id
cart_id

product_id is an external reference to Product Service, not a DB FK.

Order Service

Order Service has been created and Docker is running correctly.

Structure:

services/order-service/
├── app/
│   ├── database/
│   ├── models/
│   │   ├── customer.py
│   │   ├── order.py
│   │   ├── shipping_address.py
│   │   └── billing_address.py
│   ├── schemas/
│   │   ├── customer.py
│   │   ├── order.py
│   │   ├── shipping_address.py
│   │   └── billing_address.py
│   └── routers/
│       ├── customer.py
│       ├── shipping_address.py
│       ├── billing_address.py
│       └── order.py
├── Dockerfile
└── requirements.txt

Order relationships

Customer 1 ───── N ShippingAddress
Customer 1 ───── N BillingAddress
Customer 1 ───── N Order

Order N ───── 1 ShippingAddress
Order N ───── 1 BillingAddress

Order fields:

order_number       PK
customer_id        FK → Customer
cart_id            external reference → Cart Service
order_date
shipping_address_id FK → ShippingAddress
billing_address_id  FK → BillingAddress
status

Default status:

pending

The latest ERD/model does not contain total_price in Order. Cart has total_price. Do not silently add it unless the ERD/business design is explicitly changed.

Order Router — Missing Microservice Communication

The initial Order Router was only CRUD.

Order creation should communicate with Cart Service:

POST /orders
      │
      ├── Check Customer
      ├── Check ShippingAddress
      ├── Check ShippingAddress belongs to Customer
      ├── Check BillingAddress
      ├── Check BillingAddress belongs to Customer
      ├── HTTP GET Cart Service
      ├── Check Cart exists
      ├── Check Cart belongs to Customer
      └── Create Order

Order Service should define:

CART_SERVICE_URL = "http://cart-service:8000"

Cart Service already calls Product Service, so Order does not need PRODUCT_SERVICE_URL.

Error handling:

Cart not found → 404
Cart Service unavailable → 503
Cart belongs to another customer → 400

No retry, circuit breaker, distributed transaction, Kafka, Redis, API Gateway, or Service Mesh is currently planned.

Customer

Current fields:

customer_id
name
email
phone

Relationships:

Customer
├── orders
├── shipping_addresses
└── billing_addresses

Customer currently belongs to Order Service.

The exact Customer ↔ User Service mapping is not finalized. Do not assume a direct User API call until the mapping is defined.

ShippingAddress

id
customer_id
address
city

Relationships:

Customer 1 ───── N ShippingAddress
Order N ───── 1 ShippingAddress

Business rule:

shipping_address.customer_id == order.customer_id

BillingAddress

id
customer_id
address
city

Relationships:

Customer 1 ───── N BillingAddress
Order N ───── 1 BillingAddress

Business rule:

billing_address.customer_id == order.customer_id

Seller — Newly Identified Requirement

Current system originally modeled only buyers/customers.

Planned domain:

User Service
├── User
└── Authority

Product Service
├── Seller
└── Product
       └── seller_id

Seller responsibilities:

Create products

Update products

Delete products

Manage product stock

View products owned by the seller

Later authorization can restrict product modification to the owning seller. Authentication/authorization should be added later without expanding architecture unnecessarily.

Next Steps

Step 1 — Update ERD

Add:

Seller 1 ───── N Product
Product.seller_id

Step 2 — Implement Seller in Product Service

Add:

Seller model
Seller schemas
Seller router

Basic CRUD is enough initially.

Step 3 — Update Product

Add seller_id and validate Seller existence when creating a Product.

Step 4 — Test Seller → Product

Create Seller
     ↓
Create Product with seller_id
     ↓
Get Seller's Products

Step 5 — Return to Order Router

Implement:

Order → Cart Service

using:

CART_SERVICE_URL = "http://cart-service:8000"

Architecture Principles

Microservices communicate through HTTP.

No model imports across services.

No cross-service DB foreign keys.

Shared PostgreSQL is an infrastructure simplification.

Each service owns its own domain models and routers.

Keep schemas/.

Avoid premature infrastructure such as API Gateway, Redis, Kafka, Service Mesh, Circuit Breaker, Distributed Transactions, and complex auth infrastructure.

Add complexity only when it directly supports the DACN.

Build application first, observability second, AI diagnosis third.

Prefer a working simple system over repeated architecture refactoring.

Overall Domain

                         User Service
                      ┌────────────────┐
                      │      User      │
                      │   Authority    │
                      └────────────────┘

        Seller Side                         Buyer Side

      Seller                                  Customer
         │                                      │
         │ 1:N                                  │ 1:1
         ▼                                      ▼
      Product                                  Cart
         │                                      │
         │                                      │ 1:N
         │                                      ▼
         │                                  CartItem
         │                                      │
         └───────────────┐                      │
                         │                      │
                         ▼                      ▼
                  Product Service ────────► Cart Service
                                                   │
                                                   │ HTTP
                                                   ▼
                                             Order Service
                                                   │
                         ┌─────────────────────────┼────────────────────┐
                         │                         │                    │
                         ▼                         ▼                    ▼
                      Customer             ShippingAddress       BillingAddress
                         │
                         └──────────────────► Order

The next chat should continue from this exact state.