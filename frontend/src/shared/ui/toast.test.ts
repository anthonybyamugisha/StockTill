import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createToastStore } from './toast';

describe('createToastStore', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('starts empty', () => {
    expect(createToastStore().getSnapshot()).toEqual([]);
  });

  it('adds a toast and notifies subscribers', () => {
    const store = createToastStore();
    const listener = vi.fn();
    store.subscribe(listener);

    store.success('Product added');

    expect(store.getSnapshot()).toHaveLength(1);
    expect(store.getSnapshot()[0]).toMatchObject({ kind: 'success', message: 'Product added' });
    expect(listener).toHaveBeenCalledTimes(1);
  });

  it('auto-dismisses after the duration', () => {
    const store = createToastStore(1000);
    store.info('Saved');

    vi.advanceTimersByTime(999);
    expect(store.getSnapshot()).toHaveLength(1);

    vi.advanceTimersByTime(1);
    expect(store.getSnapshot()).toEqual([]);
  });

  it('keeps a toast when the duration is zero', () => {
    const store = createToastStore();
    store.error('Failed', 0);

    vi.advanceTimersByTime(60_000);
    expect(store.getSnapshot()).toHaveLength(1);
  });

  it('dismisses by id', () => {
    const store = createToastStore(0);
    const id = store.success('One');
    store.success('Two');

    store.dismiss(id);

    expect(store.getSnapshot().map((item) => item.message)).toEqual(['Two']);
  });

  it('ignores dismissing an unknown id', () => {
    const store = createToastStore(0);
    const listener = vi.fn();
    store.success('One');
    store.subscribe(listener);

    store.dismiss(999);

    expect(store.getSnapshot()).toHaveLength(1);
    expect(listener).not.toHaveBeenCalled();
  });

  it('clears everything', () => {
    const store = createToastStore(0);
    store.success('One');
    store.success('Two');

    store.clear();

    expect(store.getSnapshot()).toEqual([]);
  });

  it('stops notifying unsubscribed listeners', () => {
    const store = createToastStore(0);
    const listener = vi.fn();
    const unsubscribe = store.subscribe(listener);
    unsubscribe();

    store.success('One');

    expect(listener).not.toHaveBeenCalled();
  });
});
