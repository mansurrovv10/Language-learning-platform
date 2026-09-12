"use client"
import React, { useState } from 'react';
import './Progress.css';

export function Progress() {
  // Статистика пользователя по ТЗ
  const [streak] = useState(5);
  const [xp] = useState(350);

  // Список пройденных и текущих уроков
  const [completedLessons] = useState([
    { id: 1, title: 'Урок 1: Знакомство', score: 100, date: '10.05.2026' },
    { id: 2, title: 'Урок 2: Еда', score: 85, date: '11.05.2026' },
  ]);

  return (
    <div className="progress-container">
      {/* Шапка */}
      <div className="progress-header">
        <h1>Мой прогресс</h1>
      </div>

      {/* Карточки с общей статистикой */}
      <div className="stats-grid">
        <div className="stat-card">
          <span className="icon">🔥</span>
          <div className="stat-value">{streak} дней</div>
          <div className="stat-label">Текущий Streak</div>
        </div>

        <div className="stat-card">
          <span className="icon">⭐</span>
          <div className="stat-value">{xp} XP</div>
          <div className="stat-label">Всего очков</div>
        </div>

        <div className="stat-card">
          <span className="icon">📚</span>
          <div className="stat-value">{completedLessons.length}</div>
          <div className="stat-label">Пройдено уроков</div>
        </div>
      </div>

      {/* Прогресс-бар до следующего уровня */}
      <div className="level-section">
        <div className="level-info">
          <span>Уровень 3</span>
          <span>350 / 500 XP</span>
        </div>
        <div className="bar-bg">
          <div className="bar-fill" style={{ width: '70%' }}></div>
        </div>
      </div>

      {/* История выполнения уроков */}
      <div className="history-section">
        <h2>История уроков</h2>
        <div className="history-list">
          {completedLessons.map((item) => (
            <div key={item.id} className="history-item">
              <div>
                <div className="item-title">{item.title}</div>
                <div className="item-date">{item.date}</div>
              </div>
              <div className="item-score">+{item.score} XP</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Progress;