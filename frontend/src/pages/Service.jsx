import { useState } from 'react';
import { DocumentTextIcon, UserGroupIcon, BuildingOfficeIcon } from '@heroicons/react/24/solid';
import { ChevronDownIcon } from '@heroicons/react/24/outline';
import ObjectListPage from '../components/ObjectListPage';
import ImportModal from '../components/ImportModal';
import AssignLabelModal from '../components/AssignLabelModal';
import { casesAPI, contactsAPI, accountsAPI } from '../services/api';
import toast from 'react-hot-toast';

const subNavItems = [
  { key: 'cases', label: 'Cases' },
  { key: 'contacts', label: 'Contacts' },
  { key: 'accounts', label: 'Accounts' },
  { key: 'quicktext', label: 'Quick Text' },
  { key: 'analytics', label: 'Analytics' },
  { key: 'knowledge', label: 'Knowledge' },
];

const caseColumns = [
  { key: 'case_number', label: 'Case Number' },
  { key: 'subject', label: 'Subject' },
  {
    key: 'priority',
    label: 'Priority',
    render: (item) => (
      <span className={`px-2 py-1 rounded text-xs font-medium ${
        item.priority === 'Critical' ? 'bg-red-100 text-red-800' :
        item.priority === 'High' ? 'bg-orange-100 text-orange-800' :
        item.priority === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
        'bg-green-100 text-green-800'
      }`}>
        {item.priority}
      </span>
    ),
  },
  {
    key: 'status',
    label: 'Status',
    render: (item) => (
      <span className={`px-2 py-1 rounded text-xs font-medium ${
        item.status === 'Escalated' ? 'bg-red-100 text-red-800' :
        item.status === 'Closed' ? 'bg-gray-100 text-gray-800' :
        item.status === 'Working' ? 'bg-blue-100 text-blue-800' :
        'bg-green-100 text-green-800'
      }`}>
        {item.status}
      </span>
    ),
  },
  {
    key: 'created_at',
    label: 'Date/Time Opened',
    render: (item) => new Date(item.created_at).toLocaleString(),
  },
  { key: 'owner_alias', label: 'Case Owner Alias' },
];

const contactColumns = [
  {
    key: 'full_name',
    label: 'Name',
    render: (item) => item.full_name || `${item.first_name || ''} ${item.last_name}`.trim(),
  },
  { key: 'account_name', label: 'Account Name' },
  { key: 'phone', label: 'Phone' },
  { key: 'email', label: 'Email' },
  { key: 'owner_alias', label: 'Contact Owner Alias' },
];

const accountColumns = [
  { key: 'name', label: 'Account Name' },
  { key: 'phone', label: 'Phone' },
  { key: 'industry', label: 'Industry' },
  { key: 'owner_alias', label: 'Account Owner Alias' },
];

export default function Service() {
  const [activeTab, setActiveTab] = useState('cases');
  const [showImportModal, setShowImportModal] = useState(false);
  const [showLabelModal, setShowLabelModal] = useState(false);
  const [selectedRecords, setSelectedRecords] = useState([]);
  const [importObjectType, setImportObjectType] = useState('case');

  const handleImport = (objectType) => {
    setImportObjectType(objectType);
    setShowImportModal(true);
  };

  const handleChangeOwner = (selectedIds) => {
    if (selectedIds.length === 0) {
      toast.error('Please select at least one record');
      return;
    }
    toast.success(`Change owner for ${selectedIds.length} record(s)`);
  };

  const handleMergeCases = (selectedIds) => {
    if (selectedIds.length < 2) {
      toast.error('Please select at least 2 cases to merge');
      return;
    }
    // In a real app, this would open a merge modal to select master case
    const confirmMerge = window.confirm(
      `Merge ${selectedIds.length} cases? The first selected case will be the master.`
    );
    if (confirmMerge) {
      casesAPI.merge(selectedIds, selectedIds[0])
        .then(() => {
          toast.success('Cases merged successfully');
          window.location.reload();
        })
        .catch(() => {
          toast.error('Failed to merge cases');
        });
    }
  };

  const handleEscalate = async (selectedIds) => {
    if (selectedIds.length === 0) {
      toast.error('Please select at least one case');
      return;
    }
    try {
      for (const id of selectedIds) {
        await casesAPI.escalate(id);
      }
      toast.success(`Escalated ${selectedIds.length} case(s)`);
      window.location.reload();
    } catch (error) {
      toast.error('Failed to escalate cases');
    }
  };

  const handleAssignLabel = (selectedIds, records) => {
    if (selectedIds.length === 0) {
      toast.error('Please select at least one record');
      return;
    }
    setSelectedRecords(records);
    setShowLabelModal(true);
  };

  const handleImportSuccess = () => {
    window.location.reload();
  };

  const getImportApi = () => {
    switch (importObjectType) {
      case 'case': return casesAPI;
      case 'contact': return contactsAPI;
      case 'account': return accountsAPI;
      default: return casesAPI;
    }
  };

  const caseActions = [
    { label: 'Change Owner', onClick: handleChangeOwner, requiresSelection: true },
    { label: 'Merge Cases', onClick: handleMergeCases, requiresSelection: true },
    { label: 'Escalate', onClick: handleEscalate, requiresSelection: true },
    { label: 'Assign Label', onClick: handleAssignLabel, requiresSelection: true },
  ];

  const contactActions = [
    { label: 'Import', onClick: () => handleImport('contact') },
    { label: 'Assign Label', onClick: handleAssignLabel, requiresSelection: true },
  ];

  const accountActions = [
    { label: 'Import', onClick: () => handleImport('account') },
    { label: 'Assign Label', onClick: handleAssignLabel, requiresSelection: true },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'cases':
        return (
          <ObjectListPage
            objectType="case"
            objectLabel="Case"
            columns={caseColumns}
            api={casesAPI}
            actions={caseActions}
            icon={<DocumentTextIcon className="w-5 h-5 text-white" />}
            iconColor="bg-pink-500"
            emptyTitle="Track customer support in one place"
            emptyDescription="Cases bring together customer questions, feedback, and issues from any channel."
            onSelectionChange={(ids, records) => setSelectedRecords(records)}
          />
        );
      case 'contacts':
        return (
          <ObjectListPage
            objectType="contact"
            objectLabel="Contact"
            columns={contactColumns}
            api={contactsAPI}
            actions={contactActions}
            icon={<UserGroupIcon className="w-5 h-5 text-white" />}
            iconColor="bg-purple-500"
            emptyTitle="Top sellers add their contacts first"
            emptyDescription="It's the fastest way to win more deals."
            onSelectionChange={(ids, records) => setSelectedRecords(records)}
          />
        );
      case 'accounts':
        return (
          <ObjectListPage
            objectType="account"
            objectLabel="Account"
            columns={accountColumns}
            api={accountsAPI}
            actions={accountActions}
            icon={<BuildingOfficeIcon className="w-5 h-5 text-white" />}
            iconColor="bg-indigo-500"
            emptyTitle="Accounts show where your contacts work"
            emptyDescription="Improve your reporting and deal tracking with accounts."
            onSelectionChange={(ids, records) => setSelectedRecords(records)}
          />
        );
      default:
        return (
          <div className="p-6">
            <div className="card p-12 text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Coming Soon</h3>
              <p className="text-gray-500">This feature is under development.</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div>
      {/* Page Header */}
      <div className="px-6 pt-6 pb-0">
        <h1 className="text-2xl font-bold text-gray-900">Service</h1>
        <div className="mt-2 border-b border-gray-200">
          <nav className="-mb-px flex space-x-6 overflow-x-auto">
            {subNavItems.map((item) => (
              <button
                type="button"
                key={item.key}
                onClick={() => setActiveTab(item.key)}
                className={`py-2 px-1 text-sm font-medium whitespace-nowrap flex items-center ${
                  activeTab === item.key
                    ? 'border-b-2 border-sf-blue-500 text-sf-blue-500'
                    : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {item.label}
                <ChevronDownIcon className="w-3 h-3 ml-1" />
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      {renderContent()}

      {/* Import Modal */}
      <ImportModal
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        objectType={importObjectType}
        api={getImportApi()}
        onSuccess={handleImportSuccess}
      />

      {/* Assign Label Modal */}
      <AssignLabelModal
        isOpen={showLabelModal}
        onClose={() => setShowLabelModal(false)}
        selectedCount={selectedRecords.length}
        onAssign={(labels) => {
          console.log('Assigned labels:', labels);
        }}
      />
    </div>
  );
}
