"use client";
import React, { useState } from 'react';
import './chat.css';

interface ChatItem {
  id: string;
  name: string;
  type: 'private' | 'group';
  lang?: string;
  isOnline?: boolean;
}

interface Message {
  id: string;
  sender: string;
  text: string;
  time: string;
  isMe: boolean;
}

export function Chat() {
  const [chats] = useState<ChatItem[]>([
    { id: '1', name: 'English Practice', type: 'group', lang: 'EN' },
    { id: '2', name: 'Alex Johnson', type: 'private', isOnline: true },
    { id: '3', name: 'Español Chat', type: 'group', lang: 'ES' },
    { id: '4', name: 'Maria Garcia', type: 'private', isOnline: false },
  ]);

  const [activeChat, setActiveChat] = useState<ChatItem>(chats[0]);
  const [inputText, setInputText] = useState('');
  
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', sender: 'Alex', text: 'Hello everyone! How is your English practice today?', time: '14:20', isMe: false },
    { id: '2', sender: 'Вы', text: 'Hi! I just finished my daily lesson.', time: '14:22', isMe: true },
  ]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      sender: 'Вы',
      text: inputText,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isMe: true,
    };

    setMessages([...messages, newMessage]);
    setInputText('');
  };

  return (
    <div className="chat-page">
      <div className="chat-sidebar">
        <div className="sidebar-title">
          <h2>Чаты</h2>
        </div>

        <div className="chat-list">
          {chats.map((chat) => (
            <div
              key={chat.id}
              className={activeChat.id === chat.id ? 'chat-item active' : 'chat-item'}
              onClick={() => setActiveChat(chat)}
            >
              <div className="avatar-box">
                {chat.type === 'group' ? '💬' : '👤'}
                {chat.type === 'private' && (
                  <span className={chat.isOnline ? 'dot online' : 'dot'} />
                )}
              </div>

              <div className="chat-meta">
                <div className="name-row">
                  <span className="chat-name">{chat.name}</span>
                  {chat.lang && <span className="lang-badge">{chat.lang}</span>}
                </div>
                <span className="chat-sub">
                  {chat.type === 'group' ? 'Групповой чат' : chat.isOnline ? 'В сети' : 'Не в сети'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="chat-main">
        <div className="chat-top">
          <h3>{activeChat.name}</h3>
          <span>{activeChat.type === 'group' ? 'Языковой чат' : activeChat.isOnline ? 'В сети' : 'Был(а) недавно'}</span>
        </div>

        <div className="messages-container">
          {messages.map((msg) => (
            <div key={msg.id} className={msg.isMe ? 'msg-row me' : 'msg-row'}>
              <div className="msg-bubble">
                {!msg.isMe && <div className="msg-sender">{msg.sender}</div>}
                <div className="msg-text">{msg.text}</div>
                <div className="msg-time">{msg.time}</div>
              </div>
            </div>
          ))}
        </div>

        <form className="chat-form" onSubmit={handleSend}>
          <input
            type="text"
            placeholder="Напишите сообщение..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
          />
          <button type="submit">Отправить</button>
        </form>
      </div>
    </div>
  );
}

export default Chat;