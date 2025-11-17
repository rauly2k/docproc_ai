import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import { InvoiceValidation } from '../components/Invoices/InvoiceValidation';

export const Invoices: React.FC = () => {
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null);

  const { data: invoices, isLoading } = useQuery({
    queryKey: ['invoices'],
    queryFn: () => apiClient.listInvoices(),
  });

  if (selectedInvoiceId) {
    return (
      <div>
        <button
          onClick={() => setSelectedInvoiceId(null)}
          className="mb-4 text-primary-600 hover:text-primary-800 flex items-center"
        >
          ← Back to list
        </button>
        <InvoiceValidation documentId={selectedInvoiceId} />
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Invoices</h2>

      {isLoading ? (
        <div className="text-center py-8">Loading invoices...</div>
      ) : invoices?.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No invoices yet. Upload an invoice to get started.
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {invoices?.map((invoice: any) => (
              <li key={invoice.id}>
                <div className="px-4 py-4 flex items-center sm:px-6 hover:bg-gray-50">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-primary-600 truncate">
                        {invoice.vendor_name || 'Unknown Vendor'}
                      </p>
                      {invoice.is_validated ? (
                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                          Validated
                        </span>
                      ) : (
                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">
                          Needs Review
                        </span>
                      )}
                    </div>
                    <div className="mt-2 flex">
                      <div className="flex items-center text-sm text-gray-500">
                        <span>Invoice #{invoice.invoice_number}</span>
                        <span className="mx-2">•</span>
                        <span>
                          {invoice.total_amount} {invoice.currency}
                        </span>
                        <span className="mx-2">•</span>
                        <span>{new Date(invoice.invoice_date).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                  <div>
                    <button
                      onClick={() => setSelectedInvoiceId(invoice.document_id)}
                      className="ml-4 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                      {invoice.is_validated ? 'View' : 'Review'}
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
