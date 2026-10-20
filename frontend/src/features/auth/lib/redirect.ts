import { User } from '../api/auth';

export function homePathFor(user: Pick<User, 'must_change_password'>): string {
  return user.must_change_password ? '/change-password' : '/';
}
