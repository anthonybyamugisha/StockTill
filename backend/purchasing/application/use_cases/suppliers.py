from uuid import UUID

from purchasing.application.commands import CreateSupplierCommand, UpdateSupplierCommand
from purchasing.application.snapshots import supplier_contact_snapshot
from purchasing.domain.entities import Supplier
from purchasing.domain.errors import SupplierNotFoundError
from purchasing.domain.repository import SupplierRepository
from shared.application.audit import AuditPort, NullAuditPort
from shared.domain.clock import Clock


class CreateSupplierUseCase:
    def __init__(
        self, supplier_repository: SupplierRepository, clock: Clock, audit: AuditPort | None = None
    ):
        self._supplier_repo = supplier_repository
        self._clock = clock
        self._audit = audit or NullAuditPort()

    def execute(self, command: CreateSupplierCommand) -> Supplier:
        supplier = Supplier(
            name=command.name,
            contact_name=command.contact_name,
            email=command.email,
            phone=command.phone,
            address=command.address,
            created_at=self._clock.now(),
        )
        self._supplier_repo.save(supplier)
        self._audit.record(
            user_id=command.actor_id,
            action="supplier.created",
            entity_type="supplier",
            entity_id=str(supplier.id),
            after={"name": supplier.name, "phone": supplier.phone, "email": supplier.email},
        )
        return supplier


class UpdateSupplierUseCase:
    def __init__(self, supplier_repository: SupplierRepository, audit: AuditPort | None = None):
        self._supplier_repo = supplier_repository
        self._audit = audit or NullAuditPort()

    def execute(self, command: UpdateSupplierCommand) -> Supplier:
        supplier = self._supplier_repo.get_by_id(command.supplier_id)
        if supplier is None:
            raise SupplierNotFoundError("Supplier not found")
        before = supplier_contact_snapshot(supplier)
        supplier.update_contact(
            name=command.name,
            contact_name=command.contact_name,
            email=command.email,
            phone=command.phone,
            address=command.address,
        )
        self._supplier_repo.save(supplier)
        after = supplier_contact_snapshot(supplier)
        changed = {key: value for key, value in after.items() if value != before[key]}
        if changed:
            self._audit.record(
                user_id=command.actor_id,
                action="supplier.updated",
                entity_type="supplier",
                entity_id=str(supplier.id),
                before={key: before[key] for key in changed},
                after=changed,
            )
        return supplier


class ListSuppliersUseCase:
    def __init__(self, supplier_repository: SupplierRepository):
        self._supplier_repo = supplier_repository

    def execute(self, *, search: str | None = None) -> list[Supplier]:
        return self._supplier_repo.list_suppliers(search=search)


class GetSupplierUseCase:
    def __init__(self, supplier_repository: SupplierRepository):
        self._supplier_repo = supplier_repository

    def execute(self, supplier_id: UUID) -> Supplier:
        supplier = self._supplier_repo.get_by_id(supplier_id)
        if supplier is None:
            raise SupplierNotFoundError("Supplier not found")
        return supplier
