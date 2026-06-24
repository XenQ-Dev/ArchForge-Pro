"""Settings Page."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QDoubleSpinBox, QLineEdit,
    QComboBox, QMessageBox, QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt

from app.models.settings_model import get_all_settings, set_setting


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(20)

        hdr = QLabel("Settings")
        hdr.setObjectName("section_title")
        sub = QLabel("Configure application-wide defaults")
        sub.setObjectName("section_subtitle")
        lay.addWidget(hdr)
        lay.addWidget(sub)

        # ── Company Info ────────────────────────────────────────────────────
        comp_group = QGroupBox("Company Information")
        comp_form = QFormLayout(comp_group)

        self._company_name = QLineEdit()
        self._company_addr = QLineEdit()
        self._company_phone = QLineEdit()
        self._company_email = QLineEdit()
        comp_form.addRow("Company Name:", self._company_name)
        comp_form.addRow("Address:", self._company_addr)
        comp_form.addRow("Phone:", self._company_phone)
        comp_form.addRow("Email:", self._company_email)
        lay.addWidget(comp_group)

        # ── Cost Parameters ─────────────────────────────────────────────────
        cost_group = QGroupBox("Default Cost Parameters")
        cost_form = QFormLayout(cost_group)

        self._gst_spin = QDoubleSpinBox()
        self._gst_spin.setRange(0, 28)
        self._gst_spin.setSuffix(" %")
        cost_form.addRow("GST Rate:", self._gst_spin)

        self._labour_spin = QDoubleSpinBox()
        self._labour_spin.setRange(5, 60)
        self._labour_spin.setSuffix(" %")
        cost_form.addRow("Labour Cost %:", self._labour_spin)

        self._equipment_spin = QDoubleSpinBox()
        self._equipment_spin.setRange(1, 20)
        self._equipment_spin.setSuffix(" %")
        cost_form.addRow("Equipment Cost %:", self._equipment_spin)

        self._margin_spin = QDoubleSpinBox()
        self._margin_spin.setRange(0, 30)
        self._margin_spin.setSuffix(" %")
        cost_form.addRow("Contractor Margin %:", self._margin_spin)

        lay.addWidget(cost_group)

        # ── Appearance ──────────────────────────────────────────────────────
        app_group = QGroupBox("Appearance")
        app_form = QFormLayout(app_group)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["dark", "light"])
        app_form.addRow("Theme:", self._theme_combo)

        self._currency_combo = QComboBox()
        self._currency_combo.addItems(["INR"])
        app_form.addRow("Currency:", self._currency_combo)

        lay.addWidget(app_group)

        # ── Email / SMTP (verification codes) ───────────────────────────────
        smtp_group = QGroupBox("Email / SMTP  —  sends verification codes")
        smtp_form = QFormLayout(smtp_group)

        self._smtp_host = QLineEdit()
        self._smtp_port = QLineEdit()
        self._smtp_user = QLineEdit()
        self._smtp_user.setPlaceholderText("your-account@gmail.com")
        self._smtp_pass = QLineEdit()
        self._smtp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self._smtp_pass.setPlaceholderText("16-char Gmail App Password")
        smtp_form.addRow("SMTP Host:", self._smtp_host)
        smtp_form.addRow("SMTP Port:", self._smtp_port)
        smtp_form.addRow("Gmail Address:", self._smtp_user)
        smtp_form.addRow("App Password:", self._smtp_pass)

        help_lbl = QLabel(
            "Gmail requires an App Password (not your normal password):\n"
            "1. Enable 2-Step Verification on your Google account\n"
            "2. Visit  myaccount.google.com/apppasswords\n"
            "3. Create a password for \"Mail\" and paste the 16 characters above\n"
            "Leave blank to run in dev mode (codes shown on-screen instead of emailed)."
        )
        help_lbl.setObjectName("section_subtitle")
        help_lbl.setWordWrap(True)
        smtp_form.addRow("", help_lbl)

        test_btn = QPushButton("Send Test Email")
        test_btn.setObjectName("btn_secondary")
        test_btn.clicked.connect(self._send_test_email)
        smtp_form.addRow("", test_btn)

        lay.addWidget(smtp_group)

        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self._save)
        lay.addWidget(save_btn)
        lay.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._load_settings()

    def refresh(self) -> None:
        self._load_settings()

    def _load_settings(self) -> None:
        s = get_all_settings()
        self._company_name.setText(s.get("company_name", ""))
        self._company_addr.setText(s.get("company_address", ""))
        self._company_phone.setText(s.get("company_phone", ""))
        self._company_email.setText(s.get("company_email", ""))
        self._gst_spin.setValue(float(s.get("gst_pct", 18.0)))
        self._labour_spin.setValue(float(s.get("labour_pct", 25.0)))
        self._equipment_spin.setValue(float(s.get("equipment_pct", 5.0)))
        self._margin_spin.setValue(float(s.get("contractor_pct", 10.0)))
        theme = s.get("theme", "dark")
        idx = self._theme_combo.findText(theme)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)
        self._smtp_host.setText(s.get("smtp_host", "smtp.gmail.com"))
        self._smtp_port.setText(s.get("smtp_port", "587"))
        self._smtp_user.setText(s.get("smtp_user", ""))
        self._smtp_pass.setText(s.get("smtp_pass", ""))

    def _save(self) -> None:
        set_setting("company_name", self._company_name.text())
        set_setting("company_address", self._company_addr.text())
        set_setting("company_phone", self._company_phone.text())
        set_setting("company_email", self._company_email.text())
        set_setting("gst_pct", str(self._gst_spin.value()))
        set_setting("labour_pct", str(self._labour_spin.value()))
        set_setting("equipment_pct", str(self._equipment_spin.value()))
        set_setting("contractor_pct", str(self._margin_spin.value()))
        set_setting("theme", self._theme_combo.currentText())
        set_setting("smtp_host", self._smtp_host.text().strip())
        set_setting("smtp_port", self._smtp_port.text().strip() or "587")
        set_setting("smtp_user", self._smtp_user.text().strip())
        set_setting("smtp_pass", self._smtp_pass.text().replace(" ", "").strip())
        QMessageBox.information(self, "Saved", "Settings saved successfully!")

    def _send_test_email(self) -> None:
        host = self._smtp_host.text().strip() or "smtp.gmail.com"
        port = self._smtp_port.text().strip() or "587"
        user = self._smtp_user.text().strip()
        pwd  = self._smtp_pass.text().strip()
        if not user or not pwd:
            QMessageBox.warning(self, "Missing Details",
                                "Enter your Gmail address and App Password first.")
            return
        from app.utils.email_sender import send_test
        QMessageBox.information(self, "Sending", f"Sending a test email to {user} …")
        ok, err = send_test(host, port, user, pwd, user)
        if ok:
            # Auto-save working credentials so registration emails work immediately
            set_setting("smtp_host", host)
            set_setting("smtp_port", port)
            set_setting("smtp_user", user)
            set_setting("smtp_pass", pwd.replace(" ", ""))
            QMessageBox.information(
                self, "Success",
                f"Test email sent to {user} and settings saved automatically.\n\n"
                "New-user verification codes will now be emailed via this account."
            )
        else:
            QMessageBox.critical(
                self, "Failed",
                f"Could not send email:\n\n{err}\n\n"
                "Common causes:\n"
                "• Using your normal password instead of an App Password\n"
                "• 2-Step Verification not enabled on your Google account\n"
                "• Typo in the email or App Password"
            )
