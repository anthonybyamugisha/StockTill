import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { changePassword, logout } from '../api/auth';
import { confirmationIssue, passwordIssue } from '../lib/passwordPolicy';
import { useAuth } from '../hooks/useAuth';
import { Input } from '../../../shared/ui/Input';
import { getApiErrorMessage } from '../../../shared/http/errors';
import logo from '../../../logo_image.png';

const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, 'Enter your current password'),
    new_password: z.string().superRefine((value, ctx) => {
      const issue = passwordIssue(value);
      if (issue) {
        ctx.addIssue({ code: z.ZodIssueCode.custom, message: issue });
      }
    }),
    confirm_password: z.string(),
  })
  .superRefine((values, ctx) => {
    const issue = confirmationIssue(values.new_password, values.confirm_password);
    if (issue) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['confirm_password'],
        message: issue,
      });
    }
  });

type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;

export function ChangePasswordPage() {
  const { user } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
    mode: 'onTouched',
  });

  const signOut = async () => {
    try {
      await logout();
    } finally {
      window.location.href = '/login';
    }
  };

  const mutation = useMutation({
    mutationFn: (data: ChangePasswordFormData) =>
      changePassword({
        current_password: data.current_password,
        new_password: data.new_password,
      }),
    onSuccess: () => {
      window.location.href = '/';
    },
  });

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-50">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <img
            src={logo}
            alt="StockTill logo"
            className="mx-auto mb-4 h-16 w-16 object-contain"
          />
          <h1 className="text-2xl font-semibold text-surface-600">
            {user?.must_change_password ? 'Choose a new password' : 'Change your password'}
          </h1>
          <p className="mt-2 text-sm text-surface-400">
            {user?.must_change_password
              ? 'Your administrator gave you a temporary password. Replace it with one only you know before continuing.'
              : 'Use a password only you know. If someone else has seen your password, change it now.'}
          </p>
        </div>

        <form
          onSubmit={handleSubmit((data) => mutation.mutate(data))}
          className="card space-y-4"
        >
          <Input
            label="Current password"
            type="password"
            autoComplete="current-password"
            autoFocus
            error={errors.current_password?.message}
            {...register('current_password')}
          />

          <Input
            label="New password"
            type="password"
            autoComplete="new-password"
            error={errors.new_password?.message}
            {...register('new_password')}
          />
          <p className="-mt-2 text-xs text-surface-400">
            Use at least 8 characters, with a letter and a number.
          </p>

          <Input
            label="Confirm new password"
            type="password"
            autoComplete="new-password"
            error={errors.confirm_password?.message}
            {...register('confirm_password')}
          />

          {mutation.error && (
            <div className="rounded bg-red-50 px-3 py-2 text-sm text-error">
              {getApiErrorMessage(mutation.error, 'Could not update your password')}
            </div>
          )}

          <button type="submit" disabled={mutation.isPending} className="btn-primary w-full">
            {mutation.isPending ? 'Updating password...' : 'Update password'}
          </button>
        </form>

        <div className="mt-4 text-center text-xs text-surface-400">
          <span>{user?.email ? `Signed in as ${user.email}.` : 'Signed in.'}</span>{' '}
          <button type="button" onClick={signOut} className="underline hover:text-surface-600">
            Sign out
          </button>
        </div>
      </div>
    </div>
  );
}
