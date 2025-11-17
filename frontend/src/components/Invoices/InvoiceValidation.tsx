import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../services/api';

interface InvoiceValidationProps {
  documentId: string;
}

export const InvoiceValidation: React.FC<InvoiceValidationProps> = ({ documentId }) => {
  const queryClient = useQueryClient();

  // Fetch invoice data
  const { data: invoice, isLoading, error } = useQuery({
    queryKey: ['invoice', documentId],
    queryFn: () => apiClient.getInvoice(documentId),
  });

  // Fetch document for PDF preview
  const { data: document } = useQuery({
    queryKey: ['document', documentId],
    queryFn: () => apiClient.getDocument(documentId),
  });

  const [formData, setFormData] = useState<any>({});
  const [validationNotes, setValidationNotes] = useState('');

  // Update form when invoice loads
  React.useEffect(() => {
    if (invoice) {
      setFormData({
        vendor_name: invoice.vendor_name || '',
        vendor_tax_id: invoice.vendor_tax_id || '',
        invoice_number: invoice.invoice_number || '',
        invoice_date: invoice.invoice_date || '',
        due_date: invoice.due_date || '',
        subtotal: invoice.subtotal || 0,
        tax_amount: invoice.tax_amount || 0,
        total_amount: invoice.total_amount || 0,
        currency: invoice.currency || 'EUR',
      });
    }
  }, [invoice]);

  // Validation mutation
  const validateMutation = useMutation({
    mutationFn: (data: any) => apiClient.validateInvoice(documentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoice', documentId] });
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      alert('Invoice validated successfully!');
    },
  });

  const handleFieldChange = (field: string, value: any) => {
    setFormData({ ...formData, [field]: value });
  };

  const handleValidate = () => {
    // Calculate corrections (only fields that changed)
    const corrections: any = {};
    if (invoice) {
      Object.keys(formData).forEach((key) => {
        if (formData[key] !== invoice[key]) {
          corrections[key] = formData[key];
        }
      });
    }

    validateMutation.mutate({
      corrections,
      validation_notes: validationNotes,
      is_approved: true,
    });
  };

  if (isLoading) {
    return <div className="text-center py-8">Loading invoice data...</div>;
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded">
        Failed to load invoice data
      </div>
    );
  }

  if (!invoice) {
    return <div>Invoice data not available yet. Processing may still be in progress.</div>;
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* PDF Preview */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium mb-4">Document Preview</h3>
        {document?.gcs_path && (
          <div className="border border-gray-300 rounded h-[800px] bg-gray-100 flex items-center justify-center">
            <p className="text-gray-500">PDF Preview (requires signed URL from backend)</p>
          </div>
        )}
      </div>

      {/* Validation Form */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">Invoice Data</h3>
          {invoice.is_validated ? (
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
              Validated ✓
            </span>
          ) : (
            <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
              Needs Review
            </span>
          )}
        </div>

        <div className="space-y-4">
          {/* Vendor Information */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Vendor Name</label>
            <input
              type="text"
              value={formData.vendor_name}
              onChange={(e) => handleFieldChange('vendor_name', e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Vendor Tax ID</label>
            <input
              type="text"
              value={formData.vendor_tax_id}
              onChange={(e) => handleFieldChange('vendor_tax_id', e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            />
          </div>

          {/* Invoice Details */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Invoice Number</label>
              <input
                type="text"
                value={formData.invoice_number}
                onChange={(e) => handleFieldChange('invoice_number', e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Currency</label>
              <select
                value={formData.currency}
                onChange={(e) => handleFieldChange('currency', e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              >
                <option value="EUR">EUR (€)</option>
                <option value="RON">RON (lei)</option>
                <option value="USD">USD ($)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Invoice Date</label>
              <input
                type="date"
                value={formData.invoice_date}
                onChange={(e) => handleFieldChange('invoice_date', e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Due Date</label>
              <input
                type="date"
                value={formData.due_date}
                onChange={(e) => handleFieldChange('due_date', e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>
          </div>

          {/* Amounts */}
          <div className="border-t pt-4">
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Subtotal</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.subtotal}
                    onChange={(e) => handleFieldChange('subtotal', parseFloat(e.target.value))}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Tax Amount</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.tax_amount}
                    onChange={(e) => handleFieldChange('tax_amount', parseFloat(e.target.value))}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Total Amount</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.total_amount}
                  onChange={(e) => handleFieldChange('total_amount', parseFloat(e.target.value))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm text-lg font-bold"
                />
              </div>
            </div>
          </div>

          {/* Validation Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Validation Notes</label>
            <textarea
              value={validationNotes}
              onChange={(e) => setValidationNotes(e.target.value)}
              rows={3}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              placeholder="Add any notes about corrections made..."
            />
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-3 pt-4">
            <button
              onClick={handleValidate}
              disabled={invoice.is_validated || validateMutation.isPending}
              className="flex-1 bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md font-medium disabled:opacity-50"
            >
              {validateMutation.isPending ? 'Validating...' : 'Validate & Approve'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
