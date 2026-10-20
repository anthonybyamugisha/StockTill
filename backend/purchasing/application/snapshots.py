from purchasing.domain.entities import Supplier


def supplier_contact_snapshot(supplier: Supplier) -> dict[str, str]:
    return {
        "name": supplier.name,
        "contact_name": supplier.contact_name,
        "email": supplier.email,
        "phone": supplier.phone,
        "address": supplier.address,
    }
