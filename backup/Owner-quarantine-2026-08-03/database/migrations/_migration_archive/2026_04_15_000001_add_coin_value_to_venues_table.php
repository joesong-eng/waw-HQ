<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('venues', function (Blueprint $table) {
            $table->unsignedInteger('coin_value')
                ->default(10)
                ->after('address')
                ->comment('1枚代幣的法幣價值（元/枚），整場統一');
        });
    }

    public function down(): void
    {
        Schema::table('venues', function (Blueprint $table) {
            $table->dropColumn('coin_value');
        });
    }
};
