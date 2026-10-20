from typing import Any

from catalog.application.commands import (
    CreateCategoryCommand,
    DeactivateCategoryCommand,
    UpdateCategoryCommand,
)
from catalog.domain.entities import Category
from catalog.domain.repository import CategoryRepository
from shared.application.audit import AuditPort, NullAuditPort


def category_snapshot(category: Category) -> dict[str, Any]:
    return {
        "name": category.name,
        "description": category.description,
        "parent_id": str(category.parent_id) if category.parent_id else None,
        "is_active": category.is_active,
    }


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


class UpdateCategoryUseCase:
    def __init__(self, category_repository: CategoryRepository, audit: AuditPort | None = None):
        self._repo = category_repository
        self._audit = audit or NullAuditPort()

    def execute(self, command: UpdateCategoryCommand) -> Category:
        category = self._repo.get_by_id(command.category_id)
        if category is None:
            raise ValueError("Category not found")

        before = category_snapshot(category)

        if command.parent_set:
            if command.parent_id == category.id:
                raise ValueError("A category cannot be its own parent")
            parent_id = command.parent_id
            while parent_id is not None:
                parent = self._repo.get_by_id(parent_id)
                if parent is None:
                    raise ValueError("Parent category not found")
                if parent.id == category.id:
                    raise ValueError("A category cannot be moved below its own child")
                parent_id = parent.parent_id
            category.parent_id = command.parent_id

        if command.name is not None:
            category.name = command.name
        if command.description is not None:
            category.description = command.description
        if command.is_active is not None:
            category.is_active = command.is_active

        self._repo.save(category)
        after = category_snapshot(category)
        changed = {key: value for key, value in after.items() if value != before[key]}
        if changed:
            self._audit.record(
                user_id=command.user_id,
                action="category.updated",
                entity_type="category",
                entity_id=str(category.id),
                before={key: before[key] for key in changed},
                after=changed,
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
