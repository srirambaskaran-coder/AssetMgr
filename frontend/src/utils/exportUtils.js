import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import { saveAs } from 'file-saver';

// Utility function to format date for filename
const formatDateForFilename = () => {
  const now = new Date();
  return now.toISOString().slice(0, 19).replace(/[:.]/g, '-');
};

// Utility function to format currency for display
const formatCurrency = (value) => {
  if (!value && value !== 0) return '-';
  return `₹${value.toLocaleString()}`;
};

// Utility function to format date for display
const formatDate = (dateString) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString();
};

// Export to Excel
export const exportToExcel = (data, filename, columns = null) => {
  try {
    // Create workbook
    const workbook = XLSX.utils.book_new();
    
    // Prepare data for Excel
    let excelData;
    if (columns) {
      // Use specified columns to format data
      excelData = data.map(item => {
        const row = {};
        columns.forEach(col => {
          let value = item[col.key];
          
          // Apply formatting based on column type
          if (col.type === 'currency' && value !== null && value !== undefined) {
            value = parseFloat(value) || 0;
          } else if (col.type === 'date' && value) {
            value = formatDate(value);
          } else if (col.type === 'array' && Array.isArray(value)) {
            value = value.join(', ');
          } else if (value === null || value === undefined) {
            value = '-';
          }
          
          row[col.header] = value;
        });
        return row;
      });
    } else {
      // Use data as-is
      excelData = data;
    }
    
    // Create worksheet
    const worksheet = XLSX.utils.json_to_sheet(excelData);
    
    // Auto-size columns
    const colWidths = [];
    if (columns) {
      columns.forEach(col => {
        const maxLength = Math.max(
          col.header.length,
          ...data.map(row => String(row[col.key] || '').length)
        );
        colWidths.push({ wch: Math.min(maxLength + 2, 50) });
      });
    }
    worksheet['!cols'] = colWidths;
    
    // Add worksheet to workbook
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Data');
    
    // Generate Excel file
    const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    
    // Save file
    const timestamp = formatDateForFilename();
    saveAs(blob, `${filename}_${timestamp}.xlsx`);
    
    return true;
  } catch (error) {
    console.error('Error exporting to Excel:', error);
    return false;
  }
};

// Export to PDF
export const exportToPDF = (data, filename, columns, title = '') => {
  try {
    // Create PDF document
    const doc = new jsPDF('landscape'); // Use landscape for better table display
    
    // Add title
    if (title) {
      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text(title, 14, 20);
    }
    
    // Add timestamp
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text(`Generated on: ${new Date().toLocaleString()}`, 14, title ? 30 : 20);
    
    // Prepare table data
    const headers = columns.map(col => col.header);
    const rows = data.map(item => {
      return columns.map(col => {
        let value = item[col.key];
        
        // Apply formatting based on column type
        if (col.type === 'currency' && value !== null && value !== undefined) {
          value = formatCurrency(value);
        } else if (col.type === 'date' && value) {
          value = formatDate(value);
        } else if (col.type === 'array' && Array.isArray(value)) {
          value = value.join(', ');
        } else if (value === null || value === undefined) {
          value = '-';
        } else {
          value = String(value);
        }
        
        return value;
      });
    });
    
    // Add table
    doc.autoTable({
      head: [headers],
      body: rows,
      startY: title ? 35 : 25,
      styles: {
        fontSize: 8,
        cellPadding: 2,
      },
      headStyles: {
        fillColor: [66, 139, 202],
        textColor: 255,
        fontStyle: 'bold',
      },
      alternateRowStyles: {
        fillColor: [245, 245, 245],
      },
      margin: { top: 10, right: 10, bottom: 10, left: 10 },
      didDrawPage: (data) => {
        // Add page numbers
        const pageNumber = doc.internal.getNumberOfPages();
        const pageSize = doc.internal.pageSize;
        doc.setFontSize(8);
        doc.text(
          `Page ${data.pageNumber} of ${pageNumber}`,
          pageSize.width - 30,
          pageSize.height - 10
        );
      },
    });
    
    // Save PDF
    const timestamp = formatDateForFilename();
    doc.save(`${filename}_${timestamp}.pdf`);
    
    return true;
  } catch (error) {
    console.error('Error exporting to PDF:', error);
    return false;
  }
};

// Export configurations for different data types
export const exportConfigs = {
  users: {
    filename: 'user_management',
    title: 'User Management Report',
    columns: [
      { key: 'name', header: 'Name', type: 'text' },
      { key: 'email', header: 'Email', type: 'text' },
      { key: 'roles', header: 'Roles', type: 'array' },
      { key: 'designation', header: 'Designation', type: 'text' },
      { key: 'location_name', header: 'Location', type: 'text' },
      { key: 'reporting_manager_name', header: 'Reporting Manager', type: 'text' },
      { key: 'date_of_joining', header: 'Date of Joining', type: 'date' },
      { key: 'is_active', header: 'Active', type: 'boolean' },
    ]
  },
  
  assetTypes: {
    filename: 'asset_types',
    title: 'Asset Types Report',
    columns: [
      { key: 'code', header: 'Code', type: 'text' },
      { key: 'name', header: 'Name', type: 'text' },
      { key: 'depreciation_applicable', header: 'Depreciation Applicable', type: 'boolean' },
      { key: 'asset_life', header: 'Asset Life (Years)', type: 'number' },
      { key: 'to_be_recovered_on_separation', header: 'Recovery Required', type: 'boolean' },
      { key: 'status', header: 'Status', type: 'text' },
      { key: 'created_at', header: 'Created Date', type: 'date' },
    ]
  },
  
  assetDefinitions: {
    filename: 'asset_definitions',
    title: 'Asset Definitions Report',
    columns: [
      { key: 'asset_code', header: 'Asset Code', type: 'text' },
      { key: 'asset_type_name', header: 'Asset Type', type: 'text' },
      { key: 'asset_description', header: 'Description', type: 'text' },
      { key: 'asset_value', header: 'Asset Value', type: 'currency' },
      { key: 'current_depreciation_value', header: 'Current Value', type: 'currency' },
      { key: 'status', header: 'Status', type: 'text' },
      { key: 'assigned_asset_manager_name', header: 'Asset Manager', type: 'text' },
      { key: 'location_name', header: 'Location', type: 'text' },
      { key: 'allocated_to_name', header: 'Allocated To', type: 'text' },
      { key: 'created_at', header: 'Created Date', type: 'date' },
    ]
  },
  
  assetRequisitions: {
    filename: 'asset_requisitions',
    title: 'Asset Requisitions Report',
    columns: [
      { key: 'id', header: 'Requisition ID', type: 'text' },
      { key: 'asset_type_name', header: 'Asset Type', type: 'text' },
      { key: 'request_type', header: 'Request Type', type: 'text' },
      { key: 'requested_for_name', header: 'Requested For', type: 'text' },
      { key: 'requested_by_name', header: 'Requested By', type: 'text' },
      { key: 'required_by_date', header: 'Required By', type: 'date' },
      { key: 'status', header: 'Status', type: 'text' },
      { key: 'assigned_to_name', header: 'Assigned To', type: 'text' },
      { key: 'routing_reason', header: 'Routing Reason', type: 'text' },
      { key: 'created_at', header: 'Request Date', type: 'date' },
    ]
  },
  
  assetAllocations: {
    filename: 'asset_allocations',
    title: 'Asset Allocations Report',
    columns: [
      { key: 'asset_definition_code', header: 'Asset Code', type: 'text' },
      { key: 'asset_type_name', header: 'Asset Type', type: 'text' },
      { key: 'request_type', header: 'Request Type', type: 'text' },
      { key: 'requested_for_name', header: 'Allocated To', type: 'text' },
      { key: 'allocated_by_name', header: 'Allocated By', type: 'text' },
      { key: 'allocated_date', header: 'Allocation Date', type: 'date' },
      { key: 'status', header: 'Status', type: 'text' },
      { key: 'remarks', header: 'Remarks', type: 'text' },
    ]
  },
  
  ndcRequests: {
    filename: 'ndc_requests',
    title: 'NDC Requests Report',
    columns: [
      { key: 'employee_name', header: 'Employee', type: 'text' },
      { key: 'employee_designation', header: 'Designation', type: 'text' },
      { key: 'location_name', header: 'Location', type: 'text' },
      { key: 'last_working_date', header: 'Last Working Date', type: 'date' },
      { key: 'separation_reason', header: 'Separation Reason', type: 'text' },
      { key: 'asset_manager_name', header: 'Asset Manager', type: 'text' },
      { key: 'status', header: 'Status', type: 'text' },
      { key: 'created_at', header: 'Created Date', type: 'date' },
    ]
  }
};

// Main export function that handles both Excel and PDF
export const handleExport = (data, type, format, customConfig = null) => {
  const config = customConfig || exportConfigs[type];
  if (!config) {
    console.error(`Export configuration not found for type: ${type}`);
    return false;
  }
  
  if (format === 'excel') {
    return exportToExcel(data, config.filename, config.columns);
  } else if (format === 'pdf') {
    return exportToPDF(data, config.filename, config.columns, config.title);
  }
  
  return false;
};