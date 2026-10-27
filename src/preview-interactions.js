/* Offline-only interaction harness. No fetch, XHR, external navigation or storage.
   Theme strings are the exact build artifacts in NEBULA_THEMES above this script. */
(() => {
  'use strict';
  const root = document.documentElement;
  const $ = (selector, scope = document) => scope.querySelector(selector);
  const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];
  const pages = new Set(['repo', 'tree', 'doc', 'code', 'issues', 'pr', 'dash', 'settings', 'login']);
  const mediaMobile = matchMedia('(max-width: 767.98px)');
  const mediaDark = matchMedia('(prefers-color-scheme: dark)');
  const mediaReduce = matchMedia('(prefers-reduced-motion: reduce)');
  const state = {page: 'repo', theme: 'light', motion: true, issueState: 'open', code: '', loginTimer: null};
  let toastTimer;

  function toast(message) {
    const element = $('#preview-toast');
    clearTimeout(toastTimer);
    element.textContent = message;
    element.hidden = false;
    toastTimer = setTimeout(() => { element.hidden = true; }, 2800);
  }

  function closeMenus() {
    $$('details.preview-dropdown[open]').forEach(element => { element.open = false; });
    if (mediaMobile.matches) $('.repo-action-details').open = false;
  }

  function setPage(page, shouldScroll = true) {
    if (!pages.has(page)) return;
    state.page = page;
    const repoPage = ['repo', 'tree', 'doc', 'code', 'issues', 'pr'].includes(page);
    $('#repo-app').hidden = !repoPage;
    $('#repo-app').className = 'page-content repository ' + ({repo: 'file list', code: 'file list', issues: 'issue list', pr: 'view issue pull'}[page] || 'file list');
    $$('[data-repo-page]').forEach(section => { section.hidden = !section.dataset.repoPage.split(' ').includes(page); });
    $('#page-dash').hidden = page !== 'dash';
    $('#page-login').hidden = page !== 'login';
    $('#page-settings').hidden = page !== 'settings';
    $$('[data-browser-view]').forEach(pane => { pane.hidden = pane.dataset.browserView !== page; });
    $('#inner-file-path').hidden = page !== 'doc';
    $$('[data-preview-file-table]').forEach(table => { table.removeAttribute('id'); });
    $('[data-preview-file-table="' + (page === 'tree' ? 'tree' : 'repo') + '"]').id = 'repo-files-table';
    $$('#view-file-tree .tree-item').forEach(item => { item.classList.toggle('selected', item.dataset.treeKey === (page === 'doc' ? 'deployment.md' : 'docs')); });
    $$('.preview-page-picker [data-page]').forEach(button => {
      if (button.dataset.page === page) button.setAttribute('aria-current', 'page');
      else button.removeAttribute('aria-current');
    });
    $$('[data-repo-tab]').forEach(link => {
      const active = link.dataset.repoTab.split(' ').includes(page);
      link.classList.toggle('active', active);
      if (active) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    $$('#navbar .navbar-left > .item[data-page]:not(#navbar-logo)').forEach(link => link.classList.toggle('active', link.dataset.page === page));
    const label = $('.preview-page-picker [data-page="' + page + '"]').textContent;
    document.title = label + ' · Nebula 2 离线预览';
    root.dataset.previewPage = page;
    closeMenus();
    try { history.replaceState(null, '', '#' + page); } catch (_) { /* srcdoc can forbid history URLs */ }
    if (shouldScroll) window.scrollTo({top: 0, behavior: 'instant'});
  }

  function setTheme(theme) {
    if (!Object.hasOwn(NEBULA_THEMES, theme)) return;
    state.theme = theme;
    $('#preview-theme').textContent = NEBULA_THEMES[theme];
    root.dataset.theme = 'nebula-' + theme;
    root.dataset.previewTheme = theme;
    root.dataset.previewEffectiveTheme = theme === 'auto' ? (mediaDark.matches ? 'dark' : 'light') : theme;
    $$('[data-theme]').filter(element => element !== root).forEach(button => button.setAttribute('aria-pressed', String(button.dataset.theme === theme)));
  }

  function setMotion(on) {
    state.motion = on;
    root.dataset.nebulaMotion = on ? 'on' : 'off';
    $('#motion-toggle').setAttribute('aria-pressed', String(on));
    $('#motion-toggle').textContent = on ? '动效开' : '动效关';
    $('#motion-toggle').title = mediaReduce.matches ? '当前系统偏好减少动态效果，装饰动画保持静止。' : '切换主题中的装饰动效';
  }

  function setResponsiveDetails() {
    $('.repo-action-details').open = !mediaMobile.matches;
    $('.repo-overview-details').open = !mediaMobile.matches;
  }

  function showDialog(title, message) {
    $('#preview-dialog-title').textContent = title;
    $('#preview-dialog-text').textContent = message;
    closeMenus();
    if (!$('#preview-dialog').open) $('#preview-dialog').showModal();
  }

  async function copyText(text, label, input) {
    try {
      if (!navigator.clipboard || !window.isSecureContext) throw new Error('clipboard unavailable');
      await navigator.clipboard.writeText(text);
      toast(label + '已复制');
    } catch (_) {
      const field = input || document.createElement('textarea');
      if (!input) {
        field.value = text;
        field.setAttribute('aria-label', '待复制的示例文本');
        field.style.position = 'fixed';
        field.style.opacity = '0';
        document.body.append(field);
      }
      field.focus();
      field.select();
      let copied = false;
      try { copied = document.execCommand('copy'); } catch (_) { /* manual fallback below */ }
      if (!input) field.remove();
      toast(copied ? label + '已复制' : (input ? '已选中示例地址，请手动复制。' : '浏览器未允许复制，请在代码区域选中复制。'));
    }
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, character => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[character]));
  }

  const schedulerCode = `package scheduler

import (
    "context"
    "sync"
    "time"
)

// Scheduler 基于分层时间轮调度任务，最小精度 1ms。
type Scheduler struct {
    mu      sync.RWMutex
    wheels  []*TimingWheel
    tick    time.Duration
    workers int
}

func New(tick time.Duration, workers int) *Scheduler {
    return &Scheduler{
        wheels:  buildWheels(tick, 4),
        tick:    tick,
        workers: workers,
    }
}

func (s *Scheduler) Run(ctx context.Context) error {
    ticker := time.NewTicker(s.tick)
    defer ticker.Stop()
    for {
        select {
        case <-ctx.Done():
            return ctx.Err()
        case now := <-ticker.C:
            s.advance(now)
        }
    }
}`;

  const sampleFiles = {
    internal: {path: 'internal/scheduler/scheduler.go', lang: 'Go', code: schedulerCode},
    '.gitea/workflows': {path: '.gitea/workflows/ci.yml', lang: 'YAML', code: '# 示例工作流\nname: build\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: go test ./...'},
    cmd: {path: 'cmd/qc/main.go', lang: 'Go', code: 'package main\n\nimport "fmt"\n\nfunc main() {\n    // 离线主题展示用的最小示例。\n    fmt.Println("Quantum Core")\n}'},
    pkg: {path: 'pkg/queue/queue.go', lang: 'Go', code: 'package queue\n\n// Queue 是主题展示用的示例结构。\ntype Queue struct {\n    tasks []string\n}\n\nfunc (q *Queue) Push(task string) {\n    q.tasks = append(q.tasks, task)\n}'},
    web: {path: 'web/src/index.ts', lang: 'TypeScript', code: '// 离线主题展示用的示例代码。\ntype Task = { id: string; status: string };\n\nexport function taskLabel(task: Task): string {\n  return `${task.id} · ${task.status}`;\n}'},
    docs: {path: 'docs/deployment.md', lang: 'Markdown', code: '# 集群部署\n\n这是 Quantum Core 示例项目的说明文件。\n\n1. 配置节点标识。\n2. 选择调度与存储设置。\n3. 启动服务并检查健康状态。\n\n本文仅用于展示 Markdown 源文件配色。'},
    '.gitignore': {path: '.gitignore', lang: 'Text', code: '# Local build outputs\nbin/\ndist/\ncoverage.out\n\n# Local environment\n.env\nconfig.local.yaml'},
    'go.mod': {path: 'go.mod', lang: 'Go module', code: 'module example.com/nebula-lab/quantum-core\n\ngo 1.23.0\n\n// Dependencies omitted in this offline preview.'},
    LICENSE: {path: 'LICENSE', lang: 'Text', code: 'MIT License\n\nCopyright (c) 2026 Nebula Lab (example)\n\nThis file is sample content for the theme preview.\nThe actual theme license is supplied with the theme package.'},
    Makefile: {path: 'Makefile', lang: 'Makefile', code: '.PHONY: build test bench\n\nbuild:\n\tgo build ./cmd/qc\n\ntest:\n\tgo test ./...\n\nbench:\n\tgo test -bench=. ./internal/scheduler'},
    'README.md': {path: 'README.md', lang: 'Markdown', code: '# Quantum Core\n\n基于分层时间轮的分布式任务调度引擎。\n\n## 特性\n\n- 分层时间轮\n- 工作池和任务队列\n- 集群协调与故障恢复\n- Web 看板与指标\n\n以上均为离线主题示例。'}
  };
  const keywords = new Set('package import func return if for range type struct var const go select case default defer chan map else break continue switch interface export function'.split(' '));
  const types = new Set('int int64 string error bool byte any Scheduler TimingWheel Task Duration Context RWMutex'.split(' '));
  function highlight(line, language) {
    if (language !== 'Go' && language !== 'TypeScript') return escapeHtml(line) || ' ';
    const pattern = /(\/\/.*$)|("(?:[^"\\]|\\.)*"|`[^`]*`)|(\b\d+(?:\.\d+)?\b)|([A-Za-z_]\w*)|(\s+)|(.)/g;
    let output = '';
    for (const match of line.matchAll(pattern)) {
      let css = '';
      if (match[1]) css = 'c';
      else if (match[2]) css = 's';
      else if (match[3]) css = 'm';
      else if (match[4]) {
        const word = match[4];
        if (keywords.has(word)) css = 'k';
        else if (types.has(word)) css = 'kt';
        else if (/^\s*\(/.test(line.slice(match.index + word.length))) css = 'nf';
      }
      output += css ? '<span class="' + css + '">' + escapeHtml(match[0]) + '</span>' : escapeHtml(match[0]);
    }
    return output || ' ';
  }

  function openFile(name, navigate = true) {
    const file = sampleFiles[name] || sampleFiles.internal;
    state.code = file.code;
    $('#code-path').textContent = file.path.replaceAll('/', ' / ');
    const lines = file.code.split('\n');
    $('#code-line-count').textContent = String(lines.length);
    $('#code-byte-count').textContent = String(new TextEncoder().encode(file.code).length);
    $('#code-language').textContent = file.lang;
    $('#code-lines').innerHTML = lines.map((line, index) => '<tr' + (index === 24 ? ' class="active"' : '') + '><td class="lines-num" aria-hidden="true">' + (index + 1) + '</td><td class="lines-code"><code class="code-inner">' + highlight(line, file.lang) + '</code></td></tr>').join('');
    if (navigate) setPage('code');
  }

  const diffLines = [
    ['tag-code', '', '', '', '@@ -41,6 +41,9 @@ func (s *Scheduler) advance(now time.Time)'],
    ['', '41', '41', '', '    for _, w := range s.wheels {'],
    ['del-code', '42', '', '−', '        w.Tick(now)'],
    ['add-code', '', '42', '+', '        if expired := w.Tick(now); len(expired) > 0 {'],
    ['add-code', '', '43', '+', '            s.dispatch(expired)'],
    ['add-code', '', '44', '+', '        }'],
    ['', '43', '45', '', '    }']
  ];
  const diffHtml = diffLines.map(([css, oldLine, newLine, sign, line]) => '<tr class="' + css + '"><td class="lines-num lines-num-old">' + oldLine + '</td><td class="lines-num lines-num-new">' + newLine + '</td><td class="lines-type-marker">' + sign + '</td><td class="lines-code"><code class="code-inner">' + (css === 'tag-code' ? escapeHtml(line) : highlight(line, 'Go')) + '</code></td></tr>').join('');
  $('#pr-inline-diff').innerHTML = diffHtml;
  $('#pr-full-diff').innerHTML = diffHtml;

  function filterFiles() {
    const query = $('#file-search').value.trim().toLowerCase();
    let count = 0;
    $$('#repo-files-table .repo-file-item').forEach(row => {
      row.hidden = !row.dataset.fileName.toLowerCase().includes(query);
      if (!row.hidden) count++;
    });
    $('#file-empty').hidden = count !== 0;
  }

  function filterIssues() {
    const query = $('#issue-search').value.trim().toLowerCase();
    const label = $('#issue-label-filter').value;
    let count = 0;
    $$('#page-issues .issue-row').forEach(row => {
      const match = row.dataset.state === state.issueState && row.dataset.search.toLowerCase().includes(query) && (label === 'all' || row.dataset.labels.split(' ').includes(label));
      row.hidden = !match;
      if (match) count++;
    });
    $('#issue-empty').hidden = count !== 0;
    $('#issue-result-count').textContent = '显示 ' + count + ' 条示例';
    $$('[data-issue-state]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.issueState === state.issueState)));
  }

  function setFieldError(field, message) {
    $('#' + field + '-field').classList.toggle('error', Boolean(message));
    $('#' + field + '-error').textContent = message;
    const input = $('#' + (field === 'username' ? 'user_name' : 'password'));
    if (message) input.setAttribute('aria-invalid', 'true');
    else input.removeAttribute('aria-invalid');
  }

  function resetLogin() {
    clearTimeout(state.loginTimer);
    state.loginTimer = null;
    $('#preview-login-form').reset();
    $('#preview-login-form').removeAttribute('aria-busy');
    $('#login-submit').classList.remove('is-loading');
    $('#login-submit').disabled = false;
    $('#login-submit').textContent = '登录';
    $('#login-result').hidden = true;
    setFieldError('username', '');
    setFieldError('password', '');
  }

  function submitLogin() {
    if (state.loginTimer !== null) return;
    const user = $('#user_name').value.trim();
    const password = $('#password').value;
    const userError = !user ? '请输入一个示例用户名或邮箱。' : user.length < 2 ? '示例用户名至少需要 2 个字符。' : '';
    const passwordError = !password ? '请输入示例密码。' : password.length < 6 ? '请输入至少 6 个字符，以展示通过校验后的状态。' : '';
    setFieldError('username', userError);
    setFieldError('password', passwordError);
    $('#login-result').hidden = true;
    if (userError || passwordError) {
      $('#' + (userError ? 'user_name' : 'password')).focus();
      return;
    }
    $('#preview-login-form').setAttribute('aria-busy', 'true');
    $('#login-submit').disabled = true;
    $('#login-submit').classList.add('is-loading');
    $('#login-submit').textContent = '正在本地校验…';
    state.loginTimer = setTimeout(() => {
      $('#preview-login-form').removeAttribute('aria-busy');
      $('#login-submit').classList.remove('is-loading');
      $('#login-submit').disabled = false;
      $('#login-submit').textContent = '登录';
      $('#password').value = '';
      $('#login-result').textContent = '本地示例校验完成。未向服务器发送用户名或密码，也未登录任何线上账户。';
      $('#login-result').hidden = false;
      state.loginTimer = null;
    }, 1500);
  }

  document.addEventListener('click', event => {
    const target = event.target.closest('button, a, summary');
    if (!target) return;
    if (target.dataset.page) { event.preventDefault(); setPage(target.dataset.page); return; }
    if (target.dataset.theme) { setTheme(target.dataset.theme); return; }
    if (target.dataset.file) { event.preventDefault(); openFile(target.dataset.file); return; }
    if (target.hasAttribute('data-readme')) {
      event.preventDefault(); setPage('repo', false); $('#readme').scrollIntoView({behavior: 'instant', block: 'start'}); return;
    }
    if (target.dataset.dialogTitle) { event.preventDefault(); showDialog(target.dataset.dialogTitle, target.dataset.dialogText || '当前为离线示例。'); return; }
    if (target.dataset.localToggle) {
      const pressed = target.getAttribute('aria-pressed') === 'true';
      target.setAttribute('aria-pressed', String(!pressed));
      $('span:not(.action-count)', target).textContent = pressed ? target.dataset.localToggle : '已' + target.dataset.localToggle;
      toast('已更新当前预览状态'); return;
    }
    if (target.dataset.branch) {
      $('#branch-name').textContent = target.dataset.branch === 'main' ? 'main' : 'feat/wheel';
      $('#branch-name').title = target.dataset.branch;
      closeMenus(); toast('已切换示例分支'); return;
    }
    if (target.dataset.cloneProtocol) {
      const protocol = target.dataset.cloneProtocol;
      $('#clone-url').value = protocol === 'ssh' ? 'git@example.com:nebula-lab/quantum-core.git' : 'https://example.com/nebula-lab/quantum-core.git';
      $$('[data-clone-protocol]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.cloneProtocol === protocol))); return;
    }
    if (target.dataset.issueState) { state.issueState = target.dataset.issueState; filterIssues(); return; }
    if (target.dataset.prTab) {
      $$('[data-pr-tab]').forEach(button => button.setAttribute('aria-selected', String(button === target)));
      ['conversation', 'commits', 'files'].forEach(tab => { $('#pr-' + tab).hidden = tab !== target.dataset.prTab; }); return;
    }
  });

  document.addEventListener('click', event => {
    $$('details.preview-dropdown[open]').forEach(details => { if (!details.contains(event.target)) details.open = false; });
    const actions = $('.repo-action-details');
    if (mediaMobile.matches && actions.open && !actions.contains(event.target)) actions.open = false;
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') closeMenus();
    if (event.key.toLowerCase() === 't' && state.page === 'repo' && !event.ctrlKey && !event.metaKey && !event.altKey && !event.target.closest('input, textarea, select') && !mediaMobile.matches) {
      event.preventDefault(); $('#file-search').focus();
    }
  });
  $('#motion-toggle').addEventListener('click', () => setMotion(!state.motion));
  $('#copy-clone').addEventListener('click', () => copyText($('#clone-url').value, '示例地址', $('#clone-url')));
  $('#copy-code').addEventListener('click', () => copyText(state.code, '示例代码'));
  $('#file-search').addEventListener('input', filterFiles);
  $('#issue-search').addEventListener('input', filterIssues);
  $('#issue-label-filter').addEventListener('change', filterIssues);
  $('#dashboard-repo-search').addEventListener('input', event => {
    const query = event.target.value.trim().toLowerCase(); let count = 0;
    $$('.dashboard-repos [data-repository]').forEach(row => { row.hidden = !row.dataset.repository.includes(query); if (!row.hidden) count++; });
    $('#dashboard-empty').hidden = count !== 0;
  });
  $$('[data-preview-settings-form]').forEach(form => form.addEventListener('submit', event => {
    event.preventDefault();
    if (form.dataset.previewSettingsForm === 'theme') setTheme($('#settings-theme').value);
    toast('已更新当前离线预览；未向服务器提交设置');
  }));
  $('#preview-login-form').addEventListener('submit', event => { event.preventDefault(); submitLogin(); });
  $('#fill-demo-login').addEventListener('click', () => { resetLogin(); $('#user_name').value = 'lin.zhao'; $('#password').value = 'preview-only'; $('#user_name').focus(); });
  $('#show-login-errors').addEventListener('click', () => { resetLogin(); submitLogin(); });
  $('#reset-login').addEventListener('click', resetLogin);
  $('#user_name').addEventListener('input', () => { if ($('#username-field').classList.contains('error')) setFieldError('username', ''); });
  $('#password').addEventListener('input', () => { if ($('#password-field').classList.contains('error')) setFieldError('password', ''); });
  $('#dialog-close').addEventListener('click', () => $('#preview-dialog').close());
  $('#dialog-done').addEventListener('click', () => $('#preview-dialog').close());
  $('#preview-dialog').addEventListener('click', event => { if (event.target === $('#preview-dialog')) $('#preview-dialog').close(); });
  mediaMobile.addEventListener('change', setResponsiveDetails);
  mediaDark.addEventListener('change', () => { if (state.theme === 'auto') root.dataset.previewEffectiveTheme = mediaDark.matches ? 'dark' : 'light'; });
  mediaReduce.addEventListener('change', () => setMotion(state.motion));

  const parameters = new URLSearchParams(location.search);
  openFile('internal', false);
  setResponsiveDetails();
  filterIssues();
  setTheme(parameters.get('theme') || 'light');
  setMotion(parameters.get('motion') !== 'off');
  const requestedPage = parameters.get('page') || location.hash.slice(1) || 'repo';
  setPage(pages.has(requestedPage) ? requestedPage : 'repo', false);
  root.dataset.previewReady = 'true';
})();
