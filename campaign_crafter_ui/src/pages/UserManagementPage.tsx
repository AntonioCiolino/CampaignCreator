import React, { useState, useEffect } from 'react';
import { User, getUsers, deleteUser, createUser, updateUser, UserCreatePayload, UserUpdatePayload } from '../services/userService';
// import { Link } from 'react-router-dom';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal'; // Added Modal import
import UserForm from '../components/UserForm'; // Added UserForm import
import './UserManagementPage.css';

const UserManagementPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [userFormError, setUserFormError] = useState<string | null>(null);

  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const fetchedUsers = await getUsers();
      setUsers(fetchedUsers);
    } catch (err) {
      console.error('Failed to fetch users:', err);
      setError('Failed to load users. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleOpenCreateModal = () => {
    setEditingUser(null);
    setUserFormError(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (user: User) => {
    setEditingUser(user);
    setUserFormError(null);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingUser(null);
    setUserFormError(null);
  };

  const handleUserFormSubmit = async (data: UserCreatePayload | UserUpdatePayload, isEditing: boolean) => {
    setUserFormError(null);
    try {
      if (isEditing && editingUser) {
        await updateUser(editingUser.id, data as UserUpdatePayload);
        alert('User updated successfully!');
      } else {
        await createUser(data as UserCreatePayload);
        alert('User created successfully!');
      }
      handleCloseModal();
      fetchUsers();
    } catch (err: any) {
      console.error('Error submitting user form:', err);
      const errorMessage = err.response?.data?.detail || (err.message || 'An unexpected error occurred.');
      setUserFormError(errorMessage);
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await deleteUser(userId);
        fetchUsers();
        alert('User deleted successfully!');
      } catch (err: any) {
        console.error(`Failed to delete user ${userId}:`, err);
        const deleteErrorMessage = err.response?.data?.detail || (err.message || `Failed to delete user ${userId}.`);
        setError(deleteErrorMessage); // Display this error more prominently on the page
      }
    }
  };

  if (isLoading) {
    return <div className="container"><p>Loading users...</p></div>;
  }

  // Display general page error first if it exists
  if (error && !isModalOpen) { // Only show page-level error if modal isn't open (modal has its own error display)
    return <div className="container error-message" style={{ textAlign: 'center' }}>{error}</div>;
  }

  return (
    <div className="user-management-page container">
      <h1>User Management</h1>

      <div className="page-actions">
        <Button onClick={handleOpenCreateModal} variant="primary">
          Create New User
        </Button>
      </div>

      {/* Display general page error here if not critical enough to block rendering table */}
      {error && !isModalOpen && (
         <div className="error-message page-error" style={{ marginBottom: '15px', textAlign: 'center' }}>{error}</div>
      )}


      {users.length === 0 && !isLoading ? (
        <p>No users found. Click "Create New User" to add one.</p>
      ) : (
        <table className="users-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Email</th>
              <th>Full Name</th>
              <th>Active</th>
              <th>Superuser</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.id}</td>
                <td>{user.email}</td>
                <td>{user.full_name || 'N/A'}</td>
                <td>{user.is_active ? 'Yes' : 'No'}</td>
                <td>{user.is_superuser ? 'Yes' : 'No'}</td>
                <td className="user-actions">
                  <Button onClick={() => handleOpenEditModal(user)} variant="secondary" size="sm">
                    Edit
                  </Button>
                  <Button onClick={() => handleDeleteUser(user.id)} variant="danger" size="sm" style={{ marginLeft: '5px' }}>
                    Delete
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {isModalOpen && (
        <Modal
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          title={editingUser ? 'Edit User' : 'Create New User'}
        >
          <UserForm
            userToEdit={editingUser}
            onSubmit={handleUserFormSubmit}
            onCancel={handleCloseModal}
            formError={userFormError}
          />
        </Modal>
      )}
    </div>
  );
};

export default UserManagementPage;
