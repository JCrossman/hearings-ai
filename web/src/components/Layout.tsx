import { ReactNode } from 'react';
import { DemoRole, DEMO_ROLES } from '../types';
import { setCurrentRole } from '../api/client';

interface LayoutProps {
  children: ReactNode;
  currentRole: DemoRole;
  onRoleChange: (role: DemoRole) => void;
}

export default function Layout({ children, currentRole, onRoleChange }: LayoutProps) {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-aer-blue text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo and Title */}
            <div className="flex items-center gap-3">
              <div className="flex-shrink-0">
                <svg className="h-8 w-8" viewBox="0 0 32 32" fill="currentColor">
                  <rect x="2" y="6" width="28" height="20" rx="2" fill="none" stroke="currentColor" strokeWidth="2"/>
                  <path d="M8 14h16M8 18h12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold">Hearings AI</h1>
              </div>
            </div>

            {/* Role Switcher */}
            <div className="flex items-center gap-4">
              <span className="text-sm text-blue-200">Demo Mode:</span>
              <RoleSwitcher currentRole={currentRole} onRoleChange={onRoleChange} />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 bg-gray-50">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-aer-blue text-white py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-blue-200">
          <p>Hearings AI POC</p>
        </div>
      </footer>
    </div>
  );
}

interface RoleSwitcherProps {
  currentRole: DemoRole;
  onRoleChange: (role: DemoRole) => void;
}

function RoleSwitcher({ currentRole, onRoleChange }: RoleSwitcherProps) {
  const roleInfo = DEMO_ROLES.find(r => r.id === currentRole)!;

  return (
    <div className="relative">
      <select
        value={currentRole}
        onChange={(e) => {
          const newRole = e.target.value as DemoRole;
          setCurrentRole(newRole);
          onRoleChange(newRole);
        }}
        className={`px-3 py-1.5 rounded-md text-sm font-medium cursor-pointer border-0 focus:ring-2 focus:ring-white ${roleInfo.color}`}
        aria-label="Select demo role"
      >
        {DEMO_ROLES.map((role) => (
          <option key={role.id} value={role.id}>
            {role.name}
          </option>
        ))}
      </select>
    </div>
  );
}
