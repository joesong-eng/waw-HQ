@extends('layouts.app')
@section('title', '信號設定檔 - WAW SignalHub')
@section('content')
<div class="space-y-6" x-data="signalHubProfiles()" x-init="initProfiles()">

    <!-- 頁頭資訊 -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-sm">
        <div>
            <h1 class="text-3xl font-black text-white tracking-wide">📡 信號設定檔管理 (Signal Profiles)</h1>
            <p class="text-base font-medium text-slate-300 mt-1">定義設備之 8 組腳位映射 (UI1~UI4 / UO1~UO4) 與統計公式規則</p>
        </div>
        <button @click="openCreateModal()"
                class="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-black text-base px-5 py-2.5 rounded-lg shadow-lg hover:shadow-cyan-500/20 transition duration-150">
            + 新建設定檔
        </button>
    </div>

    <!-- 搜尋與過濾列 -->
    <div class="bg-slate-800/80 border border-slate-700 rounded-xl p-4 flex flex-wrap items-center gap-4">
        <div class="flex-1 min-w-[240px]">
            <input type="text" x-model="filters.search" @input.debounce.300ms="loadProfiles()"
                   placeholder="🔍 搜尋設定檔名稱..."
                   class="w-full bg-slate-900 border border-slate-700 text-white rounded-lg px-4 py-2 text-base focus:outline-none focus:border-cyan-500">
        </div>
        <select x-model="filters.status" @change="loadProfiles()"
                class="bg-slate-900 border border-slate-700 text-white rounded-lg px-4 py-2 text-base font-semibold focus:outline-none focus:border-cyan-500">
            <option value="">全部狀態</option>
            <option value="active">啟用中</option>
            <option value="template">官方/自訂模板</option>
        </select>
    </div>

    <!-- 設定檔卡片與列表 -->
    <div class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden shadow-lg">
        <div x-show="loading" class="py-20 text-center text-slate-400 font-bold text-lg">
            ⏳ 數據載入中...
        </div>

        <div x-show="!loading && profiles.length === 0" class="py-20 text-center text-slate-400 space-y-3">
            <div class="text-5xl">📡</div>
            <div class="text-xl font-bold text-white">尚無任何信號設定檔</div>
            <p class="text-sm text-slate-400">點擊右上角「新建設定檔」開始配置您的第一組 8 通道採集卡</p>
        </div>

        <table x-show="!loading && profiles.length > 0" class="w-full text-left text-base">
            <thead class="bg-slate-900/80 border-b border-slate-700 text-slate-300 font-bold uppercase text-sm tracking-wider">
                <tr>
                    <th class="px-5 py-4">設定檔名稱</th>
                    <th class="px-5 py-4">行業標籤</th>
                    <th class="px-5 py-4 text-center">腳位映射</th>
                    <th class="px-5 py-4 text-center">統計指標</th>
                    <th class="px-5 py-4 text-center">狀態</th>
                    <th class="px-5 py-4 text-right">操作管理</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-700/60 font-semibold text-slate-200">
                <template x-for="p in profiles" :key="p.id">
                    <tr class="hover:bg-slate-750 transition">
                        <td class="px-5 py-4">
                            <div class="font-extrabold text-white text-lg" x-text="p.profile_name"></div>
                            <div class="text-xs text-slate-400 font-mono mt-0.5" x-text="p.description || '無備註描述'"></div>
                        </td>
                        <td class="px-5 py-4">
                            <span class="inline-block bg-slate-700 text-cyan-300 text-xs px-2.5 py-1 rounded font-bold"
                                  x-text="p.industry_tag || '通用/自訂'"></span>
                        </td>
                        <td class="px-5 py-4 text-center">
                            <a :href="'/profiles/' + p.id + '/pins'"
                               class="inline-flex items-center space-x-1 font-mono font-black text-cyan-400 hover:underline text-base">
                                <span x-text="p.pin_mappings_count || 8"></span>
                                <span class="text-xs text-slate-400">通道</span>
                            </a>
                        </td>
                        <td class="px-5 py-4 text-center">
                            <a :href="'/profiles/' + p.id + '/stats'"
                               class="inline-flex items-center space-x-1 font-mono font-black text-amber-400 hover:underline text-base">
                                <span x-text="p.stat_rules_count || 0"></span>
                                <span class="text-xs text-slate-400">規則</span>
                            </a>
                        </td>
                        <td class="px-5 py-4 text-center">
                            <span x-show="p.is_template" class="bg-purple-500/20 text-purple-300 border border-purple-500/40 text-xs px-2.5 py-1 rounded font-bold">模板</span>
                            <span x-show="!p.is_template && p.is_active" class="bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-xs px-2.5 py-1 rounded font-bold">啟用中</span>
                            <span x-show="!p.is_template && !p.is_active" class="bg-slate-700 text-slate-400 text-xs px-2.5 py-1 rounded font-bold">停用</span>
                        </td>
                        <td class="px-5 py-4 text-right space-x-2">
                            <a :href="'/profiles/' + p.id + '/pins'"
                               class="bg-slate-700 hover:bg-slate-600 text-white font-bold text-xs px-3 py-1.5 rounded transition">
                                🔌 腳位映射
                            </a>
                            <a :href="'/profiles/' + p.id + '/stats'"
                               class="bg-slate-700 hover:bg-slate-600 text-white font-bold text-xs px-3 py-1.5 rounded transition">
                                📊 統計公式
                            </a>
                            <button @click="openCopyModal(p)"
                                    class="bg-slate-700 hover:bg-slate-600 text-cyan-300 font-bold text-xs px-3 py-1.5 rounded transition">
                                📋 複製
                            </button>
                            <button @click="deleteProfile(p)"
                                    class="bg-rose-500/20 hover:bg-rose-500/40 text-rose-300 font-bold text-xs px-3 py-1.5 rounded transition">
                                🗑️
                            </button>
                        </td>
                    </tr>
                </template>
            </tbody>
        </table>
    </div>

    <!-- Modal: 新建設定檔 -->
    <div x-show="showCreateModal" x-cloak class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="bg-slate-800 border border-slate-700 rounded-xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <h2 class="text-xl font-black text-white">✨ 新建信號設定檔</h2>
            <div class="space-y-3">
                <div>
                    <label class="block text-sm font-bold text-slate-300 mb-1">設定檔名稱 <span class="text-rose-400">*</span></label>
                    <input type="text" x-model="form.profile_name" placeholder="例如：夾娃娃機-雙投幣標準型"
                           class="w-full bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2 text-base focus:border-cyan-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-sm font-bold text-slate-300 mb-1">行業標籤</label>
                    <input type="text" x-model="form.industry_tag" placeholder="如：游藝場、自助洗車、充電樁"
                           class="w-full bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2 text-base focus:border-cyan-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-sm font-bold text-slate-300 mb-1">說明描述</label>
                    <textarea x-model="form.description" rows="3" placeholder="描述此採集腳位配置細節..."
                              class="w-full bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2 text-base focus:border-cyan-500 focus:outline-none"></textarea>
                </div>
            </div>
            <div class="flex justify-end space-x-3 pt-3">
                <button @click="showCreateModal = false" class="bg-slate-700 text-slate-300 font-bold px-4 py-2 rounded-lg">取消</button>
                <button @click="submitCreate()" class="bg-cyan-500 text-slate-950 font-black px-5 py-2 rounded-lg">確定建立</button>
            </div>
        </div>
    </div>

</div>

<script>
function signalHubProfiles() {
    return {
        profiles: [],
        loading: true,
        filters: { search: '', status: '' },
        showCreateModal: false,
        form: { profile_name: '', industry_tag: '', description: '' },
        initProfiles() { this.loadProfiles(); },
        loadProfiles() {
            this.loading = true;
            let params = new URLSearchParams(this.filters);
            fetch('/api/v9/signal-hub/profiles?' + params.toString())
                .then(r => r.json())
                .then(d => {
                    if (d.success) this.profiles = d.data;
                    this.loading = false;
                })
                .catch(() => { this.loading = false; });
        },
        openCreateModal() {
            this.form = { profile_name: '', industry_tag: '', description: '' };
            this.showCreateModal = true;
        },
        submitCreate() {
            if (!this.form.profile_name) return alert('請輸入設定檔名稱');
            fetch('/api/v9/signal-hub/profiles', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.form)
            })
            .then(r => r.json())
            .then(d => {
                if (d.success) {
                    this.showCreateModal = false;
                    this.loadProfiles();
                }
            });
        },
        openCopyModal(p) {
            let name = prompt('請輸入新複製的設定檔名稱：', p.profile_name + ' (副本)');
            if (!name) return;
            fetch(`/api/v9/signal-hub/profiles/${p.id}/copy`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_name: name })
            })
            .then(r => r.json())
            .then(d => { if (d.success) this.loadProfiles(); });
        },
        deleteProfile(p) {
            if (!confirm(`確定要刪除設定檔「${p.profile_name}」嗎？`)) return;
            fetch(`/api/v9/signal-hub/profiles/${p.id}`, { method: 'DELETE' })
                .then(r => r.json())
                .then(d => { if (d.success) this.loadProfiles(); });
        }
    }
}
</script>
