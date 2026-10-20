from catalog.application.commands import (
    CreateCategoryCommand,
    DeactivateCategoryCommand,
)
from catalog.domain.entities import Category
from catalog.domain.repository import CategoryRepository
from shared.application.audit import AuditPort, NullAuditPort


class CreateCategoryUseCase:
    def __init__(self, category_repository: CategoryRepository, audit: AuditPort | None = None):
        self._repo = category_repository
        self._audit = audit or NullAuditPort()

    def execute(self, command: CreateCategoryCommand) -> Category:
        category = Category(
            name=command.name,
            description=command.description,
            parent_id=command.parent_id,
        )
        self._repo.save(category)
        self._audit.record(
            user_id=command.user_id,
            action="category.created",
            entity_type="category",
            entity_id=str(category.id),
            after={"name": category.name},
        )
        return category


class ListCategoriesUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self._repo = category_repository

    def execute(self, active_only: bool = True) -> list[Category]:
        return self._repo.list_categories(active_only=active_only)


class DeactivateCategoryUseCase:
    def __init__(self, category_repository: CategoryRepository, audit: AuditPort | None = None):
        self._repo = category_repository
        self._audit = audit or NullAuditPort()

    def execute(self, command: DeactivateCategoryCommand) -> Category:
        category = self._repo.get_by_id(command.category_id)
        if category is None:
            raise ValueError("Category not found")

        category.is_active = False
        self._repo.save(category)
        self._audit.record(
            user_id=command.user_id,
            action="category.deactivated",
            entity_type="category",
            entity_id=str(category.id),
            before={"is_active": True, "name": category.name},
            after={"is_active": False},
        )
        return category
