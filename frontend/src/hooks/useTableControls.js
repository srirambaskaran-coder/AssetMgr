import { useState, useEffect, useMemo } from 'react';

const useTableControls = (data, initialConfig = {}) => {
  const {
    initialItemsPerPage = 10,
    initialSort = { key: null, direction: 'asc' },
    searchFields = [],
    sortableFields = {},
    filterFields = {}
  } = initialConfig;

  // State management
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(initialItemsPerPage);
  const [sortConfig, setSortConfig] = useState(initialSort);
  const [filters, setFilters] = useState({});
  const [dateFilters, setDateFilters] = useState({});

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, filters, dateFilters, sortConfig]);

  // Filter data
  const filteredData = useMemo(() => {
    if (!data) return [];

    return data.filter(item => {
      // Search term filtering
      if (searchTerm && searchFields.length > 0) {
        const searchLower = searchTerm.toLowerCase();
        const matchesSearch = searchFields.some(field => {
          const value = getNestedValue(item, field);
          return value && value.toString().toLowerCase().includes(searchLower);
        });
        if (!matchesSearch) return false;
      }

      // Standard filters
      for (const [key, value] of Object.entries(filters)) {
        if (value && value !== 'all') {
          const itemValue = getNestedValue(item, key);
          if (itemValue !== value) return false;
        }
      }

      // Date filters
      for (const [key, value] of Object.entries(dateFilters)) {
        if (value) {
          const itemDate = new Date(getNestedValue(item, key));
          const filterDate = new Date(value);
          
          // For date comparison, we check if the item date is on or after the filter date
          if (itemDate < filterDate) return false;
        }
      }

      return true;
    });
  }, [data, searchTerm, filters, dateFilters, searchFields]);

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortConfig.key || !filteredData.length) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aValue = getNestedValue(a, sortConfig.key);
      const bValue = getNestedValue(b, sortConfig.key);

      // Handle null/undefined values
      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return 1;
      if (bValue == null) return -1;

      // Get sort function for this field
      const fieldConfig = sortableFields[sortConfig.key];
      if (fieldConfig && fieldConfig.sortFn) {
        return fieldConfig.sortFn(aValue, bValue, sortConfig.direction);
      }

      // Default sorting
      let result = 0;
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        result = aValue.localeCompare(bValue);
      } else if (typeof aValue === 'number' && typeof bValue === 'number') {
        result = aValue - bValue;
      } else if (aValue instanceof Date && bValue instanceof Date) {
        result = aValue.getTime() - bValue.getTime();
      } else {
        result = String(aValue).localeCompare(String(bValue));
      }

      return sortConfig.direction === 'desc' ? -result : result;
    });
  }, [filteredData, sortConfig, sortableFields]);

  // Paginate data
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return sortedData.slice(startIndex, endIndex);
  }, [sortedData, currentPage, itemsPerPage]);

  // Pagination info
  const paginationInfo = useMemo(() => ({
    totalItems: sortedData.length,
    totalPages: Math.ceil(sortedData.length / itemsPerPage),
    currentPage,
    itemsPerPage,
    startIndex: (currentPage - 1) * itemsPerPage + 1,
    endIndex: Math.min(currentPage * itemsPerPage, sortedData.length)
  }), [sortedData.length, currentPage, itemsPerPage]);

  // Helper function to get nested object values
  const getNestedValue = (obj, path) => {
    return path.split('.').reduce((current, key) => current?.[key], obj);
  };

  // Event handlers
  const handleSearchChange = (term) => {
    setSearchTerm(term);
  };

  const handleSort = (sortKey) => {
    setSortConfig(prevSort => ({
      key: sortKey,
      direction: prevSort.key === sortKey && prevSort.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const handleFilterChange = (filterKey, value) => {
    setFilters(prev => ({
      ...prev,
      [filterKey]: value
    }));
  };

  const handleDateFilterChange = (filterKey, value) => {
    setDateFilters(prev => ({
      ...prev,
      [filterKey]: value
    }));
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handleItemsPerPageChange = (newItemsPerPage) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setSearchTerm('');
    setFilters({});
    setDateFilters({});
    setSortConfig(initialSort);
    setCurrentPage(1);
  };

  // Count active filters
  const activeFiltersCount = useMemo(() => {
    let count = 0;
    Object.values(filters).forEach(value => {
      if (value && value !== 'all') count++;
    });
    Object.values(dateFilters).forEach(value => {
      if (value) count++;
    });
    return count;
  }, [filters, dateFilters]);

  return {
    // Data
    data: paginatedData,
    filteredData,
    sortedData,
    totalItems: sortedData.length,

    // State
    searchTerm,
    sortConfig,
    filters,
    dateFilters,
    activeFiltersCount,

    // Pagination
    ...paginationInfo,

    // Handlers
    handleSearchChange,
    handleSort,
    handleFilterChange,
    handleDateFilterChange,
    handlePageChange,
    handleItemsPerPageChange,
    clearFilters
  };
};

export default useTableControls;