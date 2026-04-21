// frontend/src/hooks/usePagination.jsx
import { useState } from "react";

export default function usePagination(totalItems, itemsPerPage = 10) {
  const [currentPage, setCurrentPage] = useState(1);
  const totalPages = Math.ceil(totalItems / itemsPerPage);

  const paginate = (items) => {
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    return items.slice(start, end);
  };

  return { currentPage, setCurrentPage, totalPages, paginate };
}
