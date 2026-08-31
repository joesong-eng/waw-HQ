<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>@yield('title', 'WAW SignalHub - 通用信號標準層')</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Alpine.js CDN -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <style>
        [x-cloak] { display: none !important; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
    </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col antialiased">
    <!-- 頂部導覽列 (High Contrast / Large Text) -->
    <header class="bg-slate-800 border-b border-slate-700 shadow-md">
        <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
            <div class="flex items-center space-x-6">
                <a href="/profiles" class="flex items-center space-x-2">
                    <span class="text-2xl font-black tracking-wider text-cyan-400">WAW</span>
                    <span class="text-xl font-extrabold text-white">SignalHub</span>
                    <span class="bg-cyan-500/20 text-cyan-300 text-xs px-2 py-0.5 rounded font-mono font-bold">v1.0 Layer 0</span>
                </a>
                <nav class="hidden md:flex space-x-4">
                    <a href="/profiles" class="px-3 py-1.5 rounded-md font-bold text-base transition {{ request()->is('profiles*') ? 'bg-cyan-600 text-white' : 'text-slate-300 hover:text-white hover:bg-slate-700' }}">
                        📡 設定檔 (Profiles)
                    </a>
                    <a href="/webhooks" class="px-3 py-1.5 rounded-md font-bold text-base transition {{ request()->is('webhooks*') ? 'bg-cyan-600 text-white' : 'text-slate-300 hover:text-white hover:bg-slate-700' }}">
                        🔔 Webhooks 推送
                    </a>
                </nav>
            </div>
            <div class="flex items-center space-x-3">
                <a href="/api/v9/signal-hub/profiles" target="_blank" class="bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-mono px-3 py-1.5 rounded border border-slate-600 transition">
                    REST API (v9)
                </a>
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    ● signal.tg25.win
                </span>
            </div>
        </div>
    </header>

    <!-- 主要內容區 -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
        @yield('content')
    </main>

    <!-- 頁腳 -->
    <footer class="bg-slate-800 border-t border-slate-700 py-4 text-center text-xs text-slate-400 font-mono">
        WAW Universal Signal Standard (WAW-USS) v1.0 &copy; 2026 WAW Standard Bureau (Sidney)
    </footer>
</body>
</html>
