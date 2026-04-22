// frontend/src/components/Pagination.jsx
import React from "react";

export default function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  maxPagesToShow = 5,
}) {
  if (totalPages <= 1) return null;

  const half = Math.floor(maxPagesToShow / 2);
  let start = Math.max(1, currentPage - half);
  let end = Math.min(totalPages, start + maxPagesToShow - 1);

  // Adjust start if we're near the end
  start = Math.max(1, end - maxPagesToShow + 1);

  const pages = [];
  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  return (
    <div className="flex gap-sm justify-center mt-md">
      <button
        className="btn btn-secondary"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
      >
        Prev
      </button>

      {pages.map((p) => (
        <button
          key={p}
          className={`btn ${p === currentPage ? "btn-primary" : "btn-secondary"}`}
          onClick={() => onPageChange(p)}
        >
          {p}
        </button>
      ))}

      <button
        className="btn btn-secondary"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
      >
        Next
      </button>
    </div>
  );
}
