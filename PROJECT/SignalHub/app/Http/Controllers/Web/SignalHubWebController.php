<?php

namespace App\Http\Controllers\Web;

use App\Http\Controllers\Controller;
use App\Models\SignalProfile;
use App\Models\SignalWebhook;
use Illuminate\Http\Request;
use Illuminate\View\View;

class SignalHubWebController extends Controller
{
    public function profiles(Request $request): View
    {
        return view('signal-hub.profiles');
    }

    public function pins(Request $request, int $id): View
    {
        $profile = SignalProfile::with('pinMappings')->findOrFail($id);
        return view('signal-hub.pins', compact('profile'));
    }

    public function stats(Request $request, int $id): View
    {
        $profile = SignalProfile::with(['pinMappings', 'statRules'])->findOrFail($id);
        return view('signal-hub.stats', compact('profile'));
    }

    public function webhooks(Request $request): View
    {
        return view('signal-hub.webhooks');
    }
}
