import { useQuery } from '@tanstack/react-query';
import { getCurrentUser, User } from '../api/auth';

export function useAuth() {
  const { data: user, isLoading } = useQuery<User | null>({
    queryKey: ['currentUser'],
    queryFn: getCurrentUser,
    retry: false,
  });

  return { user, isLoading };
}
