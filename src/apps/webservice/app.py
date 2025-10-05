"""
This file defines the `WebApplication` class, a Flask-based web service that
handles the confirmation of QR code payments.

When a user pays via QRIS, the coffee machine generates a QR code containing a URL
pointing to this web service. When the user scans the QR code and opens the URL,
this application processes the request, validates the payment reference ID, and
updates the payment status in the Google Sheets database via the `DatabaseManager`.

Key components:
- A Flask application instance.
- Routes to handle the payment confirmation process (`/search`, `/process_search`, etc.).
- Interaction with the `DatabaseManager` to fetch and update payment data.
- Renders HTML templates to show the payment status (success, failure, loading).
"""

from typing import Optional
import os
import logging

from flask import Flask, render_template, request, redirect, url_for

from apps.database.database_manager import DatabaseManager
from apps.data_classes import QRCodeData

class WebApplication:
    """A web application for handling QR payment confirmations."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initializes the WebApplication.

        Args:
            db_manager (DatabaseManager): The DatabaseManager object to interact with the database.
        """
        self.db_manager = db_manager

        self.app = Flask(
            __name__, template_folder=os.path.join(os.getcwd(), "templates")
        )
        # Disable Flask's default logger and Werkzeug's logger to keep the console clean.
        logger = self.app.logger
        logger.disabled = True
        log = logging.getLogger("werkzeug")
        log.disabled = True

        # Set up the application routes.
        self.setup_routes()

    def setup_routes(self):
        """
        Sets up the routing for the web application.
        """

        @self.app.route("/search")
        def search():
            """Renders the loading page while the payment is being processed."""
            return render_template("loading.html")

        @self.app.route("/process_search")
        def process_search():
            """Processes the payment search and redirects to success or failure."""
            ref_id = request.args.get("ref_id")
            payment_data = self.get_data(self.db_manager, ref_id)
            if payment_data and payment_data.status == "Pending":
                self.update_status(self.db_manager, ref_id, "Selesai")
                return render_template(
                    "payment_success.html",
                    ref_id=ref_id,
                    data={
                        "total_harga": payment_data.total_harga,
                        "timestamp": payment_data.timestamp,
                        "metode_pembayaran": payment_data.metode_pembayaran,
                    },
                )
            else:
                return redirect(url_for("failure"))

        @self.app.route("/success")
        def success():
            """Displays the payment success page."""
            ref_id = request.args.get("ref_id")
            payment_data = self.get_data(self.db_manager, ref_id)
            if payment_data and payment_data.status == "Pending":
                self.update_status(self.db_manager, ref_id, "Selesai")
                return render_template(
                    "payment_success.html",
                    ref_id=ref_id,
                    data={
                        "total_harga": payment_data.total_harga,
                        "timestamp": payment_data.timestamp,
                        "metode_pembayaran": payment_data.metode_pembayaran,
                    },
                )
            else:
                return redirect(url_for("failure"))

        @self.app.route("/failure")
        def failure():
            """Displays the payment failure page."""
            return render_template("payment_failed.html")

        # Handler for page not found (404) errors.
        @self.app.errorhandler(404)
        def page_not_found(e):
            """Renders the custom 404 error page."""
            return render_template("404.html"), 404

    def get_data(
        self, db_manager: DatabaseManager, ref_id: str
    ) -> Optional[QRCodeData]:
        """
        Retrieves payment data based on the Reference ID from the cache.

        Args:
            db_manager (DatabaseManager): The DatabaseManager object.
            ref_id (str): The Reference ID of the payment to retrieve.

        Returns:
            Optional[QRCodeData]: A QRCodeData object containing payment data, or None if not found.
        """
        with db_manager.lock:
            for data in db_manager.qr_code_list:
                if data.ref_id == ref_id:
                    return data
        return None

    def update_status(
        self, db_manager: DatabaseManager, ref_id: str, new_status: str
    ) -> bool:
        """
        Updates the payment status in the local cache and enqueues it for the database.

        Args:
            db_manager (DatabaseManager): The DatabaseManager object.
            ref_id (str): The Reference ID of the payment to update.
            new_status (str): The new status for the payment.

        Returns:
            bool: True if the status was updated successfully, False otherwise.
        """
        with db_manager.lock:
            for qr in db_manager.qr_code_list:
                if qr.ref_id == ref_id:
                    qr.status = new_status
                    db_manager.enqueue_update_qr_status(ref_id, new_status)
                    return True
        return False

    def run(self, host: str, port: int):
        """
        Runs the Flask web application.

        Args:
            host (str): The host to run the web application on.
            port (int): The port to run the web application on.
        """

        # Register a template filter to format numbers as currency.
        @self.app.template_filter("rupiah")
        def format_rupiah(value):
            """Jinja2 filter for currency formatting."""
            return f"{value:,.0f}".replace(",", ".")

        self.app.run(
            host=host, port=port, debug=False, threaded=True, use_reloader=False
        )
