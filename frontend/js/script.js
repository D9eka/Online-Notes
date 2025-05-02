const apiUrl = 'http://localhost:8000';
let currentUser = null;

// Общие функции
const handleFormSubmit = (formId, endpoint, successMessage, redirectPage) => {
  const form = document.getElementById(formId);
  if (!form) return;

  form.onsubmit = async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
      const response = await fetch(`${apiUrl}/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Something went wrong');

      alert(successMessage);
      if (redirectPage) {
        localStorage.setItem('username', username);
        localStorage.setItem('password', password);
        window.location.href = redirectPage;
      }
    } catch (error) {
      alert(error.message);
    }
  };
};

// Работа с пользователями
const loadUsers = async () => {
  try {
    const response = await fetch(`${apiUrl}/users`);
    const users = await response.json();
    
    const usersList = document.getElementById('usersList');
    if (usersList) {
      usersList.innerHTML = users.map(user => `
        <div class="user-item">
          <strong>ID:</strong> ${user.id}<br>
          <strong>Username:</strong> ${user.username}
        </div>
      `).join('');
    }
  } catch (error) {
    console.error('Error loading users:', error);
  }
};

// Работа с заметками
async function initNotes() {
  const username = localStorage.getItem('username');
  const password = localStorage.getItem('password');
  
  if (!username || !password) {
    window.location.href = 'index.html';
    return;
  }
  
  currentUser = { username, password };
  await loadNotes();
}

async function loadNotes() {
  try {
    const response = await fetch(`${apiUrl}/notes?username=${currentUser.username}&password=${currentUser.password}`);
    const notes = await response.json();
    
    const notesList = document.getElementById('notesList');
    if (notesList) {
      notesList.innerHTML = notes.map(note => `
        <div class="note-item">
          <h3>${note.title}</h3>
          <p>${note.content.substring(0, 50)}...</p>
          <small>Last updated: ${new Date(note.updated_at).toLocaleString()}</small>
          <button onclick="editNote(${note.id})">Edit</button>
          <button onclick="deleteNote(${note.id})">Delete</button>
        </div>
      `).join('');
    }
  } catch (error) {
    console.error('Error loading notes:', error);
  }
}

async function loadNoteForEditing(noteId) {
  try {
    const response = await fetch(`${apiUrl}/notes?username=${currentUser.username}&password=${currentUser.password}`);
    const notes = await response.json();
    const note = notes.find(n => n.id == noteId);
    
    if (note) {
      document.getElementById('editorTitle').textContent = 'Edit Note';
      document.getElementById('noteTitle').value = note.title;
      document.getElementById('noteContent').value = note.content;
    }
  } catch (error) {
    console.error('Error loading note:', error);
  }
}

// Обработчики событий
document.addEventListener('DOMContentLoaded', () => {
  // Инициализация форм
  handleFormSubmit('loginForm', 'login', 'Login successful!', 'notes.html');
  handleFormSubmit('registerForm', 'register', 'Registration successful!', 'index.html');
  
  // Загрузка пользователей
  loadUsers();

  // Инициализация заметок
  if (window.location.pathname.includes('notes.html') || 
      window.location.pathname.includes('note-editor.html')) {
    initNotes();
  }

  // Редактор заметок
  const urlParams = new URLSearchParams(window.location.search);
  const noteId = urlParams.get('id');
  if (noteId) loadNoteForEditing(noteId);

  // Обработчик формы редактора
  document.getElementById('noteForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!currentUser) {
      alert('Session expired. Please login again.');
      window.location.href = 'index.html';
      return;
    }

    const title = document.getElementById('noteTitle').value;
    const content = document.getElementById('noteContent').value;
    const noteId = urlParams.get('id');

    try {
      if (noteId) {
        await fetch(`${apiUrl}/notes/${noteId}?username=${currentUser.username}&password=${currentUser.password}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title, content })
        });
      } else {
        await fetch(`${apiUrl}/notes?username=${currentUser.username}&password=${currentUser.password}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title, content })
        });
      }
      window.location.href = 'notes.html';
    } catch (error) {
      alert('Error saving note: ' + error.message);
    }
  });
});

// Вспомогательные функции
async function deleteNote(noteId) {
  if (confirm('Are you sure you want to delete this note?')) {
    try {
      await fetch(`${apiUrl}/notes/${noteId}?username=${currentUser.username}&password=${currentUser.password}`, {
        method: 'DELETE'
      });
      await loadNotes();
    } catch (error) {
      alert('Error deleting note: ' + error.message);
    }
  }
}

function editNote(noteId) {
  window.location.href = `note-editor.html?id=${noteId}`;
}