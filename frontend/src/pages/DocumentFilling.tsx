import React from 'react';
import { DocumentFillingForm } from '../components/Filling/DocumentFillingForm';

export const DocumentFilling: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto py-8">
      <h2 className="text-2xl font-bold mb-6">Automatic Document Filling</h2>

      <div className="mb-6 bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium mb-2">What is Document Filling?</h3>
        <p className="text-gray-700 mb-4">
          Automatically extract data from identity documents (ID cards, passports) and use that
          information to fill out PDF forms. No manual typing required!
        </p>

        <h4 className="font-medium mb-2">Supported Documents:</h4>
        <ul className="list-disc list-inside text-gray-700 space-y-1">
          <li>Romanian ID Cards (Carte de Identitate)</li>
          <li>EU Identity Cards</li>
          <li>Passports</li>
        </ul>
      </div>

      <DocumentFillingForm />
    </div>
  );
};
