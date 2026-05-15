/**
     * Handle register form submission
     */
    function handleRegister(event) {
      event.preventDefault();

      const nama = document.getElementById('nama').value.trim();
      const email = document.getElementById('email').value.trim();
      const telepon = document.getElementById('telepon').value.trim();
      const password = document.getElementById('password').value;
      const confirmPassword = document.getElementById('confirmPassword').value;
      const btn = document.getElementById('btnSubmit');
      const originalText = btn.innerText;

      // Validasi sederhana
      if (!nama || !email || !telepon || !password || !confirmPassword) {
        shakeButton(btn);
        return;
      }

      // Cek password match
      if (password !== confirmPassword) {
        shakeButton(btn);
        alert('Password tidak cocok!');
        return;
      }

      // Loading state
      btn.innerHTML = '<i class="fas fa-circle-notch fa-spin" style="margin-right:8px;"></i>Memuat...';
      btn.disabled = true;
      btn.style.opacity = '0.85';

      fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nama, email, telepon, password })
      })
      .then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok || !data.ok) {
          throw new Error(data.message || 'Registrasi gagal');
        }
        return data;
      })
      .then(() => {
        window.location.href = '/login';
      })
      .catch((err) => {
        alert(err.message || 'Registrasi gagal');
        // Reset button
        btn.innerHTML = originalText;
        btn.disabled = false;
        btn.style.opacity = '1';
      });

    }

    /**
     * Shake animation untuk error
     */
    function shakeButton(btn) {
      btn.style.animation = 'shake 0.5s ease';
      setTimeout(() => {
        btn.style.animation = '';
      }, 500);
    }

    // Tambah keyframe shake secara dinamis
    const style = document.createElement('style');
    style.textContent = `
      @keyframes shake {
        0%, 100% { transform: translateX(0); }
        20% { transform: translateX(-6px); }
        40% { transform: translateX(6px); }
        60% { transform: translateX(-4px); }
        80% { transform: translateX(4px); }
      }
    `;
    document.head.appendChild(style);