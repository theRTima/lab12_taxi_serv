def test_role_guards_and_order_payment_reports(client, admin_token, client_token, driver_token):
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    headers_client = {"Authorization": f"Bearer {client_token}"}
    headers_driver = {"Authorization": f"Bearer {driver_token}"}

    # admin endpoint
    resp = client.get("/admin/users/list", headers=headers_admin)
    assert resp.status_code == 200

    resp = client.get("/admin/users/list", headers=headers_client)
    assert resp.status_code == 403

    # driver-only endpoint
    resp = client.get("/drivers/me", headers=headers_driver)
    assert resp.status_code == 200

    # client creates order
    resp = client.post(
        "/orders",
        json={"tariff_id": 1, "pickup": "A", "destination": "B"},
        headers=headers_client,
    )
    assert resp.status_code == 201
    order = resp.json()
    order_id = order["id"]

    # driver can view pending unassigned order
    resp = client.get(f"/orders/{order_id}", headers=headers_driver)
    assert resp.status_code == 200

    # get driver profile id
    resp = client.get("/drivers/me", headers=headers_driver)
    driver_profile = resp.json()
    driver_profile_id = driver_profile["id"]

    # driver assigns & progresses order
    resp = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "assigned", "driver_id": driver_profile_id},
        headers=headers_driver,
    )
    assert resp.status_code == 200

    resp = client.patch(
        f"/orders/{order_id}/status", json={"status": "in_progress"}, headers=headers_driver
    )
    assert resp.status_code == 200

    resp = client.patch(
        f"/orders/{order_id}/status", json={"status": "completed"}, headers=headers_driver
    )
    assert resp.status_code == 200

    # client cannot update completed order
    resp = client.patch(f"/orders/{order_id}", json={"pickup": "X"}, headers=headers_client)
    assert resp.status_code == 400

    # simulate payment for completed order
    resp = client.post(
        "/payments/simulate",
        json={
            "order_id": order_id,
            "amount": 42.5,
            "card_number": "4111111111111111",
            "card_holder": "Client Person",
        },
        headers=headers_client,
    )
    assert resp.status_code == 201
    payment = resp.json()
    assert payment["amount"] == 42.5
    assert payment["status"] == "paid"

    # simulate decline for card ending 0000
    resp = client.post(
        "/payments/simulate",
        json={"order_id": order_id, "amount": 10, "card_number": "4000000000000000", "card_holder": "X"},
        headers=headers_client,
    )
    assert resp.status_code == 400

    # invalid card number (letters) -> 422
    resp = client.post(
        "/payments/simulate",
        json={"order_id": order_id, "amount": 10, "card_number": "abcd-efgh-ijkl", "card_holder": "X"},
        headers=headers_client,
    )
    assert resp.status_code == 422

    # amount 0 -> 422
    resp = client.post(
        "/payments/simulate",
        json={"order_id": order_id, "amount": 0, "card_number": "4111111111111111", "card_holder": "X"},
        headers=headers_client,
    )
    assert resp.status_code == 422

    # get report summary (any authenticated user)
    resp = client.get("/reports/summary", headers=headers_admin)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_orders" in data
    assert "revenue_by_tariff" in data
    assert "top_drivers" in data
    assert "orders_per_day" in data

    # get payment for order
    resp = client.get(f"/payments/order/{order_id}", headers=headers_client)
    assert resp.status_code == 200
    assert resp.json()["amount"] == 42.5

    payment_id = payment["id"]
    # admin can update payment
    resp = client.patch(f"/payments/{payment_id}", json={"status": "refunded"}, headers=headers_admin)
    assert resp.status_code == 200
    assert resp.json()["status"] == "refunded"

    # client lists their payments
    resp = client.get("/payments", headers=headers_client)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
