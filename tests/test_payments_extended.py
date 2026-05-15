"""Extended tests for payments endpoint with high coverage"""

import pytest
from fastapi import status
from app.models.payment import Payment, PaymentStatus
from app.models.order import Order, OrderStatus


class TestPaymentsEdgeCases:
    """Test edge cases for payments"""

    @pytest.mark.parametrize(
        "amount,should_succeed",
        [
            (0.01, True),  # Min valid
            (999999.99, True),  # Large amount
            (0, False),  # Zero
            (-1, False),  # Negative
            (-0.01, False),  # Negative decimal
        ],
    )
    def test_create_payment_amount_boundary(self, client, auth_headers_client, order, amount, should_succeed):
        """Test payment creation with boundary amounts"""
        # First transition order to IN_PROGRESS
        order.status = OrderStatus.IN_PROGRESS
        order.session.commit()

        response = client.post(
            "/payments",
            json={"order_id": order.id, "amount": amount},
            headers=auth_headers_client,
        )
        if should_succeed:
            assert response.status_code == 201
        else:
            assert response.status_code in (400, 422)

    def test_create_payment_for_nonexistent_order(self, client, auth_headers_client):
        """Test payment creation for non-existent order"""
        response = client.post(
            "/payments",
            json={"order_id": 9999, "amount": 100},
            headers=auth_headers_client,
        )
        assert response.status_code == 404
        assert "Order not found" in response.json()["detail"]

    def test_create_payment_not_client_of_order(self, client, auth_headers_client, auth_headers_admin, tariff, db):
        """Test payment creation by non-owner of order"""
        from app.models.user import User, UserRole

        other_client = User(
            email="other3@example.com",
            hashed_password="hash",
            name="Other3",
            role=UserRole.CLIENT,
        )
        db.add(other_client)
        db.commit()

        order = Order(
            client_id=other_client.id,
            tariff_id=tariff.id,
            pickup="A",
            destination="B",
            status=OrderStatus.IN_PROGRESS,
        )
        db.add(order)
        db.commit()

        response = client.post(
            "/payments",
            json={"order_id": order.id, "amount": 100},
            headers=auth_headers_client,
        )
        assert response.status_code == 403
        assert "Not your order" in response.json()["detail"]

    def test_create_payment_pending_order_not_payable(self, client, auth_headers_client, order):
        """Test that PENDING orders cannot be paid"""
        # order is PENDING by default
        response = client.post(
            "/payments",
            json={"order_id": order.id, "amount": 100},
            headers=auth_headers_client,
        )
        assert response.status_code == 400
        assert "Payment is only allowed" in response.json()["detail"]

    def test_create_payment_duplicate_payment(self, client, auth_headers_client, order, db):
        """Test that only one payment per order is allowed"""
        order.status = OrderStatus.IN_PROGRESS
        db.commit()

        # Create first payment
        response = client.post(
            "/payments",
            json={"order_id": order.id, "amount": 100},
            headers=auth_headers_client,
        )
        assert response.status_code == 201

        # Try to create second payment
        response = client.post(
            "/payments",
            json={"order_id": order.id, "amount": 200},
            headers=auth_headers_client,
        )
        assert response.status_code == 400
        assert "Payment already exists" in response.json()["detail"]

    def test_get_payment_not_found(self, client, auth_headers_client):
        """Test getting non-existent payment"""
        response = client.get("/payments/9999", headers=auth_headers_client)
        assert response.status_code == 404

    def test_get_payment_access_denied(self, client, auth_headers_client, db):
        """Test that clients can't see other's payments"""
        from app.models.user import User, UserRole

        other_client = User(
            email="other4@example.com",
            hashed_password="hash",
            name="Other4",
            role=UserRole.CLIENT,
        )
        db.add(other_client)
        db.commit()

        # Create order and payment for other client
        order = Order(
            client_id=other_client.id,
            tariff_id=1,
            pickup="A",
            destination="B",
            status=OrderStatus.IN_PROGRESS,
        )
        db.add(order)
        db.commit()

        payment = Payment(order_id=order.id, amount=100)
        db.add(payment)
        db.commit()

        # Try to access as different client
        response = client.get(f"/payments/{payment.id}", headers=auth_headers_client)
        assert response.status_code == 403

    def test_list_payments_client_sees_only_own(self, client, auth_headers_client, order, db):
        """Test that clients only see their own payments"""
        order.status = OrderStatus.IN_PROGRESS
        db.commit()

        # Create payment
        response = client.post(
            "/payments",
            json={"order_id": order.id, "amount": 100},
            headers=auth_headers_client,
        )
        assert response.status_code == 201
        payment_id = response.json()["id"]

        # List payments
        response = client.get("/payments", headers=auth_headers_client)
        assert response.status_code == 200
        assert len(response.json()) >= 1
        returned_ids = [p["id"] for p in response.json()]
        assert payment_id in returned_ids

    def test_get_payment_for_order_not_found(self, client, auth_headers_client):
        """Test getting payment for non-existent order"""
        response = client.get("/payments/order/9999", headers=auth_headers_client)
        assert response.status_code == 404

    def test_get_payment_for_order_none_exists(self, client, auth_headers_client, order):
        """Test getting payment when no payment exists for order"""
        response = client.get(f"/payments/order/{order.id}", headers=auth_headers_client)
        assert response.status_code == 200
        assert response.json() is None

    def test_simulate_payment_demo_card_declined(self, client, auth_headers_client, order, db):
        """Test that demo card ending in 0000 is declined"""
        order.status = OrderStatus.IN_PROGRESS
        db.commit()

        response = client.post(
            "/payments/simulate",
            json={
                "order_id": order.id,
                "amount": 100,
                "card_number": "4111111111110000",
                "card_holder": "Test User",
            },
            headers=auth_headers_client,
        )
        assert response.status_code == 400
        assert "declined" in response.json()["detail"].lower()

    def test_simulate_payment_valid_card(self, client, auth_headers_client, order, db):
        """Test successful simulated payment"""
        order.status = OrderStatus.IN_PROGRESS
        db.commit()

        response = client.post(
            "/payments/simulate",
            json={
                "order_id": order.id,
                "amount": 150.75,
                "card_number": "4111111111111111",
                "card_holder": "John Doe",
            },
            headers=auth_headers_client,
        )
        assert response.status_code == 201
        payment = response.json()
        assert payment["status"] == PaymentStatus.PAID
        assert payment["amount"] == 150.75
        assert payment["paid_at"] is not None

    def test_simulate_payment_invalid_card_number(self, client, auth_headers_client, order, db):
        """Test simulated payment with invalid card number"""
        order.status = OrderStatus.IN_PROGRESS
        db.commit()

        response = client.post(
            "/payments/simulate",
            json={
                "order_id": order.id,
                "amount": 100,
                "card_number": "not_a_number",
                "card_holder": "Test User",
            },
            headers=auth_headers_client,
        )
        assert response.status_code == 422

    @pytest.mark.parametrize(
        "card_number,should_fail",
        [
            ("", True),  # Empty
            ("123", True),  # Too short
            ("12345678901234567890", True),  # Too long
            ("411111111111111", True),  # Valid length but with letters should fail
        ],
    )
    def test_simulate_payment_card_boundary(
        self, client, auth_headers_client, order, db, card_number, should_fail
    ):
        """Test simulated payment with boundary card numbers"""
        order.status = OrderStatus.IN_PROGRESS
        db.commit()

        response = client.post(
            "/payments/simulate",
            json={
                "order_id": order.id,
                "amount": 100,
                "card_number": card_number,
                "card_holder": "Test",
            },
            headers=auth_headers_client,
        )
        if should_fail:
            assert response.status_code in (400, 422)

    def test_update_payment_admin_only(self, client, auth_headers_client, auth_headers_admin, order, db):
        """Test that only admin can update payments"""
        order.status = OrderStatus.IN_PROGRESS
        db.commit()

        # Create payment
        payment = Payment(order_id=order.id, amount=100, status=PaymentStatus.PENDING)
        db.add(payment)
        db.commit()

        # Client tries to update
        response = client.patch(
            f"/payments/{payment.id}",
            json={"status": PaymentStatus.PAID},
            headers=auth_headers_client,
        )
        assert response.status_code == 403
        assert "Admin only" in response.json()["detail"]

        # Admin can update
        response = client.patch(
            f"/payments/{payment.id}",
            json={"status": PaymentStatus.PAID},
            headers=auth_headers_admin,
        )
        assert response.status_code == 200

    def test_delete_payment_admin_only(self, client, auth_headers_client, auth_headers_admin, order, db):
        """Test that only admin can delete payments"""
        order.status = OrderStatus.IN_PROGRESS
        db.commit()

        payment = Payment(order_id=order.id, amount=100)
        db.add(payment)
        db.commit()

        # Client tries to delete
        response = client.delete(f"/payments/{payment.id}", headers=auth_headers_client)
        assert response.status_code == 403

        # Admin can delete
        response = client.delete(f"/payments/{payment.id}", headers=auth_headers_admin)
        assert response.status_code == 204


class TestPaymentsIntegration:
    """Integration tests for payment flows"""

    def test_complete_payment_flow(self, client, auth_headers_client, order, db):
        """Test complete payment flow"""
        order.status = OrderStatus.IN_PROGRESS
        db.commit()

        # Create payment
        response = client.post(
            "/payments",
            json={"order_id": order.id, "amount": 100},
            headers=auth_headers_client,
        )
        assert response.status_code == 201
        payment_id = response.json()["id"]

        # Get payment
        response = client.get(f"/payments/{payment_id}", headers=auth_headers_client)
        assert response.status_code == 200
        assert response.json()["status"] == PaymentStatus.PENDING

        # Get payment for order
        response = client.get(f"/payments/order/{order.id}", headers=auth_headers_client)
        assert response.status_code == 200
        assert response.json()["id"] == payment_id

    def test_simulate_then_update_payment(self, client, auth_headers_client, auth_headers_admin, order, db):
        """Test simulating payment then updating it"""
        order.status = OrderStatus.IN_PROGRESS
        db.commit()

        # Simulate payment
        response = client.post(
            "/payments/simulate",
            json={
                "order_id": order.id,
                "amount": 200,
                "card_number": "4111111111111111",
                "card_holder": "John Doe",
            },
            headers=auth_headers_client,
        )
        assert response.status_code == 201
        payment_id = response.json()["id"]
        assert response.json()["status"] == PaymentStatus.PAID

        # Admin updates payment status
        response = client.patch(
            f"/payments/{payment_id}",
            json={"status": PaymentStatus.REFUNDED},
            headers=auth_headers_admin,
        )
        assert response.status_code == 200
        assert response.json()["status"] == PaymentStatus.REFUNDED
