import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from '../App';

const RoleContext = createContext();

export const useRole = () => {
  const context = useContext(RoleContext);
  if (!context) {
    throw new Error('useRole must be used within a RoleProvider');
  }
  return context;
};

export const RoleProvider = ({ children }) => {
  const { user } = useAuth();
  
  // Handle both old single role structure and new multi-role structure
  const userRoles = user?.roles || (user?.role ? [user.role] : ['Employee']);
  const [activeRole, setActiveRole] = useState(userRoles[0] || 'Employee');
  
  // Sync activeRole when user changes or roles change
  useEffect(() => {
    const currentUserRoles = user?.roles || (user?.role ? [user.role] : ['Employee']);
    // If activeRole is not in user's current roles, reset to first role
    if (!currentUserRoles.includes(activeRole)) {
      setActiveRole(currentUserRoles[0] || 'Employee');
    }
  }, [user, activeRole]);
  
  // Role hierarchy for determining accessible features
  const getRoleHierarchy = (role) => {
    switch (role) {
      case 'Administrator':
        return ['Administrator', 'HR Manager', 'Manager', 'Asset Manager', 'Employee'];
      case 'HR Manager':
        return ['HR Manager', 'Employee'];
      case 'Manager':
        return ['Manager', 'Employee'];
      case 'Asset Manager':
        return ['Asset Manager', 'Employee'];
      case 'Employee':
        return ['Employee'];
      default:
        return ['Employee'];
    }
  };
  
  const accessibleRoles = getRoleHierarchy(activeRole);
  
  const value = {
    userRoles,
    activeRole,
    setActiveRole,
    accessibleRoles,
    getRoleHierarchy
  };

  return (
    <RoleContext.Provider value={value}>
      {children}
    </RoleContext.Provider>
  );
};