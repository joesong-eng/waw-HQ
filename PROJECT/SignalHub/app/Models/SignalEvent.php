<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class SignalEvent extends Model
{
    protected $table = 'signal_events';
    public $timestamps = false;

    protected $fillable = [
        'chip_id',
        'device_id',
        'machine_id',
        'profile_id',
        'pin_mapping_id',
        'pin_code',
        'raw_value',
        'delta_value',
        'converted_value',
        'event_at',
        'received_at',
    ];

    protected $casts = [
        'raw_value'       => 'integer',
        'delta_value'     => 'integer',
        'converted_value' => 'decimal:4',
        'event_at'        => 'datetime',
        'received_at'     => 'datetime',
    ];

    public function profile(): BelongsTo
    {
        return $this->belongsTo(SignalProfile::class, 'profile_id');
    }

    public function pinMapping(): BelongsTo
    {
        return $this->belongsTo(SignalPinMapping::class, 'pin_mapping_id');
    }
}
