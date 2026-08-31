<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class SignalWebhook extends Model
{
    protected $table = 'signal_webhooks';

    protected $fillable = [
        'owner_id',
        'profile_id',
        'endpoint_url',
        'secret_key',
        'trigger_pins',
        'trigger_events',
        'is_active',
        'failure_count',
        'last_success_at',
        'last_failure_at',
    ];

    protected $casts = [
        'trigger_pins'    => 'array',
        'trigger_events'  => 'array',
        'is_active'       => 'boolean',
        'failure_count'   => 'integer',
        'last_success_at' => 'datetime',
        'last_failure_at' => 'datetime',
    ];

    public function profile(): BelongsTo
    {
        return $this->belongsTo(SignalProfile::class, 'profile_id');
    }
}
