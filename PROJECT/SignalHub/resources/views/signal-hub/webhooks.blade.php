@extends('layouts.app')
@section('title', 'Webhook 推送設定 - WAW SignalHub')
@section('content')
<div class="space-y-6" x-data="signalHubWebhooks()" x-init="initWebhooks()">

    <!-- 頁頭資訊 -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-sm">
        <div>
            <h1 class="text-3xl font-black text-white tracking-wide">🔔 第三方 Webhook 實時推送設定</h1>
            <p class="text-base font-medium text-slate-300 mt-1">當信號累計值變更時，透過 HTTP POST (HMAC-SHA256 簽名) 自動推送到第三方系統</p>
        </div>
        <button @click="openCreateModal()"
                class="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-black text-base px-5 py-2.5 rounded-lg shadow-lg hover:shadow-cyan-500/20 transition duration-150">
            + 新建 Webhook
        </button>
    </div>

    <!-- Webhook 列表 -->
    <div class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden shadow-lg">
        <div x-show="loading" class="py-20 text-center text-slate-400 font-bold text-lg">
            ⏳ 數據載入中...
        </div>

        <div x-show="!loading && webhooks.length === 0" class="py-20 text-center text-slate-400 space-y-3">
            <div class="text-5xl">🔔</div>
            <div class="text-xl font-bold text-white">尚無 Webhook 推送設定</div>
            <p class="text-sm text-slate-400">點擊「新建 Webhook」配置實時事件轉發 URL 與簽名金鑰</p>
        </div>

        <table x-show="!loading && webhooks.length > 0" class="w-full text-left text-base">
            <thead class="bg-slate-900/80 border-b border-slate-700 text-slate-300 font-bold uppercase text-sm tracking-wider">
                <tr>
                    <th class="px-5 py-4">Endpoint URL</th>
                    <th class="px-5 py-4">綁定設定檔</th>
                    <th class="px-5 py-4">HMAC 密鑰狀態</th>
                    <th class="px-5 py-4 text-center">狀態 / 失敗次數</th>
                    <th class="px-5 py-4 text-right">操作與測試</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-700/60 font-semibold text-slate-200">
                <template x-for="w in webhooks" :key="w.id">
                    <tr class="hover:bg-slate-750 transition">
                        <td class="px-5 py-4">
                            <div class="font-mono font-extrabold text-cyan-300 text-base break-all" x-text="w.endpoint_url"></div>
                        </td>
                        <td class="px-5 py-4 font-bold text-white" x-text="w.profile ? w.profile.profile_name : '全部 (All Profiles)'"></td>
                        <td class="px-5 py-4">
                            <span x-show="w.secret_key" class="bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs px-2.5 py-1 rounded font-mono font-bold">已設 SHA256 密鑰</span>
                            <span x-show="!w.secret_key" class="bg-slate-700 text-slate-400 text-xs px-2.5 py-1 rounded font-bold">無金鑰 (未簽名)</span>
                        </td>
                        <td class="px-5 py-4 text-center">
                            <span x-show="w.is_active" class="bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-xs px-2.5 py-1 rounded font-bold">啟用</span>
                            <span x-show="!w.is_active" class="bg-slate-700 text-slate-400 text-xs px-2.5 py-1 rounded font-bold">停用</span>
                            <div x-show="w.failure_count > 0" class="text-xs text-rose-400 font-mono mt-1" x-text="'失敗 ' + w.failure_count + ' 次'"></div>
                        </td>
                        <td class="px-5 py-4 text-right space-x-2">
                            <button @click="testWebhook(w.id)" class="bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs px-3 py-1.5 rounded transition">
                                ⚡ 測試發送
                            </button>
                            <button @click="deleteWebhook(w.id)" class="bg-rose-500/20 hover:bg-rose-500/40 text-rose-300 font-bold text-xs px-3 py-1.5 rounded transition">
                                🗑️ 刪除
                            </button>
                        </td>
                    </tr>
                </template>
            </tbody>
        </table>
    </div>

    <!-- Modal: 新建 Webhook -->
    <div x-show="showModal" x-cloak class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="bg-slate-800 border border-slate-700 rounded-xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <h2 class="text-xl font-black text-white">✨ 新建 Webhook 推送端點</h2>
            <div class="space-y-3">
                <div>
                    <label class="block text-sm font-bold text-slate-300 mb-1">接收 Endpoint URL <span class="text-rose-400">*</span></label>
                    <input type="url" x-model="form.endpoint_url" placeholder="https://api.yourdomain.com/webhook/waw-signal"
                           class="w-full bg-slate-900 border border-slate-700 text-cyan-300 font-mono font-bold rounded-lg px-3 py-2 text-base focus:border-cyan-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-sm font-bold text-slate-300 mb-1">HMAC-SHA256 簽名金鑰 (Secret Key)</label>
                    <input type="text" x-model="form.secret_key" placeholder="自訂驗簽密鑰（留空則產生隨機字串）"
                           class="w-full bg-slate-900 border border-slate-700 text-white font-mono rounded-lg px-3 py-2 text-base focus:border-cyan-500 focus:outline-none">
                </div>
            </div>
            <div class="flex justify-end space-x-3 pt-3">
                <button @click="showModal = false" class="bg-slate-700 text-slate-300 font-bold px-4 py-2 rounded-lg">取消</button>
                <button @click="submitWebhook()" class="bg-cyan-500 text-slate-950 font-black px-5 py-2 rounded-lg">建立 Webhook</button>
            </div>
        </div>
    </div>

</div>

<script>
function signalHubWebhooks() {
    return {
        webhooks: [],
        loading: true,
        showModal: false,
        form: { endpoint_url: '', secret_key: '' },
        initWebhooks() {
            this.loading = true;
            fetch('/api/v9/signal-hub/webhooks')
                .then(r => r.json())
                .then(d => {
                    if (d.success) this.webhooks = d.data;
                    this.loading = false;
                })
                .catch(() => { this.loading = false; });
        },
        openCreateModal() {
            this.form = { endpoint_url: '', secret_key: '' };
            this.showModal = true;
        },
        submitWebhook() {
            if (!this.form.endpoint_url) return alert('請填寫 Endpoint URL');
            fetch('/api/v9/signal-hub/webhooks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.form)
            })
            .then(r => r.json())
            .then(d => {
                if (d.success) {
                    this.showModal = false;
                    this.initWebhooks();
                } else alert('建立失敗：' + (d.message || 'URL格式不符'));
            });
        },
        testWebhook(id) {
            fetch(`/api/v9/signal-hub/webhooks/${id}/test`, { method: 'POST' })
                .then(r => r.json())
                .then(d => {
                    if (d.success) alert('⚡ 測試 Webhook 發送成功！狀態碼 200 OK');
                });
        },
        deleteWebhook(id) {
            if (!confirm('確定要刪除此 Webhook？')) return;
            fetch(`/api/v9/signal-hub/webhooks/${id}`, { method: 'DELETE' })
                .then(r => r.json())
                .then(d => { if (d.success) this.initWebhooks(); });
        }
    }
}
</script>
