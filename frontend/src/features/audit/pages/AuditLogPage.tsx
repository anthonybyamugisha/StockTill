import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { Card } from '../../../shared/ui/Card';
import { Table } from '../../../shared/ui/Table';
import { Badge } from '../../../shared/ui/Badge';
import { apiClient } from '../../../shared/http/client';

interface AuditEntry {
  id: string;
  user_id: string | null;
  user_name: string | null;
  user_email: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  timestamp: string;
}

type BadgeVariant = 'success' | 'warning' | 'error' | 'neutral' | 'primary';

function actionVariant(action: string): BadgeVariant {
  if (/(voided|failed|blocked|deactivated|cancelled)/.test(action)) return 'error';
  if (/^(auth\.login$|auth\.password_changed$|sale\.completed|shift\.opened|purchase_order\.received)/.test(action)) return 'success';
  if (/^(stock\.|product\.(updated|created)|settings\.updated|supplier\.(updated|created))/.test(action)) return 'warning';
  return 'primary';
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '—';
  if (Array.isArray(value)) return value.length ? value.join(', ') : '—';
  if (typeof value === 'boolean') return value ? 'yes' : 'no';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function ChangeList({ before, after }: { before: Record<string, unknown> | null; after: Record<string, unknown> | null }) {
  const keys = Array.from(new Set([...Object.keys(before ?? {}), ...Object.keys(after ?? {})]));
  if (keys.length === 0) {
    return <span className="text-surface-400">—</span>;
  }
  return (
    <div className="space-y-0.5 text-xs">
      {keys.map((key) => {
        const hadValue = before !== null && key in before;
        const hasValue = after !== null && key in after;
        return (
          <div key={key}>
            <span className="text-surface-400">{key}: </span>
            {hadValue && <span className="text-surface-500">{formatValue(before?.[key])}</span>}
            {hadValue && hasValue && <span className="text-surface-400"> → </span>}
            {hasValue && <span className="font-medium text-surface-700">{formatValue(after?.[key])}</span>}
          </div>
        );
      })}
    </div>
  );
}

export function AuditLogPage() {
  const [query, setQuery] = useState('');
  const { data: logs, isLoading } = useQuery({
    queryKey: ['auditLog'],
    queryFn: async () => {
      const res = await apiClient.get<AuditEntry[]>('/accounts/audit-log/');
      return res.data;
    },
  });

  const filtered = useMemo(() => {
    const entries = logs ?? [];
    const term = query.trim().toLowerCase();
    if (!term) return entries;
    return entries.filter((entry) =>
      [entry.action, entry.entity_type, entry.entity_id, entry.user_name, entry.user_email]
        .filter(Boolean)
        .some((field) => String(field).toLowerCase().includes(term)),
    );
  }, [logs, query]);

  return (
    <div className="space-y-4">
      <Card title="Audit Log" subtitle="Track who changed what, and when">
        <div className="mb-4">
          <input
            className="input w-full max-w-sm"
            placeholder="Filter by user, action or entity..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
        {isLoading ? (
          <p className="py-8 text-center text-surface-400">Loading audit log...</p>
        ) : (
          <Table
            columns={[
              {
                key: 'timestamp',
                header: 'Time',
                render: (log: AuditEntry) => (
                  <span className="whitespace-nowrap">{new Date(log.timestamp).toLocaleString()}</span>
                ),
              },
              {
                key: 'user',
                header: 'User',
                render: (log: AuditEntry) => (
                  <div>
                    <p className="font-medium text-surface-700">{log.user_name || log.user_email || 'System'}</p>
                    {log.user_name && log.user_email && (
                      <p className="text-xs text-surface-400">{log.user_email}</p>
                    )}
                  </div>
                ),
              },
              {
                key: 'action',
                header: 'Action',
                render: (log: AuditEntry) => (
                  <Badge variant={actionVariant(log.action)}>{log.action}</Badge>
                ),
              },
              {
                key: 'entity',
                header: 'Entity',
                render: (log: AuditEntry) => (
                  <span className="text-surface-600">
                    {log.entity_type} ({log.entity_id.slice(0, 8)})
                  </span>
                ),
              },
              {
                key: 'changes',
                header: 'Changes',
                render: (log: AuditEntry) => <ChangeList before={log.before} after={log.after} />,
              },
            ]}
            data={filtered}
            keyExtractor={(log) => log.id}
            emptyMessage="No audit entries yet"
          />
        )}
      </Card>
    </div>
  );
}
