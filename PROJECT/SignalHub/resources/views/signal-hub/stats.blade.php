@extends('layouts.app')
@section('title', '統計指標規則 - WAW SignalHub')
@section('content')
<div class="space-y-6" x-data="signalHubStats({{ $profile->id }})" x-init="initRules()">

    <!-- 頁頭與返回 -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-sm">
        <div>
            <div class="flex items-center space-x-2 text-sm text-amber-400 font-bold mb-1">
                <a href="/profiles" class="hover:underline">← 返回設定檔列表</a>
                <span>/</span>
                <span class="text-slate-400 font-mono">Profile #{{ $profile->id }}</span>
            </div>
            <h1 class="text-3xl font-black text-white tracking-wide flex items-center gap-3">
                📊 統計指標計算規則
                <span class="text-xl font-extrabold text-amber-400">({{ $profile->profile_name }})</span>
            </h1>
            <p class="text-base font-medium text-slate-300 mt-1">利用自訂算式（如 UI1 - UI2）將多路信號組合換算為實體營運指標</p>
        </div>
        <button @click="openCreateModal()"
                class="bg-amber-500 hover:bg-amber-400 text-slate-950 font-black text-base px-5 py-2.5 rounded-lg shadow-lg hover:shadow-amber-500/20 transition duration-150">
            + 新建統計規則
        </button>
    </div>

    <!-- 規則列表卡片 -->
    <div class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden shadow-lg">
        <div x-show="rules.length === 0" class="py-16 text-center text-slate-400 space-y-3">
            <div class="text-5xl">📊</div>
            <div class="text-xl font-bold text-white">尚無統計規則</div>
            <p class="text-sm text-slate-400">建立規則即可將通道信號自動換算為實體指標 (例如: 淨收益 = UI1 - UI2)</p>
        </div>

        <table x-show="rules.length > 0" class="w-full text-left text-base">
            <thead class="bg-slate-900/80 border-b border-slate-700 text-slate-300 font-bold uppercase text-sm tracking-wider">
                <tr>
                    <th class="px-5 py-4">指標鍵名 (Metric Key)</th>
                    <th class="px-5 py-4">顯示名稱</th>
                    <th class="px-5 py-4">計算公式 (Formula)</th>
                    <th class="px-5 py-4">單位</th>
                    <th class="px-5 py-4 text-center">狀態</th>
                    <th class="px-5 py-4 text-right">操作</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-700/60 font-semibold text-slate-200">
                <template x-for="r in rules" :key="r.id">
                    <tr class="hover:bg-slate-750 transition">
                        <td class="px-5 py-4 font-mono font-extrabold text-amber-400 text-lg" x-text="r.metric_key"></td>
                        <td class="px-5 py-4 font-extrabold text-white text-lg" x-text="r.metric_label"></td>
                        <td class="px-5 py-4">
                            <code class="bg-slate-900 text-cyan-300 px-3 py-1 rounded font-mono font-bold text-base border border-slate-700" x-text="r.formula"></code>
                            <div class="text-xs text-slate-400 mt-1" x-text="r.formula_note"></div>
                        </td>
                        <td class="px-5 py-4 font-bold text-slate-300" x-text="r.unit_label || '-'"></td>
                        <td class="px-5 py-4 text-center">
                            <span x-show="r.is_active" class="bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-xs px-2.5 py-1 rounded font-bold">啟用</span>
                            <span x-show="!r.is_active" class="bg-slate-700 text-slate-400 text-xs px-2.5 py-1 rounded font-bold">停用</span>
                        </td>
                        <td class="px-5 py-4 text-right">
                            <button @click="deleteRule(r.id)" class="bg-rose-500/20 hover:bg-rose-500/40 text-rose-300 font-bold text-xs px-3 py-1.5 rounded transition">
                                🗑️ 刪除
                            </button>
                        </td>
                    </tr>
                </template>
            </tbody>
        </table>
    </div>

    <!-- Modal: 新增規則 -->
    <div x-show="showModal" x-cloak class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="bg-slate-800 border border-slate-700 rounded-xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <h2 class="text-xl font-black text-white">✨ 新建指標統計規則</h2>
            <div class="space-y-3">
                <div>
                    <label class="block text-sm font-bold text-slate-300 mb-1">指標鍵名 (程式識別 Key) <span class="text-rose-400">*</span></label>
                    <input type="text" x-model="form.metric_key" placeholder="如：net_revenue, total_coins"
                           class="w-full bg-slate-900 border border-slate-700 text-amber-300 font-mono font-bold rounded-lg px-3 py-2 text-base focus:border-amber-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-sm font-bold text-slate-300 mb-1">顯示名稱 (Metric Label) <span class="text-rose-400">*</span></label>
                    <input type="text" x-model="form.metric_label" placeholder="如：淨營業額、實收代幣"
                           class="w-full bg-slate-900 border border-slate-700 text-white font-bold rounded-lg px-3 py-2 text-base focus:border-amber-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-sm font-bold text-slate-300 mb-1">計算公式 (Formula) <span class="text-rose-400">*</span></label>
                    <input type="text" x-model="form.formula" placeholder="例如：UI1 - UI2 或 UI1 * 10"
                           class="w-full bg-slate-900 border border-slate-700 text-cyan-300 font-mono font-bold rounded-lg px-3 py-2 text-base focus:border-amber-500 focus:outline-none">
                    <p class="text-xs text-slate-400 mt-1">提示：支援使用通道名稱 UI1~UI4 及基礎四則運算符 (+, -, *, /)</p>
                </div>
                <div>
                    <label class="block text-sm font-bold text-slate-300 mb-1">單位 (Unit)</label>
                    <input type="text" x-model="form.unit_label" placeholder="如：元、次"
                           class="w-full bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2 text-base focus:border-amber-500 focus:outline-none">
                </div>
            </div>
            <div class="flex justify-end space-x-3 pt-3">
                <button @click="showModal = false" class="bg-slate-700 text-slate-300 font-bold px-4 py-2 rounded-lg">取消</button>
                <button @click="submitRule()" class="bg-amber-500 text-slate-950 font-black px-5 py-2 rounded-lg">建立規則</button>
            </div>
        </div>
    </div>

</div>

<script>
function signalHubStats(profileId) {
    return {
        profileId: profileId,
        rules: [],
        showModal: false,
        form: { metric_key: '', metric_label: '', formula: '', unit_label: '' },
        initRules() {
            fetch(`/api/v9/signal-hub/profiles/${this.profileId}/rules`)
                .then(r => r.json())
                .then(d => { if (d.success) this.rules = d.data; });
        },
        openCreateModal() {
            this.form = { metric_key: '', metric_label: '', formula: '', unit_label: '' };
            this.showModal = true;
        },
        submitRule() {
            if (!this.form.metric_key || !this.form.formula) return alert('請填寫完整資訊');
            fetch(`/api/v9/signal-hub/profiles/${this.profileId}/rules`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.form)
            })
            .then(r => r.json())
            .then(d => {
                if (d.success) {
                    this.showModal = false;
                    this.initRules();
                } else alert('建立失敗：' + (d.message || '格式錯誤'));
            });
        },
        deleteRule(ruleId) {
            if (!confirm('確定刪除此規則？')) return;
            fetch(`/api/v9/signal-hub/profiles/${this.profileId}/rules/${ruleId}`, { method: 'DELETE' })
                .then(r => r.json())
                .then(d => { if (d.success) this.initRules(); });
        }
    }
}
</script>
