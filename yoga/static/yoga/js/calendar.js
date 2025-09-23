// yoga/static/yoga/js/calendar.js
function initCalendar(practiceDatesUrl){
  const root = document.getElementById('calendar-root');
  if(!root) return;

  fetch(practiceDatesUrl)
    .then(r => r.json())
    .then(data => {
      const dates = new Set(data.dates || []);
      renderMiniCalendar(root, dates);
    })
    .catch(err => {
      root.innerHTML = '<p>Unable to load calendar.</p>';
      console.error(err);
    });
}

function renderMiniCalendar(root, dates) {
  // create simple month view for current month
  const today = new Date();
  const y = today.getFullYear();
  const m = today.getMonth();
  const firstDay = new Date(y,m,1);
  const lastDay = new Date(y,m+1,0);
  const table = document.createElement('table');
  table.className = 'mini-calendar';
  let html = '<thead><tr>';
  ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].forEach(d=> html += `<th>${d}</th>`);
  html += '</tr></thead><tbody><tr>';
  // fill blank cells
  for(let i=0;i<firstDay.getDay();i++) html += '<td></td>';
  for(let day=1; day<=lastDay.getDate(); day++){
    const date = new Date(y,m,day);
    const iso = date.toISOString().slice(0,10);
    const practiced = dates.has(iso);
    html += `<td class="${practiced ? 'done' : ''}">${day}</td>`;
    if((firstDay.getDay() + day) % 7 === 0) html += '</tr><tr>';
  }
  html += '</tr></tbody>';
  table.innerHTML = html;
  root.innerHTML = '';
  root.appendChild(table);
}
