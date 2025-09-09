import React from 'react';
import { Card, CardContent } from './card';
import { Input } from './input';
import { Button } from './button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './select';
import { Badge } from './badge';
import { 
  Search, 
  Filter, 
  X, 
  Calendar,
  RotateCcw 
} from 'lucide-react';

const AdvancedFilters = ({ 
  searchTerm, 
  onSearchChange, 
  filters, 
  onFilterChange, 
  onClearFilters,
  dateFilters,
  onDateFilterChange,
  activeFiltersCount = 0,
  className = ""
}) => {
  const hasActiveFilters = activeFiltersCount > 0 || searchTerm;

  return (
    <Card className={className}>
      <CardContent className="p-6">
        <div className="space-y-4">
          {/* Search Bar */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search..."
                  value={searchTerm}
                  onChange={(e) => onSearchChange(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            {/* Clear Filters Button */}
            {hasActiveFilters && (
              <Button
                variant="outline"
                onClick={onClearFilters}
                className="flex items-center gap-2"
              >
                <RotateCcw className="h-4 w-4" />
                Clear Filters
                {activeFiltersCount > 0 && (
                  <Badge variant="secondary" className="ml-1">
                    {activeFiltersCount}
                  </Badge>
                )}
              </Button>
            )}
          </div>

          {/* Filter Controls */}
          <div className="flex flex-wrap items-center gap-2">
            <Filter className="h-4 w-4 text-gray-500" />
            
            {/* Render filter dropdowns */}
            {filters && filters.map((filter, index) => (
              <Select
                key={index}
                value={filter.value}
                onValueChange={(value) => onFilterChange(filter.key, value)}
              >
                <SelectTrigger className={`${filter.width || 'w-[150px]'} ${filter.value !== filter.defaultValue ? 'ring-2 ring-blue-200' : ''}`}>
                  <SelectValue placeholder={filter.placeholder} />
                </SelectTrigger>
                <SelectContent>
                  {filter.options.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ))}

            {/* Date Range Filters */}
            {dateFilters && dateFilters.map((dateFilter, index) => (
              <div key={index} className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-gray-500" />
                <Input
                  type="date"
                  value={dateFilter.value}
                  onChange={(e) => onDateFilterChange(dateFilter.key, e.target.value)}
                  className="w-[140px]"
                  placeholder={dateFilter.placeholder}
                />
                {dateFilter.value && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDateFilterChange(dateFilter.key, '')}
                    className="p-1 h-6 w-6"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                )}
              </div>
            ))}
          </div>

          {/* Active Filters Display */}
          {hasActiveFilters && (
            <div className="flex flex-wrap gap-2 pt-2 border-t">
              {searchTerm && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  Search: "{searchTerm}"
                  <X 
                    className="h-3 w-3 cursor-pointer" 
                    onClick={() => onSearchChange('')}
                  />
                </Badge>
              )}
              
              {filters && filters.map((filter) => {
                if (filter.value !== filter.defaultValue) {
                  const selectedOption = filter.options.find(opt => opt.value === filter.value);
                  return (
                    <Badge key={filter.key} variant="secondary" className="flex items-center gap-1">
                      {filter.label}: {selectedOption?.label || filter.value}
                      <X 
                        className="h-3 w-3 cursor-pointer" 
                        onClick={() => onFilterChange(filter.key, filter.defaultValue)}
                      />
                    </Badge>
                  );
                }
                return null;
              })}

              {dateFilters && dateFilters.map((dateFilter) => {
                if (dateFilter.value) {
                  return (
                    <Badge key={dateFilter.key} variant="secondary" className="flex items-center gap-1">
                      {dateFilter.label}: {new Date(dateFilter.value).toLocaleDateString()}
                      <X 
                        className="h-3 w-3 cursor-pointer" 
                        onClick={() => onDateFilterChange(dateFilter.key, '')}
                      />
                    </Badge>
                  );
                }
                return null;
              })}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default AdvancedFilters;