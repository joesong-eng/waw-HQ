<?php

use App\Http\Controllers\Api\SignalHubApiController;
use Illuminate\Support\Facades\Route;

Route::prefix('v9/signal-hub')->group(function () {
    // 1. Profiles
    Route::get('/profiles', [SignalHubApiController::class, 'indexProfiles']);
    Route::post('/profiles', [SignalHubApiController::class, 'storeProfile']);
    Route::get('/profiles/templates', [SignalHubApiController::class, 'listTemplates']);
    Route::get('/profiles/{id}', [SignalHubApiController::class, 'showProfile']);
    Route::put('/profiles/{id}', [SignalHubApiController::class, 'updateProfile']);
    Route::delete('/profiles/{id}', [SignalHubApiController::class, 'destroyProfile']);
    Route::post('/profiles/{id}/copy', [SignalHubApiController::class, 'copyProfile']);

    // 2. Pin Mappings
    Route::get('/profiles/{id}/pins', [SignalHubApiController::class, 'indexPins']);
    Route::put('/profiles/{id}/pins', [SignalHubApiController::class, 'batchUpdatePins']);

    // 3. Stat Rules
    Route::get('/profiles/{id}/rules', [SignalHubApiController::class, 'indexRules']);
    Route::post('/profiles/{id}/rules', [SignalHubApiController::class, 'storeRule']);
    Route::put('/profiles/{id}/rules/{ruleId}', [SignalHubApiController::class, 'updateRule']);
    Route::delete('/profiles/{id}/rules/{ruleId}', [SignalHubApiController::class, 'destroyRule']);

    // 4. Webhooks
    Route::get('/webhooks', [SignalHubApiController::class, 'indexWebhooks']);
    Route::post('/webhooks', [SignalHubApiController::class, 'storeWebhook']);
    Route::put('/webhooks/{id}', [SignalHubApiController::class, 'updateWebhook']);
    Route::delete('/webhooks/{id}', [SignalHubApiController::class, 'destroyWebhook']);
    Route::post('/webhooks/{id}/test', [SignalHubApiController::class, 'testWebhook']);

    // 5. Events / Telemetry
    Route::get('/events', [SignalHubApiController::class, 'queryEvents']);
});
