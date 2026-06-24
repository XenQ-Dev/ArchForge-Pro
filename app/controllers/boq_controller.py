"""BOQ Controller — convert estimate items into formatted BOQ rows."""
from __future__ import annotations


class BOQController:
    def generate_from_estimate(self, estimate: dict) -> list[dict]:
        items = estimate.get("items", [])
        boq_rows = []
        item_no = 1

        for item in items:
            boq_rows.append({
                "item_no": item_no,
                "description": item["item_name"],
                "quantity": item["quantity"],
                "unit": item["unit"],
                "rate": item["rate"],
                "amount": item["amount"],
            })
            item_no += 1

        # Labour summary row
        boq_rows.append({
            "item_no": item_no,
            "description": "Labour Charges (Skilled + Unskilled)",
            "quantity": 1,
            "unit": "LS",
            "rate": estimate["labour_cost"],
            "amount": estimate["labour_cost"],
        })
        item_no += 1

        # Equipment row
        boq_rows.append({
            "item_no": item_no,
            "description": "Equipment & Machinery Hire",
            "quantity": 1,
            "unit": "LS",
            "rate": estimate["equipment_cost"],
            "amount": estimate["equipment_cost"],
        })
        item_no += 1

        # Contractor margin row
        boq_rows.append({
            "item_no": item_no,
            "description": "Contractor's Overhead & Profit",
            "quantity": 1,
            "unit": "LS",
            "rate": estimate["contractor_margin"],
            "amount": estimate["contractor_margin"],
        })
        item_no += 1

        # GST row
        boq_rows.append({
            "item_no": item_no,
            "description": f"GST ({estimate.get('gst_pct', 18):.0f}%)",
            "quantity": 1,
            "unit": "LS",
            "rate": estimate["gst_amount"],
            "amount": estimate["gst_amount"],
        })

        return boq_rows
