"""
Automated Integration and Acceptance Tests for Event Ticketing RESTful Web API.
Verifies all CRUD endpoints, RBAC, External APIs (QR & PDF), and Error Responses.
Course: SWC3633 / SWC4443 Web API Development
"""
import sys
import os
import unittest
from fastapi.testclient import TestClient

# Ensure root directory is on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.main import app
from backend.database import get_db_connection

client = TestClient(app)

class TestEventTicketingAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 1. Log in Admin
        admin_res = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "password123"})
        assert admin_res.status_code == 200, f"Admin login failed: {admin_res.text}"
        cls.admin_token = admin_res.json()["data"]["access_token"]
        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}
        cls.admin_api_key = admin_res.json()["data"]["user"]["api_key"]

        # 2. Log in Organiser
        org_res = client.post("/api/auth/login", json={"email": "aina@example.com", "password": "password123"})
        assert org_res.status_code == 200, f"Organiser login failed: {org_res.text}"
        cls.org_token = org_res.json()["data"]["access_token"]
        cls.org_headers = {"Authorization": f"Bearer {cls.org_token}"}

        # 3. Log in Customer
        cust_res = client.post("/api/auth/login", json={"email": "sarah@example.com", "password": "password123"})
        assert cust_res.status_code == 200, f"Customer login failed: {cust_res.text}"
        cls.cust_token = cust_res.json()["data"]["access_token"]
        cls.cust_headers = {"Authorization": f"Bearer {cls.cust_token}"}

    def test_01_api_health(self):
        """Test GET /api/stats/health returns online status and external services health."""
        res = client.get("/api/stats/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["database"]["status"], "connected")
        print("[PASS] test_01_api_health")

    def test_02_auth_me_with_bearer_token(self):
        """Test GET /api/auth/me returns current user info via JWT."""
        res = client.get("/api/auth/me", headers=self.cust_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertEqual(data["email"], "sarah@example.com")
        self.assertEqual(data["role"], "customer")
        print("[PASS] test_02_auth_me_with_bearer_token")

    def test_03_auth_me_with_api_key(self):
        """Test GET /api/auth/me returns user via X-API-Key header."""
        res = client.get("/api/auth/me", headers={"X-API-Key": self.admin_api_key})
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertEqual(data["email"], "admin@example.com")
        self.assertEqual(data["role"], "admin")
        print("[PASS] test_03_auth_me_with_api_key")

    def test_04_list_events_with_filter_and_search(self):
        """Test GET /api/events with search keyword and pagination."""
        res = client.get("/api/events?search=Music&limit=5")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(len(data["data"]), 1)
        print("[PASS] test_04_list_events_with_filter_and_search")

    def test_05_list_venues(self):
        """Test GET /api/venues returns list of venues."""
        res = client.get("/api/venues?limit=5")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data["data"]), 1)
        print("[PASS] test_05_list_venues")

    def test_06_customer_booking_workflow(self):
        """Test complete booking flow: create booking, check QR code, check PDF ticket."""
        # 1. Create booking for Event 1
        payload = {
            "event_id": 1,
            "quantity": 1,
            "payment_method": "card"
        }
        res = client.post("/api/bookings", json=payload, headers=self.cust_headers)
        self.assertEqual(res.status_code, 201)
        booking = res.json()["data"]
        booking_id = booking["booking_id"]
        ticket_code = booking["ticket_code"]
        self.assertIsNotNone(ticket_code)

        # 2. Get QR Code for booking (External QR API)
        qr_res = client.get(f"/api/bookings/{booking_id}/qrcode?format=image", headers=self.cust_headers)
        self.assertEqual(qr_res.status_code, 200)
        self.assertEqual(qr_res.headers["content-type"], "image/png")
        self.assertGreater(len(qr_res.content), 100)

        # 3. Download PDF Ticket (PDF Generation API)
        pdf_res = client.get(f"/api/bookings/{booking_id}/pdf", headers=self.cust_headers)
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.headers["content-type"], "application/pdf")
        self.assertTrue(pdf_res.content.startswith(b"%PDF"))

        # 4. Gate verification endpoint
        verify_res = client.post("/api/bookings/verify-ticket", json={"ticket_code": ticket_code}, headers=self.admin_headers)
        self.assertEqual(verify_res.status_code, 200)
        self.assertTrue(verify_res.json()["valid"])

        # 5. Cancel booking with cancellation reason
        cancel_res = client.put(
            f"/api/bookings/{booking_id}/cancel", 
            json={"cancellation_reason": "Schedule conflict - Unable to attend"},
            headers=self.cust_headers
        )
        self.assertEqual(cancel_res.status_code, 200)
        self.assertIn("cancelled", cancel_res.json()["data"]["booking_status"])
        self.assertEqual(cancel_res.json()["data"]["cancellation_reason"], "Schedule conflict - Unable to attend")

        # 6. Verify cancelled ticket blocks QR generation and PDF download
        cancelled_qr = client.get(f"/api/bookings/{booking_id}/qrcode?format=image", headers=self.cust_headers)
        self.assertEqual(cancelled_qr.status_code, 400)

        cancelled_pdf = client.get(f"/api/bookings/{booking_id}/pdf", headers=self.cust_headers)
        self.assertEqual(cancelled_pdf.status_code, 400)

        # 7. Clean up test booking and payment from database so test runs never pollute user accounts
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM payments WHERE booking_id = %s", (booking_id,))
        cursor.execute("DELETE FROM bookings WHERE booking_id = %s", (booking_id,))
        conn.commit()
        conn.close()

        print("[PASS] test_06_customer_booking_workflow (Booking + External QR + PDF + Verification + Cancellation + Void Enforcement + Auto-Cleanup)")

    def test_07_rbac_admin_only_endpoints(self):
        """Test RBAC: Customer trying to access Admin-only /api/users receives HTTP 403."""
        res = client.get("/api/users", headers=self.cust_headers)
        self.assertEqual(res.status_code, 403)

        # Admin can access
        admin_res = client.get("/api/users", headers=self.admin_headers)
        self.assertEqual(admin_res.status_code, 200)
        print("[PASS] test_07_rbac_admin_only_endpoints")

    def test_08_root_endpoints_compatibility(self):
        """Test root resource endpoints (/events, /venues, /bookings) as requested by project specification."""
        e_res = client.get("/events?limit=2")
        self.assertEqual(e_res.status_code, 200)

        v_res = client.get("/venues?limit=2")
        self.assertEqual(v_res.status_code, 200)
        print("[PASS] test_08_root_endpoints_compatibility (/events, /venues)")

    def test_09_external_api_telemetry_logs(self):
        """Test GET /api/stats/external-apis returns external API audit trail."""
        res = client.get("/api/stats/external-apis", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        logs = res.json()["data"]
        self.assertGreater(len(logs), 0)
        print(f"[PASS] test_09_external_api_telemetry_logs (Total logged calls: {len(logs)})")

    def test_10_user_logins_tracking_and_admin_audit(self):
        """Test GET /api/users/logins and dashboard signed_in_today metric."""
        # 1. Customer cannot access logins audit trail (RBAC HTTP 403)
        cust_res = client.get("/api/users/logins", headers=self.cust_headers)
        self.assertEqual(cust_res.status_code, 403)

        # 2. Admin can access logins audit trail
        admin_res = client.get("/api/users/logins?limit=10", headers=self.admin_headers)
        self.assertEqual(admin_res.status_code, 200)
        data = admin_res.json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(len(data["data"]), 1)
        first_login = data["data"][0]
        self.assertIn("user_id", first_login)
        self.assertIn("login_time", first_login)
        self.assertIn("email", first_login)
        self.assertIn("minutes_ago", first_login)

        # 3. Check dashboard stats signed_in_today
        stats_res = client.get("/api/stats/dashboard", headers=self.admin_headers)
        self.assertEqual(stats_res.status_code, 200)
        metrics = stats_res.json()["metrics"]
        self.assertIn("signed_in_today", metrics)
        self.assertGreaterEqual(metrics["signed_in_today"], 1)
        print(f"[PASS] test_10_user_logins_tracking_and_admin_audit (Active sign-ins today: {metrics['signed_in_today']})")

    def test_11_admin_update_and_delete_booking(self):
        """Test Admin updating booking status, payment status, and deleting booking record."""
        # 1. Create a temporary booking
        book_res = client.post("/api/bookings", json={"event_id": 2, "quantity": 1, "payment_method": "card"}, headers=self.cust_headers)
        self.assertEqual(book_res.status_code, 201)
        temp_booking_id = book_res.json()["data"]["booking_id"]
        ticket_code = book_res.json()["data"]["ticket_code"]

        # 2. Customer cannot update booking status via PUT /api/bookings/{id} (RBAC 403)
        forbidden_res = client.put(
            f"/api/bookings/{temp_booking_id}",
            json={"booking_status": "cancelled", "payment_status": "refunded"},
            headers=self.cust_headers
        )
        self.assertEqual(forbidden_res.status_code, 403)

        # 3. Admin updates booking status and payment status
        update_res = client.put(
            f"/api/bookings/{temp_booking_id}",
            json={"booking_status": "cancelled", "payment_status": "refunded", "cancellation_reason": "Admin test cancellation"},
            headers=self.admin_headers
        )
        self.assertEqual(update_res.status_code, 200)
        updated_data = update_res.json()["data"]
        self.assertEqual(updated_data["booking_status"], "cancelled")
        self.assertEqual(updated_data["payment_status"], "refunded")
        self.assertEqual(updated_data["cancellation_reason"], "Admin test cancellation")

        # 4. Admin reactivates booking back to confirmed
        reactivate_res = client.put(
            f"/api/bookings/{temp_booking_id}",
            json={"booking_status": "confirmed", "payment_status": "paid"},
            headers=self.admin_headers
        )
        self.assertEqual(reactivate_res.status_code, 200)
        self.assertEqual(reactivate_res.json()["data"]["booking_status"], "confirmed")

        # 5. Customer cannot delete booking (RBAC 403)
        del_cust = client.delete(f"/api/bookings/{temp_booking_id}", headers=self.cust_headers)
        self.assertEqual(del_cust.status_code, 403)

        # 6. Admin deletes booking
        del_admin = client.delete(f"/api/bookings/{temp_booking_id}", headers=self.admin_headers)
        self.assertEqual(del_admin.status_code, 200)

        # 7. Verification that booking is gone
        verify_gone = client.get(f"/api/bookings/{temp_booking_id}", headers=self.admin_headers)
        self.assertEqual(verify_gone.status_code, 404)
        print(f"[PASS] test_11_admin_update_and_delete_booking (Ticket: {ticket_code})")

if __name__ == "__main__":
    unittest.main()
