"""ML Prediction Page — predict cost & duration using trained models."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDoubleSpinBox, QSpinBox, QComboBox, QGroupBox,
    QFormLayout, QFrame, QTextEdit, QSizePolicy,
)
from PyQt6.QtCore import Qt


class MLPredictionPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        hdr = QLabel("ML Cost & Duration Prediction")
        hdr.setObjectName("section_title")
        sub = QLabel("Random Forest / XGBoost model trained on 10,000+ Indian construction projects")
        sub.setObjectName("section_subtitle")
        outer.addWidget(hdr)
        outer.addWidget(sub)

        main_row = QHBoxLayout()
        main_row.setSpacing(16)

        # ── Inputs ──────────────────────────────────────────────────────────
        input_group = QGroupBox("Project Inputs")
        input_group.setMaximumWidth(340)
        form = QFormLayout(input_group)

        self._plot_area = QDoubleSpinBox()
        self._plot_area.setRange(100, 500000)
        self._plot_area.setValue(2000)
        self._plot_area.setSuffix(" sq.ft")
        self._plot_area.setSingleStep(100)
        form.addRow("Plot Area:", self._plot_area)

        self._bua = QDoubleSpinBox()
        self._bua.setRange(100, 400000)
        self._bua.setValue(1500)
        self._bua.setSuffix(" sq.ft")
        self._bua.setSingleStep(100)
        form.addRow("Built-up Area:", self._bua)

        self._floors = QSpinBox()
        self._floors.setRange(1, 50)
        self._floors.setValue(2)
        form.addRow("Number of Floors:", self._floors)

        self._proj_type = QComboBox()
        self._proj_type.addItems(["Residential", "Commercial", "Industrial"])
        form.addRow("Project Type:", self._proj_type)

        self._quality = QComboBox()
        self._quality.addItems(["Standard", "Premium", "Luxury"])
        form.addRow("Construction Quality:", self._quality)

        predict_btn = QPushButton("Predict Cost & Duration")
        predict_btn.clicked.connect(self._predict)
        input_group.layout().addRow(predict_btn)

        train_btn = QPushButton("Train / Retrain Models")
        train_btn.setObjectName("btn_secondary")
        train_btn.clicked.connect(self._train_models)
        input_group.layout().addRow(train_btn)

        main_row.addWidget(input_group)

        # ── Results ─────────────────────────────────────────────────────────
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(12)

        # Prediction cards
        self._cards_row = QHBoxLayout()
        self._cards_row.setSpacing(12)
        right_lay.addLayout(self._cards_row)

        # Model metrics
        metrics_group = QGroupBox("Model Performance Metrics")
        metrics_lay = QVBoxLayout(metrics_group)
        self._metrics_text = QTextEdit()
        self._metrics_text.setReadOnly(True)
        self._metrics_text.setMaximumHeight(160)
        self._metrics_text.setPlaceholderText("Train the model to see performance metrics…")
        metrics_lay.addWidget(self._metrics_text)
        right_lay.addWidget(metrics_group)

        # Log
        log_group = QGroupBox("Training Log")
        log_lay = QVBoxLayout(log_group)
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setPlaceholderText("Training log will appear here…")
        log_lay.addWidget(self._log_text)
        right_lay.addWidget(log_group, stretch=1)

        main_row.addWidget(right, stretch=1)
        outer.addLayout(main_row, stretch=1)

        # Try to load metrics from previously trained model
        self._try_load_metrics()

    def refresh(self) -> None:
        self._try_load_metrics()

    def _predict(self) -> None:
        from app.ml.predictor import MLPredictor
        predictor = MLPredictor()
        if not predictor.models_exist():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Models",
                                "Models not trained yet. Click 'Train / Retrain Models' first.")
            return

        result = predictor.predict(
            plot_area=self._plot_area.value(),
            built_up_area=self._bua.value(),
            num_floors=self._floors.value(),
            project_type=self._proj_type.currentText(),
            quality=self._quality.currentText(),
        )

        # Clear cards
        while self._cards_row.count():
            item = self._cards_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        from app.utils.formatters import fmt_inr
        cards = [
            ("Predicted Cost (RF)",     fmt_inr(result["rf_cost"]),      "#f0a500"),
            ("Predicted Cost (XGB)",    fmt_inr(result["xgb_cost"]),     "#4a9eff"),
            ("Predicted Duration (RF)", f"{result['rf_days']:.0f} days", "#27ae60"),
            ("Predicted Duration (XGB)",f"{result['xgb_days']:.0f} days","#8b5cf6"),
        ]
        for label, val, color in cards:
            card = _PredCard(label, val, color)
            self._cards_row.addWidget(card)
        self._cards_row.addStretch()

    def _train_models(self) -> None:
        self._log_text.clear()
        self._log_text.append("Generating synthetic dataset of 10,000 Indian construction projects…")

        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            from app.ml.trainer import ModelTrainer
            trainer = ModelTrainer()

            def log(msg: str):
                self._log_text.append(msg)
                QApplication.processEvents()

            metrics = trainer.train(log_callback=log)
            self._display_metrics(metrics)
            self._log_text.append("\n✔  Training complete! Models saved to ml_models/")
        except Exception as exc:
            self._log_text.append(f"\n✘  Error: {exc}")

    def _try_load_metrics(self) -> None:
        try:
            from app.ml.predictor import MLPredictor
            predictor = MLPredictor()
            if predictor.models_exist():
                metrics = predictor.load_metrics()
                if metrics:
                    self._display_metrics(metrics)
        except Exception:
            pass

    def _display_metrics(self, metrics: dict) -> None:
        lines = ["Model Performance Metrics\n" + "─" * 40]
        for model_name, m in metrics.items():
            lines.append(f"\n{model_name}:")
            lines.append(f"  Cost MAE  : ₹{m.get('cost_mae', 0):,.0f}")
            lines.append(f"  Cost RMSE : ₹{m.get('cost_rmse', 0):,.0f}")
            lines.append(f"  Cost R²   : {m.get('cost_r2', 0):.4f}")
            lines.append(f"  Days MAE  : {m.get('days_mae', 0):.1f}")
            lines.append(f"  Days RMSE : {m.get('days_rmse', 0):.1f}")
            lines.append(f"  Days R²   : {m.get('days_r2', 0):.4f}")
        self._metrics_text.setPlainText("\n".join(lines))


class _PredCard(QFrame):
    def __init__(self, label: str, value: str, color: str):
        super().__init__()
        self.setObjectName("stat_card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(4)
        v = QLabel(value)
        v.setStyleSheet(f"color:{color}; font-weight:700; font-size:16px;")
        v.setWordWrap(True)
        l = QLabel(label)
        l.setObjectName("stat_label")
        l.setStyleSheet("font-size:10px;")
        l.setWordWrap(True)
        lay.addWidget(v)
        lay.addWidget(l)
