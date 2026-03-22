<template>
  <div class="app">
    <header>
      <h1>{{ t('title') }}</h1>
      <div class="controls">
        <span class="music-badge" :class="musicOnline ? 'online' : 'offline'">
          🎵 ACE-Step {{ musicOnline ? t('online') : t('offline') }}
        </span>
        <button @click="toggleLang" class="lang-btn">
          {{ lang === 'zh' ? 'EN' : '中文' }}
        </button>
      </div>
    </header>

    <section v-if="active.length">
      <h2>⚙️ {{ t('running') }}</h2>
      <div class="card-row">
        <div v-for="task in active" :key="task.started_at + task.type" class="card running">
          <div class="card-type">{{ task.type_label }}</div>
          <div class="card-name">{{ task.name }}</div>
          <div class="card-elapsed">{{ task.elapsed }}s</div>
        </div>
      </div>
    </section>

    <section>
      <h2>📊 {{ t('stats') }}</h2>
      <div class="card-row">
        <div v-for="(s, key) in stats" :key="key" class="card stat">
          <div class="card-type">{{ s.label }}</div>
          <div class="stat-row">
            <span class="done">✅ {{ s.done }}</span>
            <span class="error">❌ {{ s.error }}</span>
          </div>
        </div>
      </div>
    </section>

    <section>
      <h2>📋 {{ t('events') }}</h2>
      <table>
        <thead>
          <tr>
            <th>{{ t('time') }}</th>
            <th>{{ t('type') }}</th>
            <th>{{ t('name') }}</th>
            <th>{{ t('status') }}</th>
            <th>{{ t('message') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in events" :key="e.id" :class="e.status">
            <td>{{ formatTime(e.created_at) }}</td>
            <td><span class="tag" :class="e.type">{{ e.type_label }}</span></td>
            <td class="name-cell">{{ e.name }}</td>
            <td><span class="status-badge" :class="e.status">{{ e.status_label }}</span></td>
            <td class="msg-cell">{{ e.message }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="!events.length" class="empty">{{ t('noData') }}</div>
    </section>

    <footer>{{ t('lastUpdate') }}: {{ lastUpdate }}</footer>
  </div>
</template>

<script>
const I18N = {
  zh: {
    title: 'IsanX13 監控中心', running: '正在執行', stats: '統計',
    events: '事件紀錄', time: '時間', type: '類型', name: '名稱',
    status: '狀態', message: '訊息', noData: '尚無事件記錄',
    lastUpdate: '最後更新', online: '運行中', offline: '離線',
  },
  en: {
    title: 'IsanX13 Monitor', running: 'Running', stats: 'Statistics',
    events: 'Event Log', time: 'Time', type: 'Type', name: 'Name',
    status: 'Status', message: 'Message', noData: 'No events yet',
    lastUpdate: 'Last updated', online: 'Online', offline: 'Offline',
  },
}

export default {
  data() {
    return {
      lang: localStorage.getItem('lang') || 'zh',
      events: [], stats: {}, active: [],
      musicOnline: false, lastUpdate: '--', timer: null,
    }
  },
  computed: {
    t() { return (key) => I18N[this.lang][key] || key },
  },
  methods: {
    toggleLang() {
      this.lang = this.lang === 'zh' ? 'en' : 'zh'
      localStorage.setItem('lang', this.lang)
      this.fetchAll()
    },
    async fetchAll() {
      const l = this.lang
      try {
        const [ev, st, ac, ms] = await Promise.all([
          fetch(`/api/events?lang=${l}&limit=50`).then(r => r.json()),
          fetch(`/api/stats?lang=${l}`).then(r => r.json()),
          fetch(`/api/active?lang=${l}`).then(r => r.json()),
          fetch(`/api/music/status`).then(r => r.json()),
        ])
        this.events = ev
        this.stats = st
        this.active = ac
        this.musicOnline = ms.online
        this.lastUpdate = new Date().toLocaleTimeString(this.lang === 'zh' ? 'zh-TW' : 'en-US')
      } catch(e) { console.error(e) }
    },
    formatTime(ts) {
      return new Date(ts * 1000).toLocaleString(
        this.lang === 'zh' ? 'zh-TW' : 'en-US',
        { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }
      )
    },
  },
  mounted() { this.fetchAll(); this.timer = setInterval(this.fetchAll, 4000) },
  beforeUnmount() { clearInterval(this.timer) },
}
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #0f1117; color: #e2e8f0; font-family: 'Segoe UI', sans-serif; }
.app { max-width: 1200px; margin: 0 auto; padding: 20px; }
header { display: flex; justify-content: space-between; align-items: center; padding: 16px 0 24px; border-bottom: 1px solid #2d3748; }
header h1 { font-size: 1.5rem; color: #90cdf4; }
.controls { display: flex; align-items: center; gap: 12px; }
.music-badge { padding: 4px 10px; border-radius: 999px; font-size: 0.8rem; font-weight: 600; }
.music-badge.online  { background: #1a3a2a; color: #68d391; border: 1px solid #2f855a; }
.music-badge.offline { background: #3a1a1a; color: #fc8181; border: 1px solid #9b2c2c; }
.lang-btn { background: #2d3748; color: #e2e8f0; border: 1px solid #4a5568; padding: 4px 12px; border-radius: 6px; cursor: pointer; font-size: 0.85rem; }
.lang-btn:hover { background: #4a5568; }
section { margin-top: 28px; }
section h2 { font-size: 1rem; color: #a0aec0; margin-bottom: 12px; }
.card-row { display: flex; flex-wrap: wrap; gap: 12px; }
.card { background: #1a202c; border: 1px solid #2d3748; border-radius: 10px; padding: 14px 18px; min-width: 160px; }
.card.running { border-color: #3182ce; background: #1a2a3a; }
.card-type { font-size: 0.75rem; color: #718096; margin-bottom: 4px; }
.card-name { font-size: 0.95rem; color: #e2e8f0; word-break: break-all; }
.card-elapsed { font-size: 0.8rem; color: #63b3ed; margin-top: 6px; }
.stat-row { display: flex; gap: 12px; margin-top: 6px; font-size: 0.9rem; }
.done { color: #68d391; }
.error { color: #fc8181; }
table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
th { text-align: left; padding: 8px 12px; color: #718096; border-bottom: 1px solid #2d3748; }
td { padding: 8px 12px; border-bottom: 1px solid #1e2533; vertical-align: top; }
tr:hover td { background: #1a202c; }
.tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.78rem; font-weight: 600; }
.tag.music        { background: #2d3a2d; color: #68d391; }
.tag.design       { background: #2d2d3a; color: #90cdf4; }
.tag.claude       { background: #3a2d2d; color: #fc8181; }
.tag.orchestrator { background: #3a3a2d; color: #f6e05e; }
.tag.cron         { background: #2d3a3a; color: #81e6d9; }
.tag.discord      { background: #2d2d4a; color: #a78bfa; }
.tag.line         { background: #2d3a2d; color: #9ae6b4; }
.status-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.78rem; }
.status-badge.done     { background: #1a3a2a; color: #68d391; }
.status-badge.error    { background: #3a1a1a; color: #fc8181; }
.status-badge.start    { background: #1a2a3a; color: #63b3ed; }
.status-badge.progress { background: #2d3a2d; color: #f6e05e; }
.name-cell { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.msg-cell  { max-width: 300px; color: #a0aec0; word-break: break-all; }
.empty { color: #4a5568; text-align: center; padding: 40px; }
footer { margin-top: 32px; text-align: center; color: #4a5568; font-size: 0.8rem; }
</style>
