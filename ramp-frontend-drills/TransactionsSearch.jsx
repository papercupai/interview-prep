// A Ramp-shaped data view: debounced search over a paginated API, with loading,
// error and "no more pages" states, and a guard against out-of-order responses.
// It exercises the framework's Level 3 skills: async calls, errors, pagination.
import { useEffect, useState } from 'react';

export function useDebounced(value, delayMs = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(id);
  }, [value, delayMs]);
  return debounced;
}

// fetchPage(query, page, pageSize) -> Promise<{ items: [{ id, merchant, amountCents }], hasMore }>
export default function TransactionsSearch({ fetchPage, pageSize = 10, debounceMs = 300 }) {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounced(query, debounceMs);
  // Remember which query a page number belongs to, so a new search starts on
  // page 1 without a second state update (and without a wasted request).
  const [pageFor, setPageFor] = useState({ query: '', page: 0 });
  const page = pageFor.query === debouncedQuery ? pageFor.page : 0;
  const [result, setResult] = useState({ status: 'loading', items: [], hasMore: false, error: null });

  useEffect(() => {
    let stale = false; // a slower, older response must never overwrite a newer one
    setResult((r) => ({ ...r, status: 'loading', error: null }));
    fetchPage(debouncedQuery, page, pageSize)
      .then(({ items, hasMore }) => {
        if (!stale) setResult({ status: 'ready', items, hasMore, error: null });
      })
      .catch((err) => {
        if (!stale) setResult({ status: 'error', items: [], hasMore: false, error: err.message });
      });
    return () => {
      stale = true;
    };
  }, [fetchPage, debouncedQuery, page, pageSize]);

  return (
    <div>
      <input aria-label="search merchants" value={query} onChange={(e) => setQuery(e.target.value)} />
      {result.status === 'loading' && <p>Loading...</p>}
      {result.status === 'error' && <p role="alert">{result.error}</p>}
      <table>
        <thead>
          <tr>
            <th>Merchant</th>
            <th>Amount</th>
          </tr>
        </thead>
        <tbody>
          {result.items.map((t) => (
            <tr key={t.id}>
              <td>{t.merchant}</td>
              <td>{(t.amountCents / 100).toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <button type="button" disabled={page === 0} onClick={() => setPageFor({ query: debouncedQuery, page: page - 1 })}>
        Previous
      </button>
      <span> Page {page + 1} </span>
      <button
        type="button"
        disabled={!result.hasMore || result.status !== 'ready'}
        onClick={() => setPageFor({ query: debouncedQuery, page: page + 1 })}
      >
        Next
      </button>
    </div>
  );
}
