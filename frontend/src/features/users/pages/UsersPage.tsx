import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listUsers, createUser, updateUser, deactivateUser, User } from '../api/users';
import { Card } from '../../../shared/ui/Card';
import { Button } from '../../../shared/ui/Button';
import { Badge } from '../../../shared/ui/Badge';
import { Table } from '../../../shared/ui/Table';
import { Modal } from '../../../shared/ui/Modal';
import { ConfirmDialog } from '../../../shared/ui/ConfirmDialog';
import { Input } from '../../../shared/ui/Input';
import { Select } from '../../../shared/ui/Select';
import { toast } from '../../../shared/ui/toast';
import { getApiErrorMessage } from '../../../shared/http/errors';

export function UsersPage() {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [userToDeactivate, setUserToDeactivate] = useState<User | null>(null);

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: listUsers,
  });

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: (user) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setShowModal(false);
      toast.success(`${user.email} added. They must change the temporary password at first login.`);
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not add user')),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Pick<User, 'first_name' | 'last_name' | 'role'>> }) =>
      updateUser(id, data),
    onSuccess: (user) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setShowModal(false);
      toast.success(`User ${user.email} updated`);
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not update user')),
  });

  const deactivateMutation = useMutation({
    mutationFn: (user: User) => deactivateUser(user.id),
    onSuccess: (_data, user) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setUserToDeactivate(null);
      toast.success(`${user.first_name} ${user.last_name} was deactivated`);
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not deactivate user')),
  });

  const roleColors: Record<string, 'primary' | 'success' | 'neutral'> = {
    admin: 'primary',
    manager: 'success',
    cashier: 'neutral',
  };

  const pendingCount = users?.filter((user) => user.must_change_password).length ?? 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-surface-400">
          {users?.length ?? 0} users
          {pendingCount > 0 && ` · ${pendingCount} awaiting first login`}
        </p>
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
              { key: 'name', header: 'Name', render: (u: User) => (
                <div>
                  <p className="font-medium">{u.first_name} {u.last_name}</p>
                  <p className="text-xs text-surface-400">{u.email}</p>
                </div>
              )},
              { key: 'role', header: 'Role', render: (u: User) => (
                <Badge variant={roleColors[u.role] || 'neutral'}>{u.role}</Badge>
              )},
              { key: 'status', header: 'Status', render: (u: User) => (
                <div className="flex flex-wrap gap-1">
                  <Badge variant={u.is_active ? 'success' : 'neutral'}>{u.is_active ? 'Active' : 'Inactive'}</Badge>
                  {u.must_change_password && <Badge variant="warning">First login pending</Badge>}
                </div>
              )},
              { key: 'last_login', header: 'Last Login', render: (u: User) => u.last_login ? new Date(u.last_login).toLocaleDateString() : 'Never' },
              { key: 'actions', header: '', render: (u: User) => (
                <div className="flex gap-1">
                  <button onClick={() => { setEditingUser(u); setShowModal(true); }} className="btn-ghost btn-sm">Edit</button>
                  {u.is_active && u.role !== 'admin' && (
                    <button onClick={() => setUserToDeactivate(u)} className="btn-danger btn-sm">Deactivate</button>
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

      <ConfirmDialog
        isOpen={userToDeactivate !== null}
        title="Deactivate user?"
        message={
          <>
            <p>
              Are you sure you want to deactivate{' '}
              <span className="font-medium text-surface-700">
                {userToDeactivate?.first_name} {userToDeactivate?.last_name}
              </span>
              ?
            </p>
            <p className="mt-2">
              They will no longer be able to sign in, but their sales and history are kept.
            </p>
          </>
        }
        confirmLabel="Yes, deactivate"
        cancelLabel="Keep active"
        isLoading={deactivateMutation.isPending}
        onConfirm={() => {
          if (userToDeactivate) deactivateMutation.mutate(userToDeactivate);
        }}
        onCancel={() => {
          deactivateMutation.reset();
          setUserToDeactivate(null);
        }}
      />
    </div>
  );
}

function UserModal({ user, onClose, onSubmit, isLoading }: {
  user: User | null;
  onClose: () => void;
  onSubmit: (data: {
    email: string;
    first_name: string;
    last_name: string;
    role: User['role'];
    password: string;
  }) => void;
  isLoading: boolean;
}) {
  const [form, setForm] = useState<{
    email: string;
    first_name: string;
    last_name: string;
    role: User['role'];
    password: string;
  }>({
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
          onChange={(e) => setForm({ ...form, role: e.target.value as User['role'] })}
          options={[
            { value: 'admin', label: 'Administrator' },
            { value: 'manager', label: 'Manager' },
            { value: 'cashier', label: 'Cashier' },
          ]}
        />
        {!user && (
          <div className="space-y-1">
            <Input label="Temporary password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
            <p className="text-xs text-surface-400">
              At least 8 characters, with a letter and a number. The new user must replace it at\n              first sign-in.
            </p>
          </div>
        )}
      </form>
    </Modal>
  );
}
