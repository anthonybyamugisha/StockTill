import { Link } from 'react-router-dom';
import { useAuth } from '../../features/auth/hooks/useAuth';
import { logout } from '../../features/auth/api/auth';

interface HeaderProps {
  onOpenNav: () => void;
}

export function Header({ onOpenNav }: HeaderProps) {
  const { user } = useAuth();

  if (!user) return null;

  const handleLogout = async () => {
    await logout();
    window.location.href = '/login';
  };

  const roleLabels: Record<string, string> = {
    admin: 'Administrator',
    manager: 'Manager',
    cashier: 'Cashier',
  };

  const today = new Date().toLocaleDateString('en-UG', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-3 border-b border-surface-100 bg-white px-4 shadow-nav sm:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          onClick={onOpenNav}
          aria-label="Open navigation"
          aria-controls="main-navigation"
          className="-ml-1 rounded p-2 text-surface-500 hover:bg-surface-100 hover:text-surface-600 md:hidden"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <h2 className="hidden truncate text-sm font-medium text-surface-500 md:block" title={today}>
          {today}
        </h2>
      </div>

      <div className="flex shrink-0 items-center gap-2 sm:gap-4">
        <div className="hidden text-right lg:block">
          <p className="max-w-[12rem] truncate text-sm font-medium text-surface-600">
            {user.first_name} {user.last_name}
          </p>
          <p className="text-xs text-surface-400">{roleLabels[user.role] || user.role}</p>
        </div>
        <div
          className="hidden h-9 w-9 items-center justify-center rounded-full bg-primary-100 text-sm font-semibold text-primary-700 sm:flex"
          aria-hidden="true"
        >
          {user.first_name?.[0] ?? ''}
          {user.last_name?.[0] ?? ''}
        </div>
        <Link
          to="/change-password"
          className="btn-secondary btn-sm"
          aria-label="Change password"
          title="Change password"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
          </svg>
          <span className="hidden md:inline">Change Password</span>
        </Link>
        <button
          onClick={handleLogout}
          className="btn-secondary btn-sm"
          aria-label="Sign out"
          title="Sign out"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          <span className="hidden md:inline">Sign Out</span>
        </button>
      </div>
    </header>
  );
}
