<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     * 
     * 移除重複的 coin_value 欄位
     * - pulse_ratio 已經存在且正在使用（計數器每次觸發的金額）
     * - coin_value 是重複的概念，應該移除
     * - 保留 credit_amount（開分金額）
     */
    public function up(): void
    {
        Schema::table('devices', function (Blueprint $table) {
            $table->dropColumn('coin_value');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('devices', function (Blueprint $table) {
            $table->unsignedInteger('coin_value')
                ->default(10)
                ->after('pulse_ratio')
                ->comment('代幣面額（元/幣）');
        });
    }
};
