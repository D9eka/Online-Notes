const apiUrl = 'http://localhost:8000';

// Общие функции
const showNotification = (message, isSuccess) => {
  const notification = document.getElementById('notification');
  notification.textContent = message;
  notification.className = `notification ${isSuccess ? 'success' : 'error'}`;
  notification.style.display = 'block';
  setTimeout(() => notification.style.display = 'none', 3000);
};

const handleFormSubmit = (formId, endpoint, successMessage, redirectPage) => {
  const form = document.getElementById(formId);
  if (!form) return;

  form.onsubmit = async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
      let options;
      if (endpoint === 'signup' || endpoint === 'token') {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        options = {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: formData
        };
      } else {
        options = {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password })
        };
      }

      const response = await fetch(`${apiUrl}/${endpoint}`, options);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка сервера');
      }

      const data = await response.json();
      if (endpoint === 'token') {
        localStorage.setItem('token', data.access_token);
      }

      showNotification(successMessage, true);
      if (redirectPage) {
        window.location.href = redirectPage;
      }

    } catch (error) {
      showNotification(error.message, false);
    }
  };
};

async function authFetch(url, options = {}) {
  const token = localStorage.getItem('token');
  if (!token) {
    window.location.replace('index.html');
    throw new Error('No token');
  }

  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`
  };

  const response = await fetch(url, { ...options, headers });
  if (response.status === 401) {
    localStorage.removeItem('token');
    window.location.replace('index.html');
    throw new Error('Unauthorized');
  }
  return response;
}

async function loadNotes() {
  try {
    const response = await authFetch(`${apiUrl}/notes`);
    const notes = await response.json();
    const notesList = document.getElementById('notesList');
    if (notesList) {
      notesList.innerHTML = notes.map(note => `
        <div class="note-item">
          <div class="note-header">
            <h3>${note.title}</h3>
            <div class="note-actions">
              <button onclick="editNote(${note.id})">Edit</button>
              <button onclick="deleteNote(${note.id})">Delete</button>
            </div>
          </div>
          <p>${note.content.substring(0, 100)}...</p>
          ${note.files.map(file => `
            <div class="file-attachment">
              <a href="${apiUrl}/files/${file.path}" download="${file.filename}">${file.filename}</a>
            </div>
          `).join('')}
          <small>Last updated: ${new Date(note.updated_at).toLocaleString()}</small>
        </div>
      `).join('');
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

async function deleteFile(noteId, fileId) {
  if (confirm('Delete this file?')) {
    await authFetch(`${apiUrl}/files/${fileId}?note_id=${noteId}`, { method: 'DELETE' });
    await loadNotes();
  }
}

document.getElementById('noteForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const title = document.getElementById('noteTitle').value;
  const content = document.getElementById('noteContent').value;
  const noteId = new URLSearchParams(window.location.search).get('id');
  try {
    let response;
    if (noteId) {
      response = await authFetch(`${apiUrl}/notes/${noteId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({title, content})
      });
    } else {
      response = await authFetch(`${apiUrl}/notes`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({title, content})
      });
    }
    const newNote = await response.json();
    await uploadFiles(newNote.id);
    window.location.href = 'notes.html';
  } catch (error) {
    alert('Error: ' + error.message);
  }
});

async function uploadFiles(noteId) {
  const files = document.getElementById('fileInput').files;
  for (const file of files) {
    const formData = new FormData();
    formData.append('file', file);
    await authFetch(`${apiUrl}/notes/${noteId}/files`, {
      method: 'POST',
      body: formData
    });
  }
}

async function initNotes() {
  const protectedPaths = ['/notes.html', '/note-editor.html'];
  const currentPath = window.location.pathname;
  if (protectedPaths.some(path => currentPath.endsWith(path))) {
    const token = localStorage.getItem('token');
    if (!token) {
      window.location.replace('index.html');
      return;
    }
    if (currentPath.endsWith('notes.html')) {
      await loadNotes();
    }
    if (currentPath.endsWith('note-editor.html')) {
      const noteId = new URLSearchParams(window.location.search).get('id');
      if (noteId) {
        try {
          const response = await authFetch(`${apiUrl}/notes/${noteId}`);
          const note = await response.json();
          document.getElementById('noteTitle').value = note.title;
          document.getElementById('noteContent').value = note.content;
          document.getElementById('existingFiles').innerHTML = note.files.map(file => `
            <div class="file-attachment">
              ${file.filename}
              <button onclick="deleteFile('${noteId}', '${file.id}')">×</button>
            </div>
          `).join('');
        } catch (error) {
          console.error('Error loading note:', error);
        }
      }
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  handleFormSubmit('registerForm', 'signup', 'Registered!', 'index.html');
  handleFormSubmit('loginForm', 'token', 'Login successful!', 'notes.html');
  initNotes().catch(error => {
    console.error('Init failed:', error);
    window.location.replace('index.html');
  });
});

async function deleteNote(noteId) {
  if (confirm('Delete this note?')) {
    await authFetch(`${apiUrl}/notes/${noteId}`, { method: 'DELETE' });
    await loadNotes();
  }
}

function editNote(noteId) {
  window.location.href = `note-editor.html?id=${noteId}`;
}

function logout() {
  localStorage.removeItem('token');
  window.location.replace('index.html');
}