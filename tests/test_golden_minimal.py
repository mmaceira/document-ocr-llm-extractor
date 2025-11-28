from document_llm_extractor.deliverynote.models import DeliveryNoteReport


def test_schema_roundtrip():
    # sanity: the schema compiles and accepts a tiny minimal object
    data = {
        "numero_deliverynote": "A-001",
        "fecha_deliverynote": "2025-01-10",
        "nombre_empresa": "ACME SA",
        "nif_cif": "B12345678",
        "productos": [
            {
                "producto": "Caja",
                "cantidad": 1,
                "precio_unitario": 10.0,
                "importe_linea": 10.0,
            }
        ],
        "base_imponible": 10.0,
        "importe_impuestos": 2.1,
        "importe_retencion": 0.0,
        "total_deliverynote": 12.1,
    }
    obj = DeliveryNoteReport.model_validate(data)
    assert obj.total_deliverynote >= obj.base_imponible
