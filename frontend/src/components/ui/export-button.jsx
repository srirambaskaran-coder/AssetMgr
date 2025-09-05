import React, { useState } from 'react';
import { Button } from './button';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from './dropdown-menu';
import { Download, FileSpreadsheet, FileText } from 'lucide-react';
import { handleExport } from '../../utils/exportUtils';
import { toast } from 'sonner';

const ExportButton = ({ 
  data, 
  type, 
  customConfig = null, 
  disabled = false,
  className = "",
  size = "sm"
}) => {
  const [isExporting, setIsExporting] = useState(false);

  const handleExportClick = async (format) => {
    if (!data || data.length === 0) {
      toast.error('No data available to export');
      return;
    }

    setIsExporting(true);
    
    try {
      const success = handleExport(data, type, format, customConfig);
      
      if (success) {
        toast.success(`Data exported to ${format.toUpperCase()} successfully`);
      } else {
        toast.error(`Failed to export data to ${format.toUpperCase()}`);
      }
    } catch (error) {
      console.error('Export error:', error);
      toast.error(`Error exporting data: ${error.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size={size}
          disabled={disabled || isExporting || !data || data.length === 0}
          className={className}
        >
          <Download className="h-4 w-4 mr-2" />
          {isExporting ? 'Exporting...' : 'Export'}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem 
          onClick={() => handleExportClick('excel')}
          disabled={isExporting}
        >
          <FileSpreadsheet className="h-4 w-4 mr-2 text-green-600" />
          Export to Excel
        </DropdownMenuItem>
        <DropdownMenuItem 
          onClick={() => handleExportClick('pdf')}
          disabled={isExporting}
        >
          <FileText className="h-4 w-4 mr-2 text-red-600" />
          Export to PDF
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default ExportButton;