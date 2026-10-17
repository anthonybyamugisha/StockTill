export function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString('en-UG', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(isoString: string): string {
  return new Date(isoString).toLocaleString('en-UG', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function toISODate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function todayISO(now: Date = new Date()): string {
  return toISODate(now);
}

export function daysAgoISO(days: number, now: Date = new Date()): string {
  return toISODate(new Date(now.getFullYear(), now.getMonth(), now.getDate() - days));
}

export function monthStartISO(now: Date = new Date()): string {
  return toISODate(new Date(now.getFullYear(), now.getMonth(), 1));
}

export function formatShortDate(isoDate: string): string {
  const [year, month, day] = isoDate.split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString('en-UG', {
    day: 'numeric',
    month: 'short',
  });
}
