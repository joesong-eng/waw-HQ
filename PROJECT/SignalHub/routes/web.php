<?php

use App\Http\Controllers\Web\SignalHubWebController;
use Illuminate\Support\Facades\Route;

Route::redirect('/', '/profiles');

Route::get('/profiles', [SignalHubWebController::class, 'profiles'])->name('signal.profiles');
Route::get('/profiles/{id}/pins', [SignalHubWebController::class, 'pins'])->name('signal.pins');
Route::get('/profiles/{id}/stats', [SignalHubWebController::class, 'stats'])->name('signal.stats');
Route::get('/webhooks', [SignalHubWebController::class, 'webhooks'])->name('signal.webhooks');
