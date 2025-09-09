import React from 'react';
import { TableHead } from './table';
import { Button } from './button';
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';

const TableHeaderSortable = ({ 
  children, 
  sortKey, 
  currentSort, 
  onSort, 
  className = "" 
}) => {
  const handleSort = () => {
    if (currentSort.key === sortKey) {
      // If already sorting by this column, toggle direction
      const newDirection = currentSort.direction === 'asc' ? 'desc' : 'asc';
      onSort({ key: sortKey, direction: newDirection });
    } else {
      // If not sorting by this column, start with ascending
      onSort({ key: sortKey, direction: 'asc' });
    }
  };

  const getSortIcon = () => {
    if (currentSort.key !== sortKey) {
      return <ArrowUpDown className="h-4 w-4" />;
    }
    return currentSort.direction === 'asc' 
      ? <ArrowUp className="h-4 w-4" />
      : <ArrowDown className="h-4 w-4" />;
  };

  return (
    <TableHead className={className}>
      <Button
        variant="ghost"
        onClick={handleSort}
        className="h-auto p-0 font-semibold hover:bg-transparent flex items-center gap-2"
      >
        {children}
        {getSortIcon()}
      </Button>
    </TableHead>
  );
};

export default TableHeaderSortable;