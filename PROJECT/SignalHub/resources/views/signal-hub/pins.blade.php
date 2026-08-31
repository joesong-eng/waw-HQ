@extends('layouts.app')
@section('title', '8通道腳位映射 - WAW SignalHub')
@section('content')
<div class="space-y-6" x-data="signalHubPins({{ $profile->id }})" x-init="initPins()">

    <!-- 頁頭與返回 -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-sm">
        <div>
            <div class="flex items-center space-x-2 text-sm text-cyan-400 font-bold mb-1">
                <a href="/profiles" class="hover:underline">← 返回設定檔列表</a>
                <span>/</span>
                <span class="text-slate-400 font-mono">Profile #{{ $profile->id }}</span>
            </div>
            <h1 class="text-3xl font-black text-white tracking-wide flex items-center gap-3">
                🔌 8 通道腳位映射設定
                <span class="text-xl font-extrabold text-cyan-400">({{ $profile->profile_name }})</span>
            </h1>
            <p class="text-base font-medium text-slate-300 mt-1">獨立配置 UI1~UI4 (硬體 PCNT 脈衝/開關) 與 UO1~UO4 (輸出觸發) 之名稱、倍率與分組</p>
        </div>
        <button @click="savePins()"
                class="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-base px-6 py-2.5 rounded-lg shadow-lg hover:shadow-emerald-500/20 transition duration-150">
            💾 儲存腳位變更
        </button>
    </div>

    <!-- 腳位通道設定卡片 (8 Channels) -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <template x-for="(pin, index) in pins" :key="pin.pin_code">
            <div class="bg-slate-800 border rounded-xl p-5 space-y-4 shadow-lg transition"
                 :class="pin.pin_code.startsWith('UI') ? 'border-cyan-500/40 bg-slate-800/90' : 'border-amber-500/40 bg-slate-800/90'">
                
                <!-- 卡片標頭 -->
                <div class="flex items-center justify-between border-b border-slate-700/80 pb-3">
                    <div class="flex items-center space-x-3">
                        <span class="font-mono text-xl font-black px-3 py-1 rounded-md text-white shadow-inner"
                              :class="pin.pin_code.startsWith('UI') ? 'bg-cyan-600' : 'bg-amber-600'"
                              x-text="pin.pin_code"></span>
                        <div>
                            <div class="font-extrabold text-white text-lg">
                                <span x-text="pin.pin_code.startsWith('UI') ? '輸入通道 (Input)' : '輸出通道 (Output)'"></span>
                            </div>
                            <div class="text-xs text-slate-400 font-mono"
                                 x-text="pin.pin_code.startsWith('UI') ? '硬體 PCNT 脈衝計數器 / 中斷感測' : '繼電器 / Open-Drain 輸出'"></div>
                        </div>
                    </div>
                    <label class="flex items-center space-x-2 cursor-pointer">
                        <input type="checkbox" x-model="pin.is_visible" class="w-5 h-5 rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-0">
                        <span class="text-sm font-bold text-slate-300">啟用顯示</span>
                    </label>
                </div>

                <!-- 腳位欄位表單 (高對比/大字緊湊) -->
                <div class="grid grid-cols-2 gap-4 text-base">
                    <div>
                        <label class="block text-xs font-bold text-slate-400 mb-1">自訂標籤 (Label) <span class="text-rose-400">*</span></label>
                        <input type="text" x-model="pin.label" placeholder="如：總投幣、投退幣"
                               class="w-full bg-slate-900 border border-slate-700 text-white font-bold rounded-lg px-3 py-2 focus:border-cyan-500 focus:outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-400 mb-1">信號類型 (Signal Type)</label>
                        <select x-model="pin.signal_type"
                                class="w-full bg-slate-900 border border-slate-700 text-white font-bold rounded-lg px-3 py-2 focus:border-cyan-500 focus:outline-none">
                            <option value="counter">Counter (里程表脈衝)</option>
                            <option value="toggle">Toggle (開關電位)</option>
                            <option value="event">Event (單次脈衝事件)</option>
                            <option value="value">Value (連續數值)</option>
                            <option value="ignored">Ignored (不採集/停用)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-400 mb-1">脈衝換算倍率 (Pulse Ratio)</label>
                        <input type="number" step="0.0001" x-model="pin.pulse_ratio" placeholder="1.0"
                               class="w-full bg-slate-900 border border-slate-700 text-cyan-300 font-mono font-bold rounded-lg px-3 py-2 focus:border-cyan-500 focus:outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-400 mb-1">顯示單位 (Unit)</label>
                        <input type="text" x-model="pin.unit_label" placeholder="如：元、次、枚"
                               class="w-full bg-slate-900 border border-slate-700 text-white font-bold rounded-lg px-3 py-2 focus:border-cyan-500 focus:outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-400 mb-1">統計分組 (Stat Group)</label>
                        <select x-model="pin.stat_group"
                                class="w-full bg-slate-900 border border-slate-700 text-slate-200 font-bold rounded-lg px-3 py-2 focus:border-cyan-500 focus:outline-none">
                            <option value="">未分組</option>
                            <option value="revenue">💰 營收/投幣 (revenue)</option>
                            <option value="cost">💸 出幣/退幣 (cost)</option>
                            <option value="alert">⚠️ 警報/故障 (alert)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-400 mb-1">備註說明</label>
                        <input type="text" x-model="pin.description" placeholder="詳細描述..."
                               class="w-full bg-slate-900 border border-slate-700 text-slate-300 rounded-lg px-3 py-2 focus:border-cyan-500 focus:outline-none">
                    </div>
                </div>

            </div>
        </template>
    </div>

</div>

<script>
function signalHubPins(profileId) {
    return {
        profileId: profileId,
        pins: [],
        initPins() {
            fetch(`/api/v9/signal-hub/profiles/${this.profileId}/pins`)
                .then(r => r.json())
                .then(d => { if (d.success) this.pins = d.data; });
        },
        savePins() {
            fetch(`/api/v9/signal-hub/profiles/${this.profileId}/pins`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pins: this.pins })
            })
            .then(r => r.json())
            .then(d => {
                if (d.success) alert('✅ 8 通道腳位設定儲存成功！');
                else alert('❌ 儲存失敗：' + (d.message || '格式錯誤'));
            });
        }
    }
}
</script>
