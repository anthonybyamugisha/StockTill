import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listUsers, createUser, updateUser, deactivateUser } from '../api/users';
import { Card } from '../../../shared/ui/Card';
import { Button } from '../../../shared/ui/Button';
import { Badge } from '../../../shared/ui/Badge';
import { Table } from '../../../shared/ui/Table';
import { Modal } from '../../../shared/ui/Modal';
import { Input } from '../../../shared/ui/Input';
import { Select } from '../../../shared/ui/Select';

export function UsersPage() {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState<any>(null);

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: listUsers,
  });

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setShowModal(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateUser(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setShowModal(false);
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: deactivateUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  });

  const roleColors: Record<string, 'primary' | 'success' | 'neutral'> = {
    admin: 'primary',
    manager: 'success',
    cashier: 'neutral',
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-surface-400">{users?.length ?? 0} users</p>
        <Button onClick={() => { setEditingUser(null); setShowModal(true); }}>
          Add User
        </Button>
      </div>

      <Card>
        {isLoading ? (
          <p className="py-8 text-center text-surface-400">Loading users...</p>
        ) : (
          <Table
            columns={[
              { key: 'name', header: 'Name', render: (u: any) => (
                <div>
                  <p className="font-medium">{u.first_name} {u.last_name}</p>
                  <p className="text-xs text-surface-400">{u.email}</p>
                </div>
              )},
              { key: 'role', header: 'Role', render: (u: any) => (
                <Badge variant={roleColors[u.role] || 'neutral'}>{u.role}</Badge>
              )},
              { key: 'status', header: 'Status', render: (u: any) => (
                <Badge variant={u.is_active ? 'success' : 'neutral'}>{u.is_active ? 'Active' : 'Inactive'}</Badge>
              )},
              { key: 'last_login', header: 'Last Login', render: (u: any) => u.last_login ? new Date(u.last_login).toLocaleDateString() : 'Never' },
              { key: 'actions', header: '', render: (u: any) => (
                <div className="flex gap-1">
                  <button onClick={() => { setEditingUser(u); setShowModal(true); }} className="btn-ghost btn-sm">Edit</button>
                  {u.is_active && u.role !== 'admin' && (
                    <button onClick={() => deactivateMutation.mutate(u.id)} className="btn-danger btn-sm">Deactivate</button>
                  )}
                </div>
              )},
            ]}
            data={users || []}
            keyExtractor={(u) => u.id}
            emptyMessage="No users found"
          />
        )}
      </Card>

      {showModal && (
        <UserModal
          user={editingUser}
          onClose={() => setShowModal(false)}
          onSubmit={(data) => {
            if (editingUser) {
              updateMutation.mutate({ id: editingUser.id, data });
            } else {
              createMutation.mutate(data);
            }
          }}
          isLoading={createMutation.isPending || updateMutation.isPending}
        />
      )}
    </div>
  );
}

function UserModal({ user, onClose, onSubmit, isLoading }: {
  user: any;
  onClose: () => void;
  onSubmit: (data: any) => void;
  isLoading: boolean;
}) {
  const [form, setForm] = useState({
    email: user?.email || '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    role: user?.role || 'cashier',
    password: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={user ? 'Edit User' : 'Add User'}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={isLoading}>
            {isLoading ? 'Saving...' : 'Save'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input label="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        <div className="grid grid-cols-2 gap-4">
          <Input label="First Name" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} required />
          <Input label="Last Name" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} required />
        </div>
        <Select
          label="Role"
          value={form.role}
          onChange={(e) => setForm({ ...form, role: e.target.value })}
          options={[
            { value: 'admin', label: 'Administrator' },
            { value: 'manager', label: 'Manager' },
            { value: 'cashier', label: 'Cashier' },
          ]}
        />
        {!user && (
          <Input label="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
        )}
      </form>
    </Modal>
  );
}
