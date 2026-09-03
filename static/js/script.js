document.addEventListener('DOMContentLoaded', () => {
  const canvas = document.getElementById('studyChart');
  if (canvas && window.studyData) {
    new Chart(canvas, {type:'line', data:{labels:window.studyLabels.map(value => value.slice(5)), datasets:[{data:window.studyData, borderColor:'#17231f', backgroundColor:'rgba(216,243,106,.35)', fill:true, tension:.35, pointRadius:4, pointBackgroundColor:'#17231f'}]}, options:{plugins:{legend:{display:false}}, scales:{y:{beginAtZero:true, grid:{color:'#edf1ed'}},x:{grid:{display:false}}}}});
  }

  const sidebar = document.querySelector('.sidebar');
  const topbar = document.querySelector('.topbar');
  if (!sidebar || !topbar) return;

  const menuButton = document.createElement('button');
  menuButton.className = 'menu-toggle';
  menuButton.type = 'button';
  menuButton.setAttribute('aria-label', 'Open navigation');
  menuButton.setAttribute('aria-expanded', 'false');
  menuButton.innerHTML = '<i class="bi bi-list"></i>';
  document.body.appendChild(menuButton);

  const backdrop = document.createElement('div');
  backdrop.className = 'sidebar-backdrop';
  document.body.appendChild(backdrop);

  const closeMenu = () => {
    sidebar.classList.remove('is-open');
    backdrop.classList.remove('is-visible');
    menuButton.setAttribute('aria-expanded', 'false');
  };
  menuButton.addEventListener('click', () => {
    const isOpen = sidebar.classList.toggle('is-open');
    backdrop.classList.toggle('is-visible', isOpen);
    menuButton.setAttribute('aria-expanded', String(isOpen));
  });
  backdrop.addEventListener('click', closeMenu);
  sidebar.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));

  const themeButton = document.createElement('button');
  themeButton.className = 'theme-toggle';
  themeButton.type = 'button';
  themeButton.setAttribute('aria-label', 'Toggle dark mode');
  themeButton.innerHTML = '<i class="bi bi-moon-stars"></i>';
  topbar.appendChild(themeButton);
  const setTheme = dark => {
    document.body.classList.toggle('dark-mode', dark);
    themeButton.innerHTML = dark ? '<i class="bi bi-sun"></i>' : '<i class="bi bi-moon-stars"></i>';
    localStorage.setItem('smart-tracker-theme', dark ? 'dark' : 'light');
  };
  setTheme(localStorage.getItem('smart-tracker-theme') === 'dark');
  themeButton.addEventListener('click', () => setTheme(!document.body.classList.contains('dark-mode')));

  document.querySelectorAll('.table-responsive table').forEach(table => {
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    const pageSize = 10;
    if (rows.length <= pageSize) return;
    const navigation = document.createElement('div');
    navigation.className = 'table-pagination';
    table.parentElement.after(navigation);
    let page = 1;
    const renderPage = () => {
      const pageCount = Math.ceil(rows.length / pageSize);
      rows.forEach((row, index) => { row.hidden = index < (page - 1) * pageSize || index >= page * pageSize; });
      navigation.innerHTML = `<span>Page ${page} of ${pageCount}</span><div><button class="btn btn-light btn-sm" ${page === 1 ? 'disabled' : ''} data-page="prev">Previous</button><button class="btn btn-light btn-sm" ${page === pageCount ? 'disabled' : ''} data-page="next">Next</button></div>`;
      navigation.querySelector('[data-page="prev"]').addEventListener('click', () => { page -= 1; renderPage(); });
      navigation.querySelector('[data-page="next"]').addEventListener('click', () => { page += 1; renderPage(); });
    };
    renderPage();
  });

  if (window.location.pathname === '/profile') {
    const profilePanel = document.querySelector('.profile-panel');
    if (profilePanel) {
      const backupPanel = document.createElement('div');
      backupPanel.className = 'backup-tools mt-4 pt-4 border-top';
      backupPanel.innerHTML = '<span class="eyebrow">Your data</span><h3>Backup and restore</h3><a class="btn btn-outline-dark btn-sm" href="/backup/export"><i class="bi bi-download"></i> Download backup</a><form method="post" action="/backup/restore" enctype="multipart/form-data" class="mt-3"><input class="form-control form-control-sm" type="file" name="backup" accept=".json" required><button class="btn btn-light btn-sm mt-2"><i class="bi bi-upload"></i> Restore backup</button></form>';
      profilePanel.appendChild(backupPanel);
    }
  }

  if (window.location.pathname === '/admin/dashboard' && window.Chart) {
    const content = document.querySelector('.page-body');
    if (content) {
      const analyticsPanel = document.createElement('div');
      analyticsPanel.className = 'panel mt-4';
      analyticsPanel.innerHTML = '<div class="panel-head"><div><span class="eyebrow">Community pulse</span><h2>Analytics</h2></div></div><canvas height="90"></canvas>';
      content.appendChild(analyticsPanel);
      fetch('/admin/analytics').then(response => response.json()).then(data => new Chart(analyticsPanel.querySelector('canvas'), {type:'bar', data:{labels:['Students','Tasks','Completed','Study hours','Attendance %','Goals','Expenses'], datasets:[{data:[data.users,data.tasks,data.completed_tasks,data.average_study_hours,data.average_attendance,data.goals,data.expenses], backgroundColor:['#d8f36a','#ef8e55','#4d8c7b','#75873b','#17231f','#b8ce4c','#e2a45e'], borderRadius:6}]}, options:{plugins:{legend:{display:false}}, scales:{y:{beginAtZero:true}}}})).catch(() => { analyticsPanel.querySelector('h2').textContent = 'Analytics unavailable'; });
    }
  }
});
