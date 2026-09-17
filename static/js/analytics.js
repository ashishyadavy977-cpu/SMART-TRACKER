(() => {
  const charts = {};
  let selectedRange = 'today';
  const colors = ['#d8f36a', '#ef8e55', '#4d8c7b', '#75873b', '#e2a45e', '#17231f'];
  const money = value => `₹${Number(value || 0).toLocaleString('en-IN', {maximumFractionDigits: 0})}`;
  const oneDecimal = value => Number(value || 0).toFixed(1);
  const empty = value => value || 'No data available for this period.';
  const setText = (id, value) => { const element = document.getElementById(id); if (element) element.textContent = value; };
  const chart = (id, type, labels, values, options = {}) => {
    const canvas = document.getElementById(id);
    if (!canvas || !window.Chart) return;
    if (charts[id]) charts[id].destroy();
    charts[id] = new Chart(canvas, {type, data: {labels, datasets: [{data: values, borderColor: '#17231f', backgroundColor: type === 'doughnut' ? colors : 'rgba(216,243,106,.45)', borderWidth: 2, borderRadius: 5, fill: type === 'line', tension: .3, pointRadius: type === 'line' ? 3 : 0}]}, options: {responsive: true, maintainAspectRatio: false, plugins: {legend: {display: type === 'doughnut', position: 'bottom'}}, scales: type === 'doughnut' ? {} : {y: {beginAtZero: true, grid: {color: '#edf1ed'}}, x: {grid: {display: false}}}, ...options}});
  };
  const list = (id, html, fallback) => { const element = document.getElementById(id); if (element) element.innerHTML = html || `<div class="empty">${fallback}</div>`; };
  const load = async () => {
    const status = document.getElementById('analyticsStatus');
    const error = document.getElementById('analyticsError');
    error.hidden = true;
    status.innerHTML = '<i class="bi bi-arrow-repeat"></i> Loading analytics...';
    const query = new URLSearchParams({range: selectedRange});
    if (selectedRange === 'custom') { query.set('start', document.getElementById('startDate').value); query.set('end', document.getElementById('endDate').value); }
    try {
      const response = await fetch(`/api/analytics/dashboard?${query}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Analytics unavailable');
      render(data);
      status.innerHTML = `<i class="bi bi-calendar3"></i> ${data.range.start} to ${data.range.end}`;
    } catch (exception) {
      status.innerHTML = '<i class="bi bi-exclamation-circle"></i> Analytics unavailable';
      error.hidden = false;
      document.querySelector('#analyticsError span').textContent = exception.message || 'Unable to load analytics. Please try again.';
    }
  };
  const render = data => {
    const summary = data.summary;
    const cards = [['Productivity score', `${summary.productivity_score}/100`, 'bi-speedometer2'], ['Study hours', `${oneDecimal(summary.study_hours)} hrs`, 'bi-book'], ['Tasks completed', summary.tasks_completed, 'bi-check2-square'], ['Attendance', `${summary.attendance}%`, 'bi-calendar2-check'], ['Goals completed', summary.goals_completed, 'bi-bullseye'], ['Expenses', money(summary.expenses), 'bi-wallet2']];
    document.getElementById('summaryCards').innerHTML = cards.map(card => `<div class="col-6 col-xl-2"><div class="metric analytics-metric"><i class="bi ${card[2]}"></i><span>${card[0]}</span><strong>${card[1]}</strong></div></div>`).join('');
    const study = data.study;
    setText('studyStat', `${oneDecimal(study.total_hours)} hrs total`);
    setText('studySnapshot', '');
    list('studySnapshot', `<div class="analytics-row"><span>Average per day</span><strong>${oneDecimal(study.average_daily_hours)} hrs</strong></div><div class="analytics-row"><span>Most studied</span><strong>${empty(study.most_studied)}</strong></div><div class="analytics-row"><span>Least studied</span><strong>${empty(study.least_studied)}</strong></div><div class="analytics-row"><span>Sessions completed</span><strong>${study.sessions}</strong></div>`, 'No study data available for this period.');
    chart('studyTrendChart', 'line', study.trend.labels.map(label => label.slice(5)), study.trend.values);
    chart('subjectStudyChart', 'bar', study.subjects.labels, study.subjects.values);
    const tasks = data.tasks;
    setText('taskStat', `${tasks.completion_percentage}% complete`);
    chart('taskStatusChart', 'doughnut', tasks.status.labels, tasks.status.values);
    chart('taskPriorityChart', 'bar', tasks.priorities.labels, tasks.priorities.values);
    const attendance = data.attendance;
    setText('attendanceStat', `${attendance.overall_percentage}% overall`);
    chart('attendanceChart', 'bar', attendance.subjects.map(item => item.subject), attendance.subjects.map(item => item.percentage), {scales: {y: {max: 100, beginAtZero: true}}});
    list('attendanceWarnings', attendance.low_subjects.map(item => `<div class="warning-row"><i class="bi bi-exclamation-triangle"></i><span>${item.subject}</span><strong>${item.percentage}%</strong></div>`).join(''), 'No subjects below the 75% threshold.');
    const expenses = data.expenses;
    setText('expenseStat', money(expenses.total));
    chart('expenseCategoryChart', 'doughnut', expenses.categories.labels, expenses.categories.values);
    chart('expenseTrendChart', 'line', expenses.trend.labels, expenses.trend.values);
    list('expenseSnapshot', `<div class="analytics-row"><span>Current month</span><strong>${money(expenses.current_month)}</strong></div><div class="analytics-row"><span>Average daily</span><strong>${money(expenses.average_daily)}</strong></div><div class="analytics-row"><span>Budget remaining</span><strong>${expenses.budget ? money(expenses.remaining) : 'Not set'}</strong></div>`, 'No expense data available for this period.');
    const goals = data.goals;
    setText('goalStat', `${goals.average_progress}% average`);
    list('goalList', goals.items.map(goal => `<div class="goal-analytics"><div><strong>${goal.title}</strong><span>${goal.progress}%</span></div><div class="progress"><div class="progress-bar" style="width:${goal.progress}%"></div></div></div>`).join(''), 'No active goals yet.');
    const exams = data.exams;
    setText('examStat', `${exams.upcoming} upcoming`);
    list('examList', exams.items.map(exam => `<div class="goal-analytics"><div><strong>${exam.name}</strong><span>${exam.days_remaining}d left</span></div><small>${exam.subject} · ${exam.preparation}% preparation</small><div class="progress"><div class="progress-bar" style="width:${exam.preparation}%"></div></div></div>`).join(''), 'No upcoming exams.');
    const productivity = data.productivity;
    setText('productivityValue', `${productivity.score}/100`);
    chart('productivityChart', 'line', productivity.trend.labels.map(label => label.slice(5)), productivity.trend.values);
    list('scoreWeights', Object.entries(productivity.weights).map(([key, value]) => `<span>${key.replaceAll('_', ' ')} <strong>${value}%</strong></span>`).join(''), 'Score weights unavailable.');
    list('insightsList', data.insights.map(item => `<div class="insight insight-${item.type}"><i class="bi bi-lightbulb"></i><p>${item.text}</p></div>`).join(''), 'No insights yet.');
    list('activityList', data.recent_activity.map(item => `<div class="activity-row"><i class="bi bi-${item.icon}"></i><div><strong>${item.label}</strong><small>${item.date}</small></div></div>`).join(''), 'No recent activity in this period.');
  };
  const setup = () => {
    document.querySelectorAll('[data-range]').forEach(button => button.addEventListener('click', () => {
      selectedRange = button.dataset.range;
      document.querySelectorAll('[data-range]').forEach(item => item.classList.toggle('active', item === button));
      document.querySelector('.custom-range').hidden = selectedRange !== 'custom';
      if (selectedRange !== 'custom') load();
    }));
    document.getElementById('applyRange').addEventListener('click', load);
    document.getElementById('retryAnalytics').addEventListener('click', load);
    load();
  };
  window.addEventListener('load', setup);
})();
