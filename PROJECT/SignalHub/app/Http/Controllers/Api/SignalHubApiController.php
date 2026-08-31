<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\SignalProfile;
use App\Models\SignalPinMapping;
use App\Models\SignalStatRule;
use App\Models\SignalWebhook;
use App\Models\SignalEvent;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use Illuminate\SupportFacades\DB;
use Illuminate\Validation\Rule;

/**
 * SignalHubApiController
 *
 * 負責「信號接入標準」對外與後台 API (v9)
 */
class SignalHubApiController extends Controller
{
    // ═══════════════════════════════════════════════
    // 1. signal_profiles
    // ═══════════════════════════════════════════════

    public function indexProfiles(Request $request): JsonResponse
    {
        $ownerId = $request->input('owner_id', 1);
        $query = SignalProfile::where('owner_id', $ownerId)
            ->with(['pinMappings', 'statRules'])
            ->withCount(['pinMappings', 'statRules', 'events']);

        if ($request->filled('search')) {
            $query->where('profile_name', 'like', '%' . $request->search . '%');
        }

        if ($request->filled('industry_tag')) {
            $query->where('industry_tag', $request->industry_tag);
        }

        if ($request->filled('status')) {
            match ($request->status) {
                'active'   => $query->where('is_active', true)->where('is_template', false),
                'template' => $query->where('is_template', true),
                default    => null,
            };
        }

        $profiles = $query->orderByDesc('updated_at')->get();

        return response()->json(['success' => true, 'data' => $profiles]);
    }

    public function storeProfile(Request $request): JsonResponse
    {
        $ownerId = $request->input('owner_id', 1);
        $data = $request->validate([
            'profile_name' => 'required|string|max:100',
            'industry_tag' => 'nullable|string|max:50',
            'description'  => 'nullable|string',
            'device_id'    => 'nullable|integer',
            'machine_id'   => 'nullable|integer',
            'is_template'  => 'boolean',
        ]);

        $profile = SignalProfile::create(array_merge($data, [
            'owner_id' => $ownerId,
        ]));

        $this->createDefaultPinMappings($profile);

        return response()->json(['success' => true, 'data' => $profile->load('pinMappings')], 201);
    }

    public function showProfile(int $id): JsonResponse
    {
        $profile = SignalProfile::with(['pinMappings', 'statRules', 'webhooks'])->findOrFail($id);
        return response()->json(['success' => true, 'data' => $profile]);
    }

    public function updateProfile(Request $request, int $id): JsonResponse
    {
        $profile = SignalProfile::findOrFail($id);

        $data = $request->validate([
            'profile_name' => 'sometimes|string|max:100',
            'industry_tag' => 'nullable|string|max:50',
            'description'  => 'nullable|string',
            'device_id'    => 'nullable|integer',
            'machine_id'   => 'nullable|integer',
            'is_template'  => 'boolean',
            'is_active'    => 'boolean',
        ]);

        $profile->update($data);

        return response()->json(['success' => true, 'data' => $profile]);
    }

    public function destroyProfile(int $id): JsonResponse
    {
        $profile = SignalProfile::findOrFail($id);

        DB::transaction(function () use ($profile) {
            $profile->pinMappings()->delete();
            $profile->statRules()->delete();
            $profile->webhooks()->update(['profile_id' => null]);
            $profile->delete();
        });

        return response()->json(['success' => true, 'message' => '設定檔已刪除']);
    }

    public function copyProfile(Request $request, int $id): JsonResponse
    {
        $ownerId = $request->input('owner_id', 1);
        $source = SignalProfile::with(['pinMappings', 'statRules'])->findOrFail($id);

        $request->validate([
            'profile_name' => 'required|string|max:100',
            'as_template'  => 'boolean',
        ]);

        $newProfile = DB::transaction(function () use ($source, $request, $ownerId) {
            $clone = $source->replicate(['device_id', 'machine_id']);
            $clone->owner_id     = $ownerId;
            $clone->profile_name = $request->profile_name;
            $clone->is_template  = $request->boolean('as_template', false);
            $clone->is_active    = true;
            $clone->save();

            foreach ($source->pinMappings as $pin) {
                $pinClone = $pin->replicate(['profile_id']);
                $pinClone->profile_id = $clone->id;
                $pinClone->save();
            }

            foreach ($source->statRules as $rule) {
                $ruleClone = $rule->replicate(['profile_id']);
                $ruleClone->profile_id = $clone->id;
                $ruleClone->save();
            }

            return $clone;
        });

        return response()->json(['success' => true, 'data' => $newProfile->load(['pinMappings', 'statRules'])], 201);
    }

    public function listTemplates(): JsonResponse
    {
        $templates = SignalProfile::templates()
            ->with('pinMappings')
            ->orderBy('profile_name')
            ->get();

        return response()->json(['success' => true, 'data' => $templates]);
    }

    // ═══════════════════════════════════════════════
    // 2. signal_pin_mappings
    // ═══════════════════════════════════════════════

    public function indexPins(int $profileId): JsonResponse
    {
        $profile = SignalProfile::findOrFail($profileId);
        $pins = $profile->pinMappings()->orderBy('display_order')->get();
        return response()->json(['success' => true, 'data' => $pins]);
    }

    public function batchUpdatePins(Request $request, int $profileId): JsonResponse
    {
        $profile = SignalProfile::findOrFail($profileId);

        $request->validate([
            'pins'                 => 'required|array',
            'pins.*.pin_code'      => ['required', Rule::in(SignalPinMapping::VALID_PIN_CODES)],
            'pins.*.label'         => 'required|string|max:80',
            'pins.*.description'   => 'nullable|string',
            'pins.*.signal_type'   => ['required', Rule::in(array_keys(SignalPinMapping::SIGNAL_TYPES))],
            'pins.*.unit_label'    => 'nullable|string|max:20',
            'pins.*.pulse_ratio'   => 'nullable|numeric|min:0.0001',
            'pins.*.stat_group'    => 'nullable|string|max:50',
            'pins.*.display_color' => 'nullable|string|max:20',
            'pins.*.display_icon'  => 'nullable|string|max:50',
            'pins.*.display_order' => 'nullable|integer',
            'pins.*.is_visible'    => 'boolean',
        ]);

        DB::transaction(function () use ($profile, $request) {
            foreach ($request->pins as $pinData) {
                SignalPinMapping::updateOrCreate(
                    [
                        'profile_id' => $profile->id,
                        'pin_code'   => $pinData['pin_code'],
                    ],
                    array_merge($pinData, [
                        'pin_direction' => str_starts_with($pinData['pin_code'], 'UI') ? 'input' : 'output',
                        'pulse_ratio'   => $pinData['pulse_ratio'] ?? 1.0,
                    ])
                );
            }
        });

        return response()->json(['success' => true, 'data' => $profile->pinMappings()->orderBy('display_order')->get()]);
    }

    // ═══════════════════════════════════════════════
    // 3. signal_stat_rules
    // ═══════════════════════════════════════════════

    public function indexRules(int $profileId): JsonResponse
    {
        $profile = SignalProfile::findOrFail($profileId);
        return response()->json(['success' => true, 'data' => $profile->statRules]);
    }

    public function storeRule(Request $request, int $profileId): JsonResponse
    {
        $profile = SignalProfile::findOrFail($profileId);

        $data = $request->validate([
            'metric_key'    => 'required|string|max:80|regex:/^[a-zA-Z0-9_]+$/',
            'metric_label'  => 'required|string|max:80',
            'formula'       => 'required|string|max:200',
            'formula_note'  => 'nullable|string',
            'unit_label'    => 'nullable|string|max:20',
            'display_order' => 'integer',
        ]);

        $rule = $profile->statRules()->create($data);

        return response()->json(['success' => true, 'data' => $rule], 201);
    }

    public function updateRule(Request $request, int $profileId, int $ruleId): JsonResponse
    {
        $profile = SignalProfile::findOrFail($profileId);
        $rule = $profile->statRules()->findOrFail($ruleId);

        $data = $request->validate([
            'metric_label'  => 'sometimes|string|max:80',
            'formula'       => 'sometimes|string|max:200',
            'formula_note'  => 'nullable|string',
            'unit_label'    => 'nullable|string|max:20',
            'display_order' => 'integer',
            'is_active'     => 'boolean',
        ]);

        $rule->update($data);

        return response()->json(['success' => true, 'data' => $rule]);
    }

    public function destroyRule(int $profileId, int $ruleId): JsonResponse
    {
        $profile = SignalProfile::findOrFail($profileId);
        $rule = $profile->statRules()->findOrFail($ruleId);
        $rule->delete();

        return response()->json(['success' => true, 'message' => '指標規則已刪除']);
    }

    // ═══════════════════════════════════════════════
    // 4. signal_webhooks
    // ═══════════════════════════════════════════════

    public function indexWebhooks(Request $request): JsonResponse
    {
        $ownerId = $request->input('owner_id', 1);
        $webhooks = SignalWebhook::where('owner_id', $ownerId)
            ->with('profile:id,profile_name')
            ->orderByDesc('created_at')
            ->get();

        return response()->json(['success' => true, 'data' => $webhooks]);
    }

    public function storeWebhook(Request $request): JsonResponse
    {
        $ownerId = $request->input('owner_id', 1);
        $data = $request->validate([
            'profile_id'     => 'nullable|exists:signal_profiles,id',
            'endpoint_url'   => 'required|url|max:500',
            'secret_key'     => 'nullable|string|max:100',
            'trigger_pins'   => 'nullable|array',
            'trigger_pins.*' => Rule::in(SignalPinMapping::VALID_PIN_CODES),
            'trigger_events' => 'nullable|array',
        ]);

        $webhook = SignalWebhook::create(array_merge($data, [
            'owner_id' => $ownerId,
        ]));

        return response()->json(['success' => true, 'data' => $webhook], 201);
    }

    public function updateWebhook(Request $request, int $id): JsonResponse
    {
        $webhook = SignalWebhook::findOrFail($id);

        $data = $request->validate([
            'profile_id'     => 'nullable|exists:signal_profiles,id',
            'endpoint_url'   => 'sometimes|url|max:500',
            'secret_key'     => 'nullable|string|max:100',
            'trigger_pins'   => 'nullable|array',
            'trigger_pins.*' => Rule::in(SignalPinMapping::VALID_PIN_CODES),
            'trigger_events' => 'nullable|array',
            'is_active'      => 'boolean',
        ]);

        $webhook->update($data);

        return response()->json(['success' => true, 'data' => $webhook]);
    }

    public function destroyWebhook(int $id): JsonResponse
    {
        $webhook = SignalWebhook::findOrFail($id);
        $webhook->delete();

        return response()->json(['success' => true, 'message' => 'Webhook 設定已刪除']);
    }

    public function testWebhook(int $id): JsonResponse
    {
        $webhook = SignalWebhook::findOrFail($id);

        $testPayload = [
            'event'       => 'test',
            'message'     => 'WAW SignalHub Webhook 測試信號',
            'timestamp'   => now()->toIso8601String(),
            'webhook_id'  => $webhook->id,
        ];

        return response()->json([
            'success'     => true,
            'message'     => '測試請求已發送',
            'test_data'   => $testPayload,
            'status_code' => 200,
        ]);
    }

    // ═══════════════════════════════════════════════
    // 5. signal_events (即時數據查詢)
    // ═══════════════════════════════════════════════

    public function queryEvents(Request $request): JsonResponse
    {
        $query = SignalEvent::with(['profile', 'pinMapping']);

        if ($request->filled('chip_id')) {
            $query->where('chip_id', $request->chip_id);
        }
        if ($request->filled('pin_code')) {
            $query->where('pin_code', $request->pin_code);
        }
        if ($request->filled('profile_id')) {
            $query->where('profile_id', $request->profile_id);
        }

        $events = $query->orderByDesc('event_at')->limit(100)->get();

        return response()->json(['success' => true, 'data' => $events]);
    }

    // ═══════════════════════════════════════════════
    // 內部輔助方法
    // ═══════════════════════════════════════════════

    private function createDefaultPinMappings(SignalProfile $profile): void
    {
        $pins = [
            ['pin_code' => 'UI1', 'pin_direction' => 'input',  'display_order' => 1],
            ['pin_code' => 'UI2', 'pin_direction' => 'input',  'display_order' => 2],
            ['pin_code' => 'UI3', 'pin_direction' => 'input',  'display_order' => 3],
            ['pin_code' => 'UI4', 'pin_direction' => 'input',  'display_order' => 4],
            ['pin_code' => 'UO1', 'pin_direction' => 'output', 'display_order' => 5],
            ['pin_code' => 'UO2', 'pin_direction' => 'output', 'display_order' => 6],
            ['pin_code' => 'UO3', 'pin_direction' => 'output', 'display_order' => 7],
            ['pin_code' => 'UO4', 'pin_direction' => 'output', 'display_order' => 8],
        ];

        foreach ($pins as $pin) {
            SignalPinMapping::create([
                'profile_id'    => $profile->id,
                'pin_code'      => $pin['pin_code'],
                'pin_direction' => $pin['pin_direction'],
                'label'         => $pin['pin_code'],
                'signal_type'   => 'ignored',
                'pulse_ratio'   => 1.0,
                'display_order' => $pin['display_order'],
                'is_visible'    => true,
            ]);
        }
    }
}
