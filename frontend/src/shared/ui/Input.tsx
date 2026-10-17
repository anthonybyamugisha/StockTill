import { InputHTMLAttributes, forwardRef } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = '', ...props }, ref) => {
    return (
      <div>
        {label && <label className="label">{label}</label>}
        <input ref={ref} className={`input ${error ? 'border-error' : ''} ${className}`} {...props} />
        {error && <p className="mt-1 text-xs text-error">{error}</p>}
      </div>
    );
  },
);

Input.displayName = 'Input';
