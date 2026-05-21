import { useState, useRef, useEffect } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import ConfirmModal from './ConfirmModal.jsx';

//nav bar
export default function Header() {
  const { user, logout, deleteAccount, updateUsername } = useAuth();
  const navigate = useNavigate();
  const [modal, setModal] = useState(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [usernameError, setUsernameError] = useState(null);
  const [usernameLoading, setUsernameLoading] = useState(false);
  const settingsRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (settingsRef.current && !settingsRef.current.contains(e.target)) {
        setSettingsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  //logout
  async function handleLogoutConfirm() {
    setModal(null);
    await logout();
    navigate('/login');
  }

  //delete account
  async function handleDeleteConfirm() {
    setModal(null);
    await deleteAccount();
    navigate('/');
  }

  //change username
  function openUsernameModal() {
    setSettingsOpen(false);
    setNewUsername(user.username);
    setUsernameError(null);
    setModal('username');
  }

  //change username submit
  async function handleUsernameSubmit(e) {
    e.preventDefault();
    if (newUsername === user.username) { setModal(null); return; }
    setUsernameError(null);
    setUsernameLoading(true);
    try {
      await updateUsername(newUsername);
      setModal(null);
    } catch (err) {
      setUsernameError(err.message || 'Guncellenemedi');
    } finally {
      setUsernameLoading(false);
    }
  }

  return (
    <>
      <nav className="nav">
        <Link to="/" className="nav-brand">NeuroScan</Link>

        {user && (
          <div className="nav-user-area" ref={settingsRef}>
            <span className="nav-user-label">👤 {user.username}</span>
          <div className="nav-settings-wrap">
            <button
              className="nav-settings-btn"
              onClick={() => setSettingsOpen(o => !o)}
              aria-label="Settings"
              title="Settings"
            >
              ⚙️
            </button>

            {settingsOpen && (
              <div className="settings-popup">
                <div className="settings-popup-divider" />
                <NavLink
                  to="/scan"
                  className={({ isActive }) =>
                    'settings-popup-item' + (isActive ? ' settings-popup-active' : '')
                  }
                  onClick={() => setSettingsOpen(false)}
                >
                  New Scan
                </NavLink>
                <NavLink
                  to="/history"
                  className={({ isActive }) =>
                    'settings-popup-item' + (isActive ? ' settings-popup-active' : '')
                  }
                  onClick={() => setSettingsOpen(false)}
                >
                  History
                </NavLink>
                <div className="settings-popup-divider" />
                <button className="settings-popup-item" onClick={openUsernameModal}>
                  Change Username
                </button>
                <button
                  className="settings-popup-item"
                  onClick={() => { setSettingsOpen(false); setModal('logout'); }}
                >
                  Logout
                </button>
                <button
                  className="settings-popup-item settings-popup-danger"
                  onClick={() => { setSettingsOpen(false); setModal('delete'); }}
                >
                  Delete Account
                </button>
              </div>
            )}
          </div>
          </div>
        )}
      </nav>

      {modal === 'logout' && (
        <ConfirmModal
          title="Çıkış Yap"
          message="Hesabınızdan çıkmak istediğinizden emin misiniz?"
          confirmText="Çıkış Yap"
          danger
          onConfirm={handleLogoutConfirm}
          onCancel={() => setModal(null)}
        />
      )}

      {modal === 'delete' && (
        <ConfirmModal
          title="Hesabı Sil"
          message={`"${user.username}" hesabını kalıcı olarak silmek istediğinizden emin misiniz? Tüm scan geçmişiniz de silinecek. Bu işlem geri alınamaz.`}
          confirmText="Hesabı Sil"
          danger
          onConfirm={handleDeleteConfirm}
          onCancel={() => setModal(null)}
        />
      )}

      {modal === 'username' && (
        <div className="modal-overlay" onClick={() => setModal(null)}>
          <div className="modal card" onClick={(e) => e.stopPropagation()}>
            <h2 className="modal-title">Kullanıcı Adını Değiştir</h2>
            <form onSubmit={handleUsernameSubmit}>
              <input
                className="username-input"
                type="text"
                value={newUsername}
                onChange={(e) => setNewUsername(e.target.value)}
                minLength={3}
                maxLength={30}
                pattern="[a-zA-Z0-9_]+"
                required
                autoFocus
                disabled={usernameLoading}
              />
              {usernameError && (
                <p className="username-error">{usernameError}</p>
              )}
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setModal(null)}>İptal</button>
                <button type="submit" className="btn btn-primary" disabled={usernameLoading}>
                  {usernameLoading ? <><span className="spinner"></span>Kaydediliyor...</> : 'Kaydet'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
