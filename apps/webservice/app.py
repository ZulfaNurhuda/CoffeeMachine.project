from typing import Optional

import os
import logging

from flask import Flask, render_template, request, redirect, url_for

from apps.database.manajer_database import ManajerDatabase

from apps.data_classes import DataRefID

class AplikasiWeb:
    def __init__(self, manajer_db: ManajerDatabase):
        """
        Inisialisasi AplikasiWeb.

        Args:
            manajer_db (ManajerDatabase): Objek ManajerDatabase untuk berinteraksi dengan database.
        """
        self.manajer_db = manajer_db

        self.app = Flask(
            __name__, template_folder=os.path.join(os.getcwd(), "templates")
        )
        logger = self.app.logger
        logger.disabled = True
        log = logging.getLogger("werkzeug")
        log.disabled = True

        # Setup routes
        self.setup_routes()

    def setup_routes(self):
        """
        Mengatur routing untuk aplikasi web.
        """

        @self.app.route("/search")
        def cari():
            return render_template("loading.html")

        @self.app.route("/proses_cari")
        def proses_cari():
            ref_id = request.args.get("ref_id")
            data_pembayaran = self.ambil_data(self.manajer_db, ref_id)
            if data_pembayaran and data_pembayaran.status == "Pending":
                self.update_status(self.manajer_db, ref_id, "Selesai")
                return render_template(
                    "next_success.html",
                    ref_id=ref_id,
                    data={
                        "total_harga": data_pembayaran.total_harga,
                        "timestamp": data_pembayaran.timestamp,
                        "metode_pembayaran": data_pembayaran.metode_pembayaran,
                    },
                )
            else:
                return redirect(url_for("gagal"))

        @self.app.route("/berhasil")
        def berhasil():
            ref_id = request.args.get("ref_id")
            data_pembayaran = self.ambil_data(self.manajer_db, ref_id)
            if data_pembayaran and data_pembayaran.status == "Pending":
                self.update_status(self.manajer_db, ref_id, "Selesai")
                return render_template(
                    "next_success.html",
                    ref_id=ref_id,
                    data={
                        "total_harga": data_pembayaran.total_harga,
                        "timestamp": data_pembayaran.timestamp,
                        "metode_pembayaran": data_pembayaran.metode_pembayaran,
                    },
                )
            else:
                return redirect(url_for("gagal"))

        @self.app.route("/gagal")
        def gagal():
            return render_template("next_failed.html")

        # Handler untuk menangani page not found (404)
        @self.app.errorhandler(404)
        def halaman_tidak_ditemukan(e):
            return render_template("404.html"), 404

    def ambil_data(
        self, manajer_db: ManajerDatabase, ref_id: str
    ) -> Optional[DataRefID]:
        """
        Mengambil data pembayaran berdasarkan Reference ID dari cache.

        Args:
            manajer_db (ManajerDatabase): Objek ManajerDatabase untuk berinteraksi dengan database.
            ref_id (str): Reference ID dari pembayaran yang akan diambil datanya.

        Returns:
            Optional[DataRefID]: Objek DataRefID yang berisi data pembayaran, atau None jika tidak ditemukan.
        """
        with manajer_db.kunci:
            for data in manajer_db.daftar_qr:
                if data.ref_id == ref_id:
                    return data
        return None

    def update_status(
        self, manajer_db: ManajerDatabase, ref_id: str, status_baru: str
    ) -> bool:
        """
        Mengupdate status pembayaran di cache lokal dan enqueue ke database.

        Args:
            manajer_db (ManajerDatabase): Objek ManajerDatabase untuk berinteraksi dengan database.
            ref_id (str): Reference ID dari pembayaran yang akan diupdate statusnya.
            status_baru (str): Status baru untuk pembayaran.

        Returns:
            bool: True jika status berhasil diupdate, False jika tidak.
        """
        with manajer_db.kunci:
            for qr in manajer_db.daftar_qr:
                if qr.ref_id == ref_id:
                    qr.status = status_baru
                    manajer_db.enqueue_update_status_qr(ref_id, status_baru)
                    return True
        return False

    def run(self, host: str, port: int):
        """
        Menjalankan aplikasi web.

        Args:
            host (str): Host untuk menjalankan aplikasi web.
            port (int): Port untuk menjalankan aplikasi web.
        """

        # Registrasi Template Filter Untuk Convert Titik Ribuan
        @self.app.template_filter("rupiah")
        def format_rupiah(value):
            """Filter Jinja2 untuk format rupiah."""
            return f"{value:,.0f}".replace(",", ".")

        self.app.run(
            host=host, port=port, debug=False, threaded=True, use_reloader=False
        )
