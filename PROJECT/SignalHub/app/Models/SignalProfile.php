<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Builder;

class SignalProfile extends Model
{
    protected $table = 'signal_profiles';

    protected $fillable = [
        'owner_id',
        'device_id',
        'machine_id',
        'profile_name',
        'industry_tag',
        'description',
        'is_template',
        'is_active',
    ];

    protected $casts = [
        'is_template' => 'boolean',
        'is_active'   => 'boolean',
    ];

    public function pinMappings(): HasMany
    {
        return $this->hasMany(SignalPinMapping::class, 'profile_id')->orderBy('display_order');
    }

    public function statRules(): HasMany
    {
        return $this->hasMany(SignalStatRule::class, 'profile_id')->orderBy('display_order');
    }

    public function webhooks(): HasMany
    {
        return $this->hasMany(SignalWebhook::class, 'profile_id');
    }

    public function events(): HasMany
    {
        return $this->hasMany(SignalEvent::class, 'profile_id');
    }

    public function scopeForOwner(Builder $query, ?int $ownerId = null): Builder
    {
        if ($ownerId) {
            return $query->where('owner_id', $ownerId);
        }
        return $query;
    }

    public function scopeTemplates(Builder $query): Builder
    {
        return $query->where('is_template', true)->where('is_active', true);
    }
}
