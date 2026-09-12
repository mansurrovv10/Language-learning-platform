"use client";
import React, { useState } from "react";
import "./home.css";


export function Home() {
  const [streak] = useState(5);
  const [xp] = useState(350);
  const [selectedLang, setSelectedLang] = useState("en");

  return (
    <div className="home-page">
      <div className="top-bar">
        <h1>Курсы и Уроки</h1>

        <div className="top-right">
          <div className="badge streak-badge">🔥 {streak} дней</div>
          <div className="badge xp-badge">⭐ {xp} XP</div>
          <div className="user-avatar" onClick={() => (window.location.href = "/profile")}>
            👤
          </div>
        </div>
      </div>

      <div className="block">
        <h2 className="block-title">Изучаемый язык</h2>
        <div className="lang-buttons">
          <button
            className={selectedLang === "en" ? "lang-btn active" : "lang-btn"}
            onClick={() => setSelectedLang("en")}
          >
            🇬🇧 Английский
          </button>
          <button
            className={selectedLang === "es" ? "lang-btn active" : "lang-btn"}
            onClick={() => setSelectedLang("es")}
          >
            🇪🇸 Испанский
          </button>
        </div>
      </div>

      <div className="block">
        <h2 className="block-title">Текущий курс</h2>
        <div className="course-card">
          <div className="course-header">
            <h3>Базовый английский</h3>
            <span className="level-tag">A1</span>
          </div>
          <p>
            Основная грамматика, базовые слова и простые диалоги на каждый день.
          </p>
        </div>
      </div>

      <div className="block">
        <h2 className="block-title">Уроки</h2>
        <div className="lessons-list">
          <div className="lesson-card">
            <div className="lesson-info">
              <span className="lesson-icon">🎯</span>
              <div>
                <div className="lesson-name">Урок 1: Знакомство</div>
                <div className="lesson-reward">+15 XP</div>
              </div>
            </div>
            <button className="btn btn-green">Начать</button>
          </div>

          <div className="lesson-card">
            <div className="lesson-info">
              <span className="lesson-icon">🎯</span>
              <div>
                <div className="lesson-name">Урок 2: Еда и напитки</div>
                <div className="lesson-reward">+20 XP</div>
              </div>
            </div>
            <button className="btn btn-green">Начать</button>
          </div>

          <div className="lesson-card disabled">
            <div className="lesson-info">
              <span className="lesson-icon">🔒</span>
              <div>
                <div className="lesson-name">Урок 3: В городе</div>
                <div className="lesson-reward">+25 XP</div>
              </div>
            </div>
            <button className="btn btn-gray" disabled>
              Закрыто
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;
