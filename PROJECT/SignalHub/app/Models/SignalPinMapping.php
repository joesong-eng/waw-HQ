<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class SignalPinMapping extends Model
{
    protected $table = 'signal_pin_mappings';

    protected $fillable = [
        'profile_id',
        'pin_code',
        'pin_direction',
        'label',
        'description',
        'signal_type',
        'unit_label',
        'pulse_ratio',
        'stat_group',
        'display_color',
        'display_icon',
        'display_order',
        'is_visible',
    ];

    protected $casts = [
        'pulse_ratio'   => 'decimal:4',
        'display_order' => 'integer',
        'is_visible'    => 'boolean',
    ];

    public const VALID_PIN_CODES = [
        'UI1', 'UI2', 'UI3', 'UI4',
        'UO1', 'UO2', 'UO3', 'UO4',
    ];

    public const SIGNAL_TYPES = [
        'counter' => '計數器（脈衝累計）',
        'toggle'  => '開關狀態（0/1）',
        'event'   => '事件觸發（一次性）',
        'value'   => '數值換算（帶比例）',
        'ignored' => '不使用（忽略）',
    ];

    public function profile(): BelongsTo
    {
        return $this->belongsTo(SignalProfile::class, 'profile_id');
    }
}
