<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class SignalStatRule extends Model
{
    protected $table = 'signal_stat_rules';

    protected $fillable = [
        'profile_id',
        'metric_key',
        'metric_label',
        'formula',
        'formula_note',
        'unit_label',
        'display_order',
        'is_active',
    ];

    protected $casts = [
        'display_order' => 'integer',
        'is_active'     => 'boolean',
    ];

    public function profile(): BelongsTo
    {
        return $this->belongsTo(SignalProfile::class, 'profile_id');
    }
}
