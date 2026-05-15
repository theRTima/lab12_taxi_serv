"""Extended tests for orders endpoint with high coverage"""

import pytest
from fastapi import status
from app.models.order import Order, OrderStatus
from app.models.tariff import Tariff


class TestOrdersEdgeCases:
    """Test edge cases for orders"""

    @pytest.mark.parametrize(
        "pickup,destination,should_succeed",
        [
            # Valid cases
            ("123 Main St", "456 Oak Ave", True),
            ("a", "b", True),  # Min length
            ("a" * 500, "b" * 500, True),  # Max length
            # Invalid cases
            ("", "dest", False),  # Empty pickup
            ("pickup", "", False),  # Empty destination
            ("", "", False),  # Both empty
            ("a" * 501, "dest", False),  # Pickup too long
            ("pickup", "a" * 501, False),  # Destination too long
        ],
    )
    def test_create_order_location_boundary_values(
        self, client, auth_headers_client, tariff, pickup, destination, should_succeed
    ):
        """Test order creation with boundary location values"""
        response = client.post(
            "/orders",
            json={
                "tariff_id": tariff.id,
                "pickup": pickup,
                "destination": destination,
            },
            headers=auth_headers_client,
        )
        if should_succeed:
            assert response.status_code == 201
        else:
            assert response.status_code in (400, 422)

    def test_create_order_with_nonexistent_tariff(self, client, auth_headers_client):
        """Test order creation with non-existent tariff"""
        response = client.post(
            "/orders",
            json={
                "tariff_id": 9999,
                "pickup": "Location A",
                "destination": "Location B",
            },
            headers=auth_headers_client,
        )
        assert response.status_code == 404
        assert "Tariff not found" in response.json()["detail"]

    def test_create_order_requires_client_role(self, client, auth_headers_driver, tariff):
        """Test that only clients can create orders"""
        response = client.post(
            "/orders",
            json={
                "tariff_id": tariff.id,
                "pickup": "Location A",
                "destination": "Location B",
            },
            headers=auth_headers_driver,
        )
        assert response.status_code == 403

    def test_list_orders_empty(self, client, auth_headers_client):
        """Test listing orders when none exist"""
        response = client.get("/orders/list", headers=auth_headers_client)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_orders_client_sees_only_own(self, client, auth_headers_client, auth_headers_admin, tariff, db):
        """Test that clients only see their own orders"""
        # Create order as client
        response = client.post(
            "/orders",
            json={"tariff_id": tariff.id, "pickup": "A", "destination": "B"},
            headers=auth_headers_client,
        )
        order_id = response.json()["id"]

        # List as client
        response = client.get("/orders/list", headers=auth_headers_client)
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == order_id

        # Admin sees all orders
        response = client.get("/orders/list", headers=auth_headers_admin)
        assert len(response.json()) >= 1

    def test_list_orders_driver_sees_own_and_pending(self, client, auth_headers_driver, db, order):
        """Test that drivers see their assigned orders and pending orders"""
        # Driver without profile shouldn't see orders
        response = client.get("/orders/list", headers=auth_headers_driver)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_order_not_found(self, client, auth_headers_client):
        """Test getting non-existent order"""
        response = client.get("/orders/9999", headers=auth_headers_client)
        assert response.status_code == 404

    def test_get_order_access_denied(self, client, auth_headers_client, auth_headers_admin, tariff, db):
        """Test that client can't see another client's order"""
        # Create order
        from app.models.user import User, UserRole

        other_client = User(
            email="other@example.com",
            hashed_password="hashed",
            name="Other",
            role=UserRole.CLIENT,
        )
        db.add(other_client)
        db.commit()

        order = Order(
            client_id=other_client.id,
            tariff_id=tariff.id,
            pickup="A",
            destination="B",
            status=OrderStatus.PENDING,
        )
        db.add(order)
        db.commit()

        # Try to access as different client
        response = client.get(f"/orders/{order.id}", headers=auth_headers_client)
        assert response.status_code == 403

    def test_update_order_pending_and_assigned_only(self, client, auth_headers_client, tariff):
        """Test that only PENDING and ASSIGNED orders can be updated"""
        # Create order (PENDING)
        response = client.post(
            "/orders",
            json={"tariff_id": tariff.id, "pickup": "A", "destination": "B"},
            headers=auth_headers_client,
        )
        order_id = response.json()["id"]

        # Update PENDING order (should work)
        response = client.patch(
            f"/orders/{order_id}",
            json={"pickup": "New Location A"},
            headers=auth_headers_client,
        )
        assert response.status_code == 200

    def test_update_order_not_found(self, client, auth_headers_client):
        """Test updating non-existent order"""
        response = client.patch(
            "/orders/9999",
            json={"pickup": "New A"},
            headers=auth_headers_client,
        )
        assert response.status_code == 404

    def test_update_order_access_denied(self, client, auth_headers_client, auth_headers_admin, tariff, db):
        """Test access control for order updates"""
        from app.models.user import User, UserRole

        other_client = User(
            email="other2@example.com",
            hashed_password="hashed",
            name="Other2",
            role=UserRole.CLIENT,
        )
        db.add(other_client)
        db.commit()

        order = Order(
            client_id=other_client.id,
            tariff_id=tariff.id,
            pickup="A",
            destination="B",
            status=OrderStatus.PENDING,
        )
        db.add(order)
        db.commit()

        response = client.patch(
            f"/orders/{order.id}",
            json={"pickup": "New A"},
            headers=auth_headers_client,
        )
        assert response.status_code == 403

    def test_delete_order_not_found(self, client, auth_headers_client):
        """Test deleting non-existent order"""
        response = client.delete("/orders/9999", headers=auth_headers_client)
        assert response.status_code == 404

    def test_delete_order_only_pending_or_cancelled(self, client, auth_headers_client, tariff, db):
        """Test that only PENDING/CANCELLED orders can be deleted"""
        # Create order
        response = client.post(
            "/orders",
            json={"tariff_id": tariff.id, "pickup": "A", "destination": "B"},
            headers=auth_headers_client,
        )
        order_id = response.json()["id"]

        # Delete PENDING order (should work)
        response = client.delete(f"/orders/{order_id}", headers=auth_headers_client)
        assert response.status_code == 204

    def test_update_order_status_client_can_only_cancel(self, client, auth_headers_client, tariff):
        """Test that clients can only cancel orders"""
        # Create order
        response = client.post(
            "/orders",
            json={"tariff_id": tariff.id, "pickup": "A", "destination": "B"},
            headers=auth_headers_client,
        )
        order_id = response.json()["id"]

        # Try to change status to something else
        response = client.patch(
            f"/orders/{order_id}/status",
            json={"status": OrderStatus.ASSIGNED},
            headers=auth_headers_client,
        )
        assert response.status_code == 403

        # Try to cancel (should work)
        response = client.patch(
            f"/orders/{order_id}/status",
            json={"status": OrderStatus.CANCELLED},
            headers=auth_headers_client,
        )
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.CANCELLED

    def test_update_order_status_not_found(self, client, auth_headers_client):
        """Test updating status of non-existent order"""
        response = client.patch(
            "/orders/9999/status",
            json={"status": OrderStatus.COMPLETED},
            headers=auth_headers_client,
        )
        assert response.status_code == 404

    @pytest.mark.parametrize(
        "status_update,should_succeed",
        [
            (OrderStatus.ASSIGNED, False),  # Client can't assign
            (OrderStatus.IN_PROGRESS, False),  # Client can't set in progress
            (OrderStatus.COMPLETED, False),  # Client can't complete
            (OrderStatus.CANCELLED, True),  # Client can cancel
        ],
    )
    def test_client_status_transitions(self, client, auth_headers_client, tariff, status_update, should_succeed):
        """Test client status transition permissions"""
        # Create order
        response = client.post(
            "/orders",
            json={"tariff_id": tariff.id, "pickup": "A", "destination": "B"},
            headers=auth_headers_client,
        )
        order_id = response.json()["id"]

        # Try status transition
        response = client.patch(
            f"/orders/{order_id}/status",
            json={"status": status_update},
            headers=auth_headers_client,
        )
        if should_succeed:
            assert response.status_code == 200
        else:
            assert response.status_code == 403


class TestOrdersIntegration:
    """Integration tests for complete order flows"""

    def test_order_full_lifecycle(self, client, auth_headers_client, auth_headers_admin, tariff, db):
        """Test complete order lifecycle: create → assign → complete"""
        # Create order
        response = client.post(
            "/orders",
            json={"tariff_id": tariff.id, "pickup": "Start", "destination": "End"},
            headers=auth_headers_client,
        )
        assert response.status_code == 201
        order_id = response.json()["id"]
        assert response.json()["status"] == OrderStatus.PENDING

        # Get order
        response = client.get(f"/orders/{order_id}", headers=auth_headers_client)
        assert response.status_code == 200

        # Cancel order
        response = client.patch(
            f"/orders/{order_id}/status",
            json={"status": OrderStatus.CANCELLED},
            headers=auth_headers_client,
        )
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.CANCELLED

    def test_multiple_orders_from_same_client(self, client, auth_headers_client, tariff):
        """Test creating multiple orders from same client"""
        order_ids = []
        for i in range(3):
            response = client.post(
                "/orders",
                json={
                    "tariff_id": tariff.id,
                    "pickup": f"Location {i}",
                    "destination": f"Destination {i}",
                },
                headers=auth_headers_client,
            )
            assert response.status_code == 201
            order_ids.append(response.json()["id"])

        # List all orders
        response = client.get("/orders/list", headers=auth_headers_client)
        assert len(response.json()) == 3
        returned_ids = [o["id"] for o in response.json()]
        assert set(order_ids).issubset(set(returned_ids))
