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
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Error');

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

async function initNotes() {
  const username = localStorage.getItem('username');
  const password = localStorage.getItem('password');

  if (!username || !password) {
    window.location.href = 'index.html';
    return;
  }

  currentUser = {username, password};
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
              <a href="${apiUrl}/files/${file.path}" download="${file.name}">${file.name}</a>
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
    await fetch(`${apiUrl}/files/${fileId}?note_id=${noteId}`, { method: 'DELETE' });
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
      response = await fetch(`${apiUrl}/notes/${noteId}?username=${currentUser.username}&password=${currentUser.password}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({title, content})
      });
    } else {
      response = await fetch(`${apiUrl}/notes?username=${currentUser.username}&password=${currentUser.password}`, {
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

    await fetch(`${apiUrl}/notes/${noteId}/files?username=${currentUser.username}&password=${currentUser.password}`, {
      method: 'POST',
      body: formData
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  handleFormSubmit('loginForm', 'login', 'Login successful!', 'notes.html');
  handleFormSubmit('registerForm', 'register', 'Registered!', 'index.html');

  if (window.location.pathname.includes('notes.html') ||
     window.location.pathname.includes('note-editor.html')) {
    initNotes();
  }

  const noteId = new URLSearchParams(window.location.search).get('id');
  if (noteId) {
    fetch(`${apiUrl}/notes?username=${currentUser?.username}&password=${currentUser?.password}`)
      .then(res => res.json())
      .then(notes => {
        const note = notes.find(n => n.id == noteId);
        if (note) {
          document.getElementById('noteTitle').value = note.title;
          document.getElementById('noteContent').value = note.content;
          document.getElementById('existingFiles').innerHTML = note.files.map(file => `
            <div class="file-attachment">
              ${file.name}
              <button onclick="deleteFile('${noteId}', '${file.id}')">×</button>
            </div>
          `).join('');
        }
      });
  }
});

async function deleteNote(noteId) {
  if (confirm('Delete this note?')) {
    await fetch(`${apiUrl}/notes/${noteId}?username=${currentUser.username}&password=${currentUser.password}`, {
      method: 'DELETE'
    });
    await loadNotes();
  }
}

function editNote(noteId) {
  window.location.href = `note-editor.html?id=${noteId}`;
}