document.addEventListener('DOMContentLoaded', () => {
  const canvas = document.getElementById('studyChart');
  if (!canvas || !window.studyData) return;
  new Chart(canvas, {type:'line', data:{labels:window.studyLabels.map(value => value.slice(5)), datasets:[{data:window.studyData, borderColor:'#17231f', backgroundColor:'rgba(216,243,106,.35)', fill:true, tension:.35, pointRadius:4, pointBackgroundColor:'#17231f'}]}, options:{plugins:{legend:{display:false}}, scales:{y:{beginAtZero:true, grid:{color:'#edf1ed'}},x:{grid:{display:false}}}}});
});
