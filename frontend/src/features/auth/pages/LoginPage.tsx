import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { login } from '../api/auth';

const loginSchema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormData = z.infinite<typeof loginSchema>;

export function LoginPage() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const mutation = useMutation({
    mutationFn: (data: LoginFormData) => login(data),
    onSuccess: () => {
      window.location.href = '/';
    },
  });

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-50">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-lg bg-primary-500 text-white text-xl font-bold">
            ST
          </div>
          <h1 className="text-2xl font-semibold text-surface-600">StockTill</h1>
          <p className="mt-1 text-sm text-surface-400">Sign in to your account</p>
        </div>

        <form
          onSubmit={handleSubmit((data) => mutation.mutate(data))}
          className="card space-y-4"
        >
          <div>
            <label className="label">Email</label>
            <input
              type="email"
              {...register('email')}
              className={`input ${errors.email ? 'border-error' : ''}`}
              placeholder="you@shop.com"
            />
            {errors.email && <p className="mt-1 text-xs text-error">{errors.email.message}</p>}
          </div>

          <div>
            <label className="label">Password</label>
            <input
              type="password"
              {...register('password')}
              className={`input ${errors.password ? 'border-error' : ''}`}
              placeholder="Enter your password"
            />
            {errors.password && <p className="mt-1 text-xs text-error">{errors.password.message}</p>}
          </div>

          {mutation.error && (
            <div className="rounded bg-red-50 px-3 py-2 text-sm text-error">
              {(mutation.error as Error).message}
            </div>
          )}

          <button
            type="submit"
            disabled={mutation.isPending}
            className="btn-primary w-full"
          >
            {mutation.isPending ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
