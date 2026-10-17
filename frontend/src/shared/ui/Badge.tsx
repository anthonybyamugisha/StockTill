import { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'success' | 'warning' | 'error' | 'neutral' | 'primary';
}

const variantClasses = {
  success: 'badge-success',
  warning: 'badge-warning',
  error: 'badge-error',
  neutral: 'badge-neutral',
  primary: 'bg-primary-100 text-primary-700',
};

export function Badge({ children, variant = 'neutral' }: BadgeProps) {
  return <span className={variantClasses[variant]}>{children}</span>;
}
