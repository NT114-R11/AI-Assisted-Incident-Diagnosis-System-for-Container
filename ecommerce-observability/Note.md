## 1. Set up môi trường test
- Sử dụng một `container` test để có thể chạy thử các unit test. Tại sao lại không sử dụng database thật để chạy test? Tuy Fixture mà pytest có thể giải quyết dữ liệu sau khi thực hiện xong. Nhưng nếu trong quá trình test. Nếu một test bị fail như ở bước tạo tài khoản (chẳng hạn), thì bước clean up của fixture sẽ không sử dụng --> trong database thật xuất hiện một user (rác).

- Tạo database test.

Khai báo `test container` vào file docker-compose.yml

```
test-postgres:
  image: postgres:16
  container_name: ecommerce-test-postgres
  environment:
    POSTGRES_USER: ${TEST_POSTGRES_USER}
    POSTGRES_PASSWORD: ${TEST_POSTGRES_PASSWORD}
    POSTGRES_DB: ${TEST_POSTGRES_DB}
  ports:
    - "${TEST_DB_PORT}:5432"
  volumes:
    - test_postgres_data:/var/lib/postgresql/data
  healthcheck:
    test:
      [
        "CMD-SHELL",
        "pg_isready -U ${TEST_POSTGRES_USER} -d ${TEST_POSTGRES_DB}"
      ]
    interval: 5s
    timeout: 5s
    retries: 5

```

- Đăng ký volumn cho container:
```
volumes:
  test_postgres_data:
```
- Tạo `setup_test_db.py` để khởi tạo một databse mẫu, và các test cho các feature.

- Thực hiện quá trình test:

Mở terminal và chạy

```
docker compose -f docker-compose.dev.yml up -d test-postgres

```

Để chạy test cần đứng ở folder "name_service"
```
export DATABASE_URL="postgresql+psycopg://test_admin:test_password_2026@localhost:5433/ecommerce_test"
python -m pytest -v

```

Access test database
```
docker exec -it ecommerce-test-postgres psql -U test_admin -d ecommerce_test

```

Tạo databse ảo

```
python -m tests.setup_test_db
```