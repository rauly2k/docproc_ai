import React from 'react';
import { DocumentFillingForm } from '../components/Filling/DocumentFillingForm';

export const DocumentFilling: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Automatic Document Filling</h1>
        <p className="text-gray-600 mb-8">
          Extract data from ID cards and automatically fill PDF forms
        </p>

        {/* Info Section */}
        <div className="mb-6 bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-medium mb-2">What is Document Filling?</h2>
          <p className="text-gray-700 mb-4">
            Automatically extract data from identity documents (ID cards, passports) and use that
            information to fill out PDF forms. No manual typing required!
          </p>

          <h3 className="font-medium mb-2">Supported Documents:</h3>
          <ul className="list-disc list-inside text-gray-700 space-y-1">
            <li>Romanian ID Cards (Carte de Identitate)</li>
            <li>EU Identity Cards</li>
            <li>Passports</li>
          </ul>
        </div>

        {/* Form */}
        <DocumentFillingForm />

        {/* Additional Info */}
        <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <h4 className="text-sm font-medium text-yellow-900 mb-2">💡 Tips:</h4>
          <ul className="text-sm text-yellow-800 space-y-1 list-disc list-inside">
            <li>Make sure your ID document image is clear and well-lit</li>
            <li>Upload your ID document with document type set to "id"</li>
            <li>The extraction process may take 10-30 seconds</li>
            <li>Review the filled PDF before submitting it officially</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
