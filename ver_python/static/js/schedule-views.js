(function () {
  'use strict';

  var schedules = [];
  var currentView = 'list';
  var calYear, calMonth;

  function init(data) {
    schedules = data || [];
    var now = new Date();
    calYear = now.getFullYear();
    calMonth = now.getMonth();

    document.querySelectorAll('.view-tab').forEach(function (btn) {
      btn.addEventListener('click', function () {
        switchView(btn.dataset.view);
      });
    });
  }

  function switchView(view) {
    currentView = view;
    document.querySelectorAll('.view-tab').forEach(function (b) {
      b.classList.toggle('active', b.dataset.view === view);
    });
    document.getElementById('view-list').style.display = view === 'list' ? '' : 'none';
    document.getElementById('view-calendar').style.display = view === 'calendar' ? '' : 'none';
    document.getElementById('view-gantt').style.display = view === 'gantt' ? '' : 'none';

    if (view === 'calendar') renderCalendar();
    if (view === 'gantt') renderGantt();
  }

  /* ========== Calendar ========== */

  function renderCalendar() {
    var wrap = document.getElementById('view-calendar');
    var months = ['1월','2월','3월','4월','5월','6월','7월','8월','9월','10월','11월','12월'];
    var days = ['일','월','화','수','목','금','토'];

    var html = '<div class="cal-header">';
    html += '<button class="btn btn-sm btn-secondary cal-nav" data-dir="-1">';
    html += '<svg viewBox="0 0 24 24" style="width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2;"><polyline points="15 18 9 12 15 6"/></svg></button>';
    html += '<span class="cal-title">' + calYear + '년 ' + months[calMonth] + '</span>';
    html += '<button class="btn btn-sm btn-secondary cal-nav" data-dir="1">';
    html += '<svg viewBox="0 0 24 24" style="width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2;"><polyline points="9 18 15 12 9 6"/></svg></button>';
    html += '<button class="btn btn-sm btn-secondary cal-today">오늘</button>';
    html += '</div>';

    html += '<div class="cal-grid">';
    for (var d = 0; d < 7; d++) {
      html += '<div class="cal-day-name' + (d === 0 ? ' sun' : '') + (d === 6 ? ' sat' : '') + '">' + days[d] + '</div>';
    }

    var first = new Date(calYear, calMonth, 1);
    var startDay = first.getDay();
    var daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();
    var today = new Date();
    var todayStr = today.getFullYear() + '-' + pad(today.getMonth() + 1) + '-' + pad(today.getDate());

    var prevDays = new Date(calYear, calMonth, 0).getDate();
    for (var i = startDay - 1; i >= 0; i--) {
      html += '<div class="cal-cell other">' + (prevDays - i) + '</div>';
    }

    for (var day = 1; day <= daysInMonth; day++) {
      var dateStr = calYear + '-' + pad(calMonth + 1) + '-' + pad(day);
      var isToday = dateStr === todayStr;
      var daySchedules = schedules.filter(function (s) {
        if (!s.scheduledAt) return false;
        if (s.startAt) {
          var sStart = s.startAt.substring(0, 10);
          var sEnd = s.scheduledAt.substring(0, 10);
          return dateStr >= sStart && dateStr <= sEnd;
        }
        return s.scheduledAt.substring(0, 10) === dateStr;
      });

      html += '<div class="cal-cell' + (isToday ? ' today' : '') + '">';
      html += '<span class="cal-date' + (isToday ? ' today-mark' : '') + '">' + day + '</span>';
      for (var si = 0; si < Math.min(daySchedules.length, 3); si++) {
        var sc = daySchedules[si];
        html += '<a href="/schedule/' + sc.id + '/edit" class="cal-event' + (sc.completed ? ' done' : '') + '">' + escapeHtml(sc.title) + '</a>';
      }
      if (daySchedules.length > 3) {
        html += '<span class="cal-more">+' + (daySchedules.length - 3) + '개</span>';
      }
      html += '</div>';
    }

    var totalCells = startDay + daysInMonth;
    var remaining = (7 - totalCells % 7) % 7;
    for (var r = 1; r <= remaining; r++) {
      html += '<div class="cal-cell other">' + r + '</div>';
    }

    html += '</div>';
    wrap.innerHTML = html;

    wrap.querySelectorAll('.cal-nav').forEach(function (btn) {
      btn.addEventListener('click', function () {
        calMonth += parseInt(btn.dataset.dir);
        if (calMonth < 0) { calMonth = 11; calYear--; }
        if (calMonth > 11) { calMonth = 0; calYear++; }
        renderCalendar();
      });
    });
    var todayBtn = wrap.querySelector('.cal-today');
    if (todayBtn) {
      todayBtn.addEventListener('click', function () {
        var n = new Date();
        calYear = n.getFullYear();
        calMonth = n.getMonth();
        renderCalendar();
      });
    }
  }

  /* ========== Gantt ========== */

  function renderGantt() {
    var wrap = document.getElementById('view-gantt');
    var items = schedules.filter(function (s) { return s.scheduledAt; });
    if (items.length === 0) {
      wrap.innerHTML = '<div class="empty-state"><h3>표시할 일정이 없습니다</h3></div>';
      return;
    }

    items.sort(function (a, b) {
      return new Date(a.scheduledAt) - new Date(b.scheduledAt);
    });

    var allDates = [];
    items.forEach(function (s) {
      allDates.push(new Date(s.startAt || s.scheduledAt));
      allDates.push(new Date(s.scheduledAt));
    });
    var minDate = new Date(Math.min.apply(null, allDates));
    var maxDate = new Date(Math.max.apply(null, allDates));

    minDate.setDate(minDate.getDate() - 1);
    maxDate.setDate(maxDate.getDate() + 2);

    var totalDays = Math.ceil((maxDate - minDate) / 86400000) + 1;
    if (totalDays < 7) totalDays = 7;
    var dayWidth = Math.max(36, Math.min(60, 900 / totalDays));

    var months = groupByMonth(minDate, maxDate);

    var html = '<div class="gantt-wrap">';
    html += '<div class="gantt-container" style="min-width:' + (200 + totalDays * dayWidth) + 'px;">';

    // header
    html += '<div class="gantt-header">';
    html += '<div class="gantt-label-col">일정</div>';
    html += '<div class="gantt-timeline">';
    // month row
    html += '<div class="gantt-months">';
    months.forEach(function (m) {
      html += '<div class="gantt-month" style="width:' + (m.days * dayWidth) + 'px;">' + m.label + '</div>';
    });
    html += '</div>';
    // day row
    html += '<div class="gantt-days">';
    var d = new Date(minDate);
    var today = new Date();
    var todayStr = today.getFullYear() + '-' + pad(today.getMonth() + 1) + '-' + pad(today.getDate());
    for (var i = 0; i < totalDays; i++) {
      var ds = d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
      var isWeekend = d.getDay() === 0 || d.getDay() === 6;
      html += '<div class="gantt-day' + (ds === todayStr ? ' today' : '') + (isWeekend ? ' weekend' : '') + '" style="width:' + dayWidth + 'px;">' + d.getDate() + '</div>';
      d.setDate(d.getDate() + 1);
    }
    html += '</div></div></div>';

    // rows
    items.forEach(function (s) {
      var start = new Date(s.startAt || s.scheduledAt);
      var end = new Date(s.scheduledAt);
      if (start > end) { var tmp = start; start = end; end = tmp; }

      var startOffset = Math.floor((start - minDate) / 86400000);
      var duration = Math.max(1, Math.ceil((end - start) / 86400000) + 1);
      var left = startOffset * dayWidth;
      var width = duration * dayWidth - 2;

      html += '<div class="gantt-row">';
      html += '<div class="gantt-label-col"><a href="/schedule/' + s.id + '/edit" class="gantt-item-link">' + escapeHtml(s.title) + '</a></div>';
      html += '<div class="gantt-timeline-row" style="width:' + (totalDays * dayWidth) + 'px;">';

      // today line
      var todayOffset = Math.floor((today - minDate) / 86400000);
      if (todayOffset >= 0 && todayOffset < totalDays) {
        html += '<div class="gantt-today-line" style="left:' + (todayOffset * dayWidth + dayWidth / 2) + 'px;"></div>';
      }

      html += '<div class="gantt-bar' + (s.completed ? ' done' : '') + '" style="left:' + left + 'px;width:' + width + 'px;" title="' + escapeHtml(s.title) + '\n' + formatDate(start) + ' → ' + formatDate(end) + '">';
      if (width > 60) html += '<span class="gantt-bar-text">' + escapeHtml(s.title) + '</span>';
      html += '</div>';
      html += '</div></div>';
    });

    html += '</div></div>';
    wrap.innerHTML = html;
  }

  function groupByMonth(min, max) {
    var result = [];
    var d = new Date(min);
    while (d <= max) {
      var y = d.getFullYear(), m = d.getMonth();
      var monthEnd = new Date(y, m + 1, 0);
      if (monthEnd > max) monthEnd = new Date(max);
      var days = 0;
      var tmp = new Date(d);
      while (tmp <= monthEnd) { days++; tmp.setDate(tmp.getDate() + 1); }
      result.push({ label: y + '.' + pad(m + 1), days: days });
      d = new Date(y, m + 1, 1);
    }
    return result;
  }

  /* ========== Util ========== */

  function pad(n) { return n < 10 ? '0' + n : '' + n; }

  function formatDate(d) {
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  window.ScheduleViews = { init: init };
})();
