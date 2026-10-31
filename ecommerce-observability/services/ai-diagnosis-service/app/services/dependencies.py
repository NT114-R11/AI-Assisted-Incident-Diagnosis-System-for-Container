SERVICE_DEPENDENCIES = {
    "order-service": {
        "cart-service": "http://cart-service:8000",
        "user-service": "http://user-service:8000",
    },
    "cart-service": {
        "product-service": "http://product-service:8000",
    },
    "product-service": {
        "user-service": "http://user-service:8000",
    },
}

POSTGRES_SERVICE = "postgres"