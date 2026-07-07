// frontend/src/hooks/useServerPagination.jsx
//
// Server-side pagination state (Sprint 6.2 #3). Unlike usePagination.jsx
// (which slices an already-loaded array client-side), this tracks page + total
// for pages that fetch ONE page at a time from a paginated endpoint returning
// { items, total, limit, offset }.
//
// Usage:
//   const pg = useServerPagination(25);
//   // fetch with pg.limit + pg.offset, then pg.setTotal(res.total)
//   // render <Pagination currentPage={pg.page} totalPages={pg.totalPages}
//   //          onPageChange={pg.setPage} />
//   // pg.reset() jumps back to page 1 (e.g. when a filter changes)

import { useState } from "react";

export default function useServerPagination(itemsPerPage = 25) {
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const totalPages = Math.max(1, Math.ceil(total / itemsPerPage));
  const offset = (page - 1) * itemsPerPage;

  const reset = () => setPage(1);

  return {
    page,
    setPage,
    total,
    setTotal,
    totalPages,
    limit: itemsPerPage,
    offset,
    reset,
  };
}
