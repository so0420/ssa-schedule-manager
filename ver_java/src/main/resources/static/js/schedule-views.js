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
    html += '<div class="cal-week-names">';
    for (var d = 0; d < 7; d++) {
      html += '<div class="cal-day-name' + (d === 0 ? ' sun' : '') + (d === 6 ? ' sat' : '') + '">' + days[d] + '</div>';
    }
    html += '</div>';

    var MAX_LANES = 3; // 한 주에 보여줄 일정 줄 수 (넘치면 "+N개")
    var first = new Date(calYear, calMonth, 1);
    var startDay = first.getDay();
    var daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();
    var weekCount = Math.ceil((startDay + daysInMonth) / 7);
    var monthPrefix = calYear + '-' + pad(calMonth + 1);
    var todayStr = formatDate(new Date());

    // 일정을 [시작일, 종료일] 날짜 구간으로 정리 (시작일이 없으면 하루짜리 일정)
    var events = schedules.filter(function (s) { return s.scheduledAt; }).map(function (s) {
      var end = s.scheduledAt.substring(0, 10);
      var start = s.startAt ? s.startAt.substring(0, 10) : end;
      if (start > end) { var tmp = start; start = end; end = tmp; }
      return { s: s, start: start, end: end };
    });
    // 먼저 시작하는 일정 → 더 긴 일정 순으로 위쪽 줄에 배치
    events.sort(function (a, b) {
      if (a.start !== b.start) return a.start < b.start ? -1 : 1;
      if (a.end !== b.end) return a.end > b.end ? -1 : 1;
      return a.s.id - b.s.id;
    });

    for (var w = 0; w < weekCount; w++) {
      var weekDates = [];
      for (var i = 0; i < 7; i++) {
        weekDates.push(formatDate(new Date(calYear, calMonth, 1 - startDay + w * 7 + i)));
      }
      var week = layoutWeek(events, weekDates, MAX_LANES);

      html += '<div class="cal-week">';
      for (i = 0; i < 7; i++) {
        var dateStr = weekDates[i];
        var isToday = dateStr === todayStr;
        var inMonth = dateStr.substring(0, 7) === monthPrefix;
        html += '<div class="cal-cell' + (inMonth ? '' : ' other') + (isToday ? ' today' : '') + '">';
        html += '<span class="cal-date' + (isToday ? ' today-mark' : '') + '">' + parseInt(dateStr.substring(8), 10) + '</span>';
        if (week.hidden[i] > 0) {
          html += '<span class="cal-more">+' + week.hidden[i] + '개</span>';
        }
        html += '</div>';
      }
      html += '<div class="cal-events">' + week.bars + '</div>';
      html += '</div>';
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

  /**
   * 한 주(7일)에 걸치는 일정들을 줄(lane)에 배치한다.
   * 여러 날에 걸친 일정은 시작~종료 칸을 가로지르는 막대 하나로 그린다.
   * 반환값: bars(막대 HTML), hidden(날짜별로 넘쳐서 숨겨진 일정 수)
   */
  function layoutWeek(events, weekDates, maxLanes) {
    var weekStart = weekDates[0];
    var weekEnd = weekDates[6];
    var lanes = [];                       // lanes[줄][요일] = 사용 중 여부
    var hidden = [0, 0, 0, 0, 0, 0, 0];
    var bars = '';

    events.forEach(function (ev) {
      if (ev.end < weekStart || ev.start > weekEnd) return;

      var contLeft = ev.start < weekStart;   // 지난주부터 이어지는 일정
      var contRight = ev.end > weekEnd;      // 다음 주로 이어지는 일정
      var c0 = contLeft ? 0 : weekDates.indexOf(ev.start);
      var c1 = contRight ? 6 : weekDates.indexOf(ev.end);

      // 해당 구간이 비어 있는 가장 위쪽 줄 찾기
      var lane = 0;
      while (lanes[lane] && isLaneBusy(lanes[lane], c0, c1)) lane++;
      if (!lanes[lane]) lanes[lane] = [];
      for (var c = c0; c <= c1; c++) lanes[lane][c] = true;

      if (lane >= maxLanes) {
        for (c = c0; c <= c1; c++) hidden[c]++;
        return;
      }

      var s = ev.s;
      var tip = s.title + '\n' + ev.start + (ev.start !== ev.end ? ' → ' + ev.end : '');
      bars += '<a href="/schedule/' + s.id + '/edit"'
        + ' class="cal-event' + (s.completed ? ' done' : '') + (contLeft ? ' cont-left' : '') + (contRight ? ' cont-right' : '') + '"'
        + ' style="grid-column:' + (c0 + 1) + ' / ' + (c1 + 2) + ';grid-row:' + (lane + 1) + ';"'
        + ' title="' + escapeAttr(tip) + '">' + escapeHtml(s.title) + '</a>';
    });

    return { bars: bars, hidden: hidden };
  }

  function isLaneBusy(lane, c0, c1) {
    for (var c = c0; c <= c1; c++) {
      if (lane[c]) return true;
    }
    return false;
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

  function escapeAttr(str) {
    return escapeHtml(str).replace(/"/g, '&quot;');
  }

  window.ScheduleViews = { init: init };
})();
