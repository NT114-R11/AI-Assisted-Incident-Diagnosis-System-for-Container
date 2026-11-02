SERVICE_DEPENDENCIES = {
    "order-service": {
        "cart-service": "http://cart-service:8003",
        "user-service": "http://user-service:8001",
    },
    "cart-service": {
        "product-service": "http://product-service:8002",
    },
    "product-service": {
        "user-service": "http://user-service:8001",
    },
}

POSTGRES_SERVICE = "postgres"