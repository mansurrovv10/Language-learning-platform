"ues client"
import React from 'react';
import './Profile.css';

interface ProfileProps {
  onBack?: () => void;
}

export function Profile({ onBack }: ProfileProps) {
  const user = {
    username: 'Элхан',
    email: 'elhan@example.com',
    role: 'User',
    streak: 5,
    xp: 350,
    created_at: '2026-05-10',
  };

  return (
    <div className="profile-container">
     

      <div className="profile-card">
        <div className="profile-avatar">👤</div>
        <h2>{user.username}</h2>
        <p className="email">{user.email}</p>
        <span className="role-badge">{user.role}</span>
      </div>

      <div className="profile-stats">
        <div className="stat-box">
          <h3>🔥 {user.streak} дней</h3>
          <p>Текущий Streak</p>
        </div>

        <div className="stat-box">
          <h3>⭐ {user.xp} XP</h3>
          <p>Всего очков</p>
        </div>
      </div>

      <div className="profile-info">
        <h3>Информация</h3>
        <p><b>Дата регистрации:</b> {user.created_at}</p>
        <p><b>Изучаемые языки:</b> Английский, Испанский</p>
      </div>

     
    </div>
  );
}

export default Profile;