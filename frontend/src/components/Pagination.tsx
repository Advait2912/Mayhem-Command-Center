import React from 'react';
import './Pagination.css';

interface PaginationProps {
  total: number;
  limit: number;
  offset: number;
  onPageChange: (newOffset: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({ total, limit, offset, onPageChange }) => {
  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit);

  if (totalPages <= 1) return null;

  const handlePrev = () => {
    if (offset - limit >= 0) {
      onPageChange(offset - limit);
    }
  };

  const handleNext = () => {
    if (offset + limit < total) {
      onPageChange(offset + limit);
    }
  };

  return (
    <div className="pagination">
      <button 
        className="page-btn" 
        onClick={handlePrev} 
        disabled={currentPage === 1}
      >
        &laquo; Prev
      </button>
      <span className="page-info">
        Page {currentPage} of {totalPages}
      </span>
      <button 
        className="page-btn" 
        onClick={handleNext} 
        disabled={currentPage === totalPages}
      >
        Next &raquo;
      </button>
    </div>
  );
};
