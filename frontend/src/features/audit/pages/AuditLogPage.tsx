import { useQuery } from '@tanstack/react-query';
import { Card } from '../../../shared/ui/Card';
import { Table } from '../../../shared/ui/Table';
import { Badge } from '../../../shared/ui/Badge';
import { apiClient } from '../../../shared/http/client';

export function AuditLogPage() {
  const { data: logs, isLoading } = useQuery({
    queryKey: ['auditLog'],
    queryFn: async () => {
      const res = await apiClient.get('/accounts/audit-log/');
      return res.data;
    },
  });

  return (
    <div className="space-y-4">
      <Card title="Audit Log" subtitle="Track all system activities">
        {isLoading ? (
          <p className="py-8 text-center text-surface-400">Loading audit log...</p>
        ) : (
          <Table
            columns={[
              { key: 'timestamp', header: 'Time', render: (log: any) => new Date(log.timestamp).toLocaleString() },
              { key: 'user', header: 'User', render: (log: any) => log.user_id?.slice(0, 8) || 'System' },
              { key: 'action', header: 'Action', render: (log: any) => (
                <Badge variant="primary">{log.action}</Badge>
              )},
              { key: 'entity', header: 'Entity', render: (log: any) => `${log.entity_type} (${log.entity_id?.slice(0, 8)})` },
              { key: 'changes', header: 'Changes', render: (log: any) => (
                <div className="text-xs">
                  {log.before && <p>Before: {JSON.stringify(log.before)}</p>}
                  {log.after && <p>After: {JSON.stringify(log.after)}</p>}
                </div>
              )},
            ]}
            data={logs || []}
            keyExtractor={(log) => log.id}
            emptyMessage="No audit logs found"
          />
        )}
      </Card>
    </div>
  );
}
