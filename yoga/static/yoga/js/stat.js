function drawWeeklyChart(){
  const canvas = document.getElementById('weeklyChart');
  if(!canvas) return;
  const ctx = canvas.getContext('2d');
  const items = document.querySelectorAll('#last7 li');
  const values = Array.from(items).map(li => li.textContent.includes('Done') ? 1 : 0);
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0,0,w,h);
  const barW = w / values.length;
  values.forEach((v,i) => {
    const barH = v * h;
    ctx.fillStyle = v ? '#4f46e5' : '#ddd';
    ctx.fillRect(i*barW+10, h - barH, barW - 20, barH);
    ctx.fillStyle = '#000';
    ctx.font = '12px sans-serif';
    // label date (short)
    const dateText = document.querySelectorAll('#last7 li')[i].getAttribute('data-date').slice(5);
    ctx.fillText(dateText, i*barW+10, h-2);
  });
}
