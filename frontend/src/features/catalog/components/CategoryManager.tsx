import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Category,
  createCategory,
  deactivateCategory,
  listCategories,
  updateCategory,
} from '../api/catalog';
import { Badge } from '../../../shared/ui/Badge';
import { Button } from '../../../shared/ui/Button';
import { Card } from '../../../shared/ui/Card';
import { ConfirmDialog } from '../../../shared/ui/ConfirmDialog';
import { Input } from '../../../shared/ui/Input';
import { Modal } from '../../../shared/ui/Modal';
import { Select } from '../../../shared/ui/Select';
import { Table } from '../../../shared/ui/Table';
import { getApiErrorMessage } from '../../../shared/http/errors';
import { toast } from '../../../shared/ui/toast';

export function CategoryManager() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [editing, setEditing] = useState<Category | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [toDeactivate, setToDeactivate] = useState<Category | null>(null);

  const { data: categories = [], isLoading } = useQuery({
    queryKey: ['catalog-categories'],
    queryFn: () => listCategories(false),
  });

  const visible = useMemo(
    () =>
      categories.filter((category) =>
        category.name.toLowerCase().includes(search.trim().toLowerCase()),
      ),
    [categories, search],
  );

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['catalog-categories'] });
    queryClient.invalidateQueries({ queryKey: ['catalog-products'] });
    queryClient.invalidateQueries({ queryKey: ['products'] });
  };

  const saveMutation = useMutation({
    mutationFn: (data: {
      id?: string;
      name: string;
      description: string;
      parent_id: string | null;
    }) =>
      data.id
        ? updateCategory(data.id, {
            name: data.name,
            description: data.description,
            parent_id: data.parent_id,
          })
        : createCategory(data),
    onSuccess: (category, variables) => {
      refresh();
      setShowModal(false);
      setEditing(null);
      toast.success(`Category "${category.name}" ${variables.id ? 'updated' : 'added'}`);
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: deactivateCategory,
    onSuccess: () => {
      refresh();
      toast.success(`Category "${toDeactivate?.name ?? ''}" deactivated`);
      setToDeactivate(null);
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not deactivate category')),
  });

  const reactivateMutation = useMutation({
    mutationFn: (id: string) => updateCategory(id, { is_active: true }),
    onSuccess: (category) => {
      refresh();
      toast.success(`Category "${category.name}" is active again`);
    },
  });

  const columns = [
    {
      key: 'name',
      header: 'Category',
      render: (category: Category) => (
        <div>
          <p className="font-medium">{category.name}</p>
          {category.description && (
            <p className="text-xs text-surface-400">{category.description}</p>
          )}
        </div>
      ),
    },
    {
      key: 'parent',
      header: 'Parent',
      render: (category: Category) =>
        categories.find((candidate) => candidate.id === category.parent_id)?.name ?? '—',
    },
    {
      key: 'status',
      header: 'Status',
      render: (category: Category) => (
        <Badge variant={category.is_active ? 'success' : 'neutral'}>
          {category.is_active ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (category: Category) => (
        <div className="flex gap-1">
          <button
            onClick={() => {
              setEditing(category);
              saveMutation.reset();
              setShowModal(true);
            }}
            className="btn-ghost btn-sm"
          >
            Edit
          </button>
          {category.is_active ? (
            <button onClick={() => setToDeactivate(category)} className="btn-danger btn-sm">
              Deactivate
            </button>
          ) : (
            <button
              onClick={() => reactivateMutation.mutate(category.id)}
              disabled={reactivateMutation.isPending}
              className="btn-secondary btn-sm"
            >
              Reactivate
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="relative w-80">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search categories..."
            className="input pl-10"
          />
          <svg
            className="absolute left-3 top-2.5 h-4 w-4 text-surface-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        <Button
          onClick={() => {
            setEditing(null);
            saveMutation.reset();
            setShowModal(true);
          }}
        >
          Add Category
        </Button>
      </div>

      <Card>
        {isLoading ? (
          <p className="py-8 text-center text-surface-400">Loading categories...</p>
        ) : (
          <Table
            columns={columns}
            data={visible}
            keyExtractor={(category) => category.id}
            emptyMessage={search.trim() ? 'No categories match your search' : 'No categories yet'}
          />
        )}
      </Card>

      {showModal && (
        <CategoryModal
          category={editing}
          categories={categories}
          error={
            saveMutation.error
              ? getApiErrorMessage(saveMutation.error, 'Could not save category')
              : null
          }
          isLoading={saveMutation.isPending}
          onClose={() => {
            saveMutation.reset();
            setShowModal(false);
            setEditing(null);
          }}
          onSubmit={(data) =>
            saveMutation.mutate({ id: editing?.id, ...data })
          }
        />
      )}

      <ConfirmDialog
        isOpen={toDeactivate !== null}
        title="Deactivate category?"
        message={
          <p>
            Products in <span className="font-medium text-surface-700">{toDeactivate?.name}</span>{' '}
            keep their category, but the category will no longer be offered for new products.
          </p>
        }
        confirmLabel="Yes, deactivate"
        cancelLabel="Keep active"
        isLoading={deactivateMutation.isPending}
        onConfirm={() => {
          if (toDeactivate) deactivateMutation.mutate(toDeactivate.id);
        }}
        onCancel={() => {
          deactivateMutation.reset();
          setToDeactivate(null);
        }}
      />
    </div>
  );
}

function CategoryModal({
  category,
  categories,
  error,
  isLoading,
  onClose,
  onSubmit,
}: {
  category: Category | null;
  categories: Category[];
  error: string | null;
  isLoading: boolean;
  onClose: () => void;
  onSubmit: (data: { name: string; description: string; parent_id: string | null }) => void;
}) {
  const [name, setName] = useState(category?.name ?? '');
  const [description, setDescription] = useState(category?.description ?? '');
  const [parentId, setParentId] = useState(category?.parent_id ?? '');

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    onSubmit({ name, description, parent_id: parentId || null });
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={category ? 'Edit Category' : 'Add Category'}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isLoading || !name.trim()}>
            {isLoading ? 'Saving...' : 'Save'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}
        <Input
          label="Name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          required
        />
        <Input
          label="Description"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
        <Select
          label="Parent category"
          value={parentId}
          onChange={(event) => setParentId(event.target.value)}
          options={[
            { value: '', label: 'No parent' },
            ...categories
              .filter((candidate) => candidate.id !== category?.id && candidate.is_active)
              .map((candidate) => ({ value: candidate.id, label: candidate.name })),
          ]}
        />
      </form>
    </Modal>
  );
}
